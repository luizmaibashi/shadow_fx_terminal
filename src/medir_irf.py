"""Ablacao do IRF por usuario com bootstrap pareado (ADR-0011)."""

import argparse
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from decisao import escolher_limiar_operacao, split_por_usuario
from gerador_v2 import gerar_dataset_v2
from pipeline_compliance import engenharia_features, normalizar_score_anomalia
from utils import DATA_PROC, FEATURES_ML, REPORTS_DIR


def _treinar_e_pontuar(calibracao: pd.DataFrame, avaliacao: pd.DataFrame,
                      colunas: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Ajusta scaler, floresta e limites p1/p99 apenas na calibracao."""
    scaler = StandardScaler()
    x_cal = scaler.fit_transform(calibracao[colunas].fillna(0).to_numpy())
    x_aval = scaler.transform(avaliacao[colunas].fillna(0).to_numpy())
    modelo = IsolationForest(n_estimators=200, contamination=0.07, random_state=42)
    modelo.fit(x_cal)
    bruto_cal = modelo.score_samples(x_cal)
    limites = {"score_min": float(np.percentile(bruto_cal, 1)),
               "score_max": float(np.percentile(bruto_cal, 99))}
    if limites["score_min"] == limites["score_max"]:
        raise ValueError("calibracao de score degenerada")
    return (normalizar_score_anomalia(bruto_cal, limites),
            normalizar_score_anomalia(modelo.score_samples(x_aval), limites))


def _por_usuario(avaliacao: pd.DataFrame, quartil: float,
                 limiares: dict[str, float]) -> pd.DataFrame:
    alto = avaliacao["irf_contexto"] >= quartil
    base = avaliacao[["user_id", "tipo_usuario", "classe_v2"]].drop_duplicates("user_id").set_index("user_id")
    if avaliacao.groupby("user_id")["classe_v2"].nunique().gt(1).any():
        raise ValueError("user_id possui mais de uma classe_v2")
    base["fraude"] = base["tipo_usuario"].str.contains("suspeito")
    base["poupador"] = base["tipo_usuario"].str.startswith("A_")
    base["tem_alto"] = alto.groupby(avaliacao["user_id"]).any().reindex(base.index, fill_value=False)
    for nome, limiar in limiares.items():
        alerta = avaliacao[f"score_{nome}"] >= limiar
        base[f"alerta_{nome}"] = alerta.groupby(avaliacao["user_id"]).any().reindex(base.index, fill_value=False)
        base[f"alerta_alto_{nome}"] = (alerta & alto).groupby(avaliacao["user_id"]).any().reindex(base.index, fill_value=False)
    return base


def _periodo_e_estresse(df_tx: pd.DataFrame, df_irf: pd.DataFrame) -> tuple[dict, float, int]:
    """Define estresse pelo macro de cada dia corrido, sem ponderar por compras."""
    periodo = df_tx.attrs.get("periodo_efetivo")
    if periodo is None:
        transacoes = pd.to_datetime(df_tx["timestamp"])
        periodo = {"inicio": str(transacoes.min().date()), "fim": str(transacoes.max().date())}
    dias = pd.date_range(periodo["inicio"], periodo["fim"], freq="D")
    calendario = pd.DataFrame({
        "user_id": "CALENDARIO_IRF",
        "timestamp": dias,
        "data": dias.date,
        "valor_brl": 0.0,
        "wallet_destino": "CALENDARIO_IRF",
    })
    # A função existente aplica o mesmo asof, lag e fallback das transações reais.
    contexto = engenharia_features(calendario, df_irf)["irf_contexto"]
    limiar = float(contexto.quantile(0.75))
    n_dias = int((contexto >= limiar).sum())
    return periodo, limiar, n_dias


def _taxas(usuarios: pd.DataFrame, nome: str) -> dict:
    fraude = usuarios["fraude"]
    poupador = usuarios["poupador"]
    estresse = poupador & usuarios["tem_alto"]
    if not fraude.any() or not poupador.any() or not estresse.any():
        raise ValueError("avaliacao requer fraude, poupadores e poupadores em IRF alto")
    alerta = usuarios[f"alerta_{nome}"]
    por_classe = {}
    for classe in ("frac_classico", "frac_fora_regra"):
        grupo = usuarios["classe_v2"] == classe
        if not grupo.any():
            raise ValueError(f"avaliacao sem classe {classe}")
        por_classe[classe] = float(alerta[grupo].mean())
    return {
        "recall": float(alerta[fraude].mean()),
        "fp_geral": float(alerta[poupador].mean()),
        "fp_estresse": float(usuarios.loc[estresse, f"alerta_alto_{nome}"].mean()),
        "recall_classe_v2": por_classe,
        "n_fraude": int(fraude.sum()),
        "n_poupador": int(poupador.sum()),
        "n_poupador_estresse": int(estresse.sum()),
    }


def _diferencas(usuarios: pd.DataFrame) -> dict[str, float]:
    com = _taxas(usuarios, "com_irf")
    sem = _taxas(usuarios, "sem_irf")
    diferencas = {chave: com[chave] - sem[chave]
                  for chave in ("recall", "fp_geral", "fp_estresse")}
    for classe in ("frac_classico", "frac_fora_regra"):
        diferencas[f"recall_{classe}"] = (com["recall_classe_v2"][classe]
                                         - sem["recall_classe_v2"][classe])
    return diferencas


def bootstrap_pareado(usuarios: pd.DataFrame, B: int = 2000,
                      seed: int = 42) -> dict:
    """Reamostra a mesma lista de IDs dentro de cada classe para os dois modelos."""
    if B <= 0 or usuarios.index.has_duplicates:
        raise ValueError("B deve ser positivo e IDs de usuario devem ser unicos")
    rng = np.random.default_rng(seed)
    grupos = [grupo.index.to_numpy() for _, grupo in usuarios.groupby("classe_v2", sort=True)]
    chaves = list(_diferencas(usuarios))
    amostras = {chave: np.empty(B) for chave in chaves}
    for b in range(B):
        ids = np.concatenate([rng.choice(grupo, size=len(grupo), replace=True) for grupo in grupos])
        diferencas = _diferencas(usuarios.loc[ids])
        for chave in chaves:
            amostras[chave][b] = diferencas[chave]
    ponto = _diferencas(usuarios)
    return {chave: {"ponto": float(ponto[chave]),
                    "ic95": [float(x) for x in np.percentile(amostras[chave], [2.5, 97.5])]}
            for chave in chaves}


def medir_mundo(df_tx: pd.DataFrame, df_irf: pd.DataFrame, seed: int = 42,
                x_max: float = 0.05, B: int = 2000) -> dict:
    """Treina duas florestas na calibracao e compara alertas na avaliacao."""
    features = engenharia_features(df_tx, df_irf)
    ids_cal, ids_aval = split_por_usuario(features, seed=seed)
    if len(ids_cal.intersection(ids_aval)):
        raise AssertionError("split misturou usuarios")
    cal = features.loc[features["user_id"].isin(ids_cal)].copy()
    aval = features.loc[features["user_id"].isin(ids_aval)].copy()
    if cal.empty or aval.empty:
        raise ValueError("calibracao e avaliacao precisam de transacoes")
    periodo, quartil, n_dias_estresse = _periodo_e_estresse(df_tx, df_irf)
    limiares = {}
    for nome, colunas in (("com_irf", FEATURES_ML),
                          ("sem_irf", [c for c in FEATURES_ML if c != "irf_contexto"])):
        score_cal, score_aval = _treinar_e_pontuar(cal, aval, colunas)
        cal[f"score_{nome}"] = score_cal
        aval[f"score_{nome}"] = score_aval
        limiar = escolher_limiar_operacao(cal, score_col=f"score_{nome}",
                                          x_max=x_max, usuarios=ids_cal)
        if limiar is None:
            raise ValueError(f"nenhum limiar operacional para {nome}")
        limiares[nome] = limiar
    usuarios = _por_usuario(aval, quartil, limiares)
    return {"com_irf": _taxas(usuarios, "com_irf"),
            "sem_irf": _taxas(usuarios, "sem_irf"),
            "diferencas": bootstrap_pareado(usuarios, B=B, seed=seed),
            "limiares": limiares,
            "periodo_efetivo": periodo,
            "limiar_irf_estresse": quartil,
            "n_dias_estresse": n_dias_estresse,
            "n_calibracao": len(ids_cal), "n_avaliacao": len(ids_aval)}


def avaliar_condicoes(res_v2: dict, res_placebo: dict) -> dict:
    """Avalia os tres gates de abandono do ADR-0011."""
    placebo_recall = res_placebo["diferencas"]["recall"]["ic95"]
    v2_recall = res_v2["diferencas"]["recall"]["ic95"]
    v2_fp_alto = res_v2["diferencas"]["fp_estresse"]["ic95"]
    return {
        "A": {"passa": placebo_recall[0] <= 0 <= placebo_recall[1],
              "ic95_recall_placebo": placebo_recall},
        "B": {"passa": v2_recall[0] > 0, "limite_inferior_recall_v2": v2_recall[0]},
        "C": {"passa": v2_fp_alto[1] <= 0.01,
              "limite_superior_fp_estresse_v2": v2_fp_alto[1]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mundo", choices=("v2", "placebo"), required=True)
    args = parser.parse_args()
    irf = pd.read_csv(DATA_PROC / "dataset_irf_completo.csv", index_col="date", parse_dates=True)
    df_tx = gerar_dataset_v2(irf["irf_v2"], acoplamento=args.mundo == "v2")
    resultado = medir_mundo(df_tx, irf)
    print(f"Período efetivo: {resultado['periodo_efetivo']['inicio']} a "
          f"{resultado['periodo_efetivo']['fim']}")
    print(f"IRF de estresse: ≥ {resultado['limiar_irf_estresse']:.2f} "
          f"({resultado['n_dias_estresse']} dias)")
    print("Mundo | Métrica | Com IRF | Sem IRF | Diferença [IC 95%]")
    for chave in ("recall", "fp_geral", "fp_estresse"):
        d = resultado["diferencas"][chave]
        print(f"{args.mundo} | {chave} | {resultado['com_irf'][chave]:.3f} | "
              f"{resultado['sem_irf'][chave]:.3f} | {d['ponto']:+.3f} "
              f"[{d['ic95'][0]:+.3f}; {d['ic95'][1]:+.3f}]")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    destino = REPORTS_DIR / f"irf_fase3_{args.mundo}.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(destino)


if __name__ == "__main__":
    main()
