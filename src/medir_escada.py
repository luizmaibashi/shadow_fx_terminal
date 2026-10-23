# -*- coding: utf-8 -*-
"""
medir_escada.py - Shadow FX Terminal
Mede cada degrau da cascata contra o rotulo do dataset sintetico.

Responde: cada degrau (regra -> Isolation Forest -> score final) se paga?
Fonte dos numeros da revisao docs/revisao/2026-10-REVISAO.md (secao 2.2 e 4.1).

Toda proporcao sai com n e IC Wilson 95%. A unidade honesta e o usuario
(10 fracionadores), nao a transacao — transacoes do mesmo usuario nao sao
independentes, por isso o script imprime as duas visoes.

Execute: python src/medir_escada.py [caminho_do_csv]
"""

import sys
from math import sqrt
from pathlib import Path

import pandas as pd
from scipy.stats import ks_2samp

CSV_PADRAO = (
    Path(__file__).resolve().parent.parent
    / "deploy" / "hf_space" / "data" / "processed" / "resultado_compliance.csv"
)

# Regras de suspeita comportamental. R1/R2 (valor e volume) sao de reporte
# obrigatorio e acertam o institucional legitimo, por isso ficam fora.
REGRAS_COMPORTAMENTO = "R3|R4|R5"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC de Wilson para a proporcao k/n, em fracao (0-1)."""
    if n <= 0:
        raise ValueError("n precisa ser positivo")
    if not 0 <= k <= n:
        raise ValueError("k precisa estar entre 0 e n")
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    meia = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centro - meia), min(1.0, centro + meia)


def fmt(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}% [{100 * lo:.1f}; {100 * hi:.1f}]"


def carregar(caminho: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho)
    df["fraude"] = df["tipo_usuario"].str.contains("suspeito")
    df["regra_comportamento"] = df["c1_razoes"].fillna("").str.contains(REGRAS_COMPORTAMENTO)
    return df


def degraus(df: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "C1 completa (R1-R6)": df["c1_flag"].astype(bool),
        "Regra R3|R4|R5": df["regra_comportamento"],
        "C2 suspeito (>70)": df["c2_classificacao"] == "suspeito",
        "alerta_final != VERDE": df["alerta_final"] != "VERDE",
    }


def medir_degrau(df: pd.DataFrame, flag: pd.Series) -> dict[str, tuple[int, int]]:
    """Contagens (k, n) de precisao, recall e FP em legitimos."""
    fraude = df["fraude"]
    return {
        "precisao": (int((flag & fraude).sum()), int(flag.sum())),
        "recall": (int((flag & fraude).sum()), int(fraude.sum())),
        "fp_legitimos": (int((flag & ~fraude).sum()), int((~fraude).sum())),
    }


def medir_por_usuario(df: pd.DataFrame) -> dict[str, tuple[int, int]]:
    u = df.groupby("user_id").agg(
        fraude=("fraude", "max"),
        regra=("regra_comportamento", "max"),
        tipo=("tipo_usuario", "first"),
    )
    poupador = u["tipo"].str.startswith("A_")
    return {
        "fracionadores pegos": (int((u["regra"] & u["fraude"]).sum()), int(u["fraude"].sum())),
        "legitimos tocados": (int((u["regra"] & ~u["fraude"]).sum()), int((~u["fraude"]).sum())),
        "poupadores tocados": (int((u["regra"] & poupador).sum()), int(poupador.sum())),
    }


def medir_ml_alem_da_regra(df: pd.DataFrame) -> dict[str, tuple[int, int]]:
    """O que o Isolation Forest acrescenta onde a regra nao acusou."""
    so_modelo = ~df["regra_comportamento"] & (df["c2_score_anomalia"] > 70)
    regra_sem_modelo = df["regra_comportamento"] & (df["c2_score_anomalia"] < 40)
    return {
        "so o modelo acusa (score>70, sem regra): fraudes": (
            int((so_modelo & df["fraude"]).sum()), int(so_modelo.sum())),
        "regra acusa e modelo da score<40: fraudes": (
            int((regra_sem_modelo & df["fraude"]).sum()), int(regra_sem_modelo.sum())),
    }


def irf_por_classe(df: pd.DataFrame) -> tuple[pd.Series, float, float]:
    medias = df.groupby("tipo_usuario")["irf_contexto"].mean().round(1)
    a = df.loc[df["tipo_usuario"].str.startswith("A_"), "irf_contexto"]
    c = df.loc[df["fraude"], "irf_contexto"]
    ks = ks_2samp(a, c)
    return medias, float(ks.statistic), float(ks.pvalue)


def main(caminho: Path) -> None:
    df = carregar(caminho)
    n_users = df.groupby("tipo_usuario")["user_id"].nunique().to_dict()
    print(f"Fonte: {caminho}")
    print(f"Transacoes: {len(df)} | usuarios por tipo: {n_users}")

    print("\n== Degraus (unidade: transacao, IC Wilson 95%) ==")
    for nome, flag in degraus(df).items():
        m = medir_degrau(df, flag)
        print(f"\n{nome} - sinaliza {int(flag.sum())}")
        for metrica, (k, n) in m.items():
            print(f"  {metrica:<13} {fmt(k, n)}")

    print("\n== Regra R3|R4|R5 por usuario (o n honesto) ==")
    for nome, (k, n) in medir_por_usuario(df).items():
        print(f"  {nome:<20} {fmt(k, n)}")

    print("\n== O que o ML acrescenta alem da regra ==")
    for nome, (k, n) in medir_ml_alem_da_regra(df).items():
        print(f"  {nome}: {fmt(k, n)}")

    cinza = int((df["c2_classificacao"] == "cinza").sum())
    print(f"\nZona cinza C2 (score 40-70, iria ao juiz LLM): {fmt(cinza, len(df))}")
    veredito = df["c3_veredito"].value_counts().to_dict()
    print(f"Vereditos C3 no snapshot: {veredito}")

    medias, d, p = irf_por_classe(df)
    print("\n== IRF por classe (se for igual, o dado nao testa a tese) ==")
    print(medias.to_string())
    print(f"KS poupador x fracionador: D={d:.3f}, p={p:.2f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PADRAO)
