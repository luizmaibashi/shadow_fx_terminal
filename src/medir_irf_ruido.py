"""Controle de ruido: troca o IRF por uma coluna aleatoria por dia (PREDICAO_FASE3.md).

Testa a hipotese de que o ganho do IRF no placebo vem de qualquer dimensao extra,
e nao do conteudo macro. O dia de estresse continua definido pelo IRF real.
"""

import argparse
import json

import numpy as np
import pandas as pd

from decisao import escolher_limiar_operacao, split_por_usuario
from gerador_v2 import gerar_dataset_v2
from medir_irf import (_periodo_e_estresse, _por_usuario, _taxas, _treinar_e_pontuar,
                       bootstrap_pareado)
from pipeline_compliance import engenharia_features
from utils import DATA_PROC, FEATURES_ML, REPORTS_DIR


def ruido_por_dia(datas: pd.Series, seed: int) -> pd.Series:
    """Um N(0,1) por dia, igual para todas as transacoes do dia."""
    dias = pd.Index(sorted(datas.dropna().unique()))
    rng = np.random.default_rng(seed)
    valores = pd.Series(rng.standard_normal(len(dias)), index=dias)
    return datas.map(valores)


def medir_ruido(df_tx: pd.DataFrame, df_irf: pd.DataFrame, seed: int = 42,
                seed_ruido: int = 7, x_max: float = 0.05, B: int = 2000) -> dict:
    features = engenharia_features(df_tx, df_irf)
    features["ruido"] = ruido_por_dia(features["data_ts"], seed_ruido)
    ids_cal, ids_aval = split_por_usuario(features, seed=seed)
    cal = features.loc[features["user_id"].isin(ids_cal)].copy()
    aval = features.loc[features["user_id"].isin(ids_aval)].copy()
    periodo, quartil, n_dias = _periodo_e_estresse(df_tx, df_irf)
    sem = [c for c in FEATURES_ML if c != "irf_contexto"]
    limiares = {}
    # "com_irf" e "sem_irf" sao os nomes que _taxas/bootstrap esperam; aqui "com" = com ruido.
    for nome, colunas in (("com_irf", [*sem, "ruido"]), ("sem_irf", sem)):
        score_cal, score_aval = _treinar_e_pontuar(cal, aval, colunas)
        cal[f"score_{nome}"] = score_cal
        aval[f"score_{nome}"] = score_aval
        limiar = escolher_limiar_operacao(cal, score_col=f"score_{nome}", x_max=x_max, usuarios=ids_cal)
        if limiar is None:
            raise ValueError(f"nenhum limiar operacional para {nome}")
        limiares[nome] = limiar
    usuarios = _por_usuario(aval, quartil, limiares)
    return {"com_ruido": _taxas(usuarios, "com_irf"), "sem": _taxas(usuarios, "sem_irf"),
            "diferencas": bootstrap_pareado(usuarios, B=B, seed=seed),
            "limiares": limiares, "periodo_efetivo": periodo,
            "limiar_irf_estresse": quartil, "n_dias_estresse": n_dias, "seed_ruido": seed_ruido}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mundo", choices=("v2", "placebo"), required=True)
    args = parser.parse_args()
    irf = pd.read_csv(DATA_PROC / "dataset_irf_completo.csv", index_col="date", parse_dates=True)
    df_tx = gerar_dataset_v2(irf["irf_v2"], acoplamento=args.mundo == "v2")
    resultado = medir_ruido(df_tx, irf)
    for chave in ("recall", "fp_geral", "fp_estresse"):
        d = resultado["diferencas"][chave]
        print(f"{args.mundo} | ruido | {chave} | {resultado['com_ruido'][chave]:.3f} | "
              f"{resultado['sem'][chave]:.3f} | {d['ponto']:+.3f} [{d['ic95'][0]:+.3f}; {d['ic95'][1]:+.3f}]")
    destino = REPORTS_DIR / f"irf_fase3_ruido_{args.mundo}.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(destino)


if __name__ == "__main__":
    main()
