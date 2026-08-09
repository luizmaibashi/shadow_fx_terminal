# -*- coding: utf-8 -*-
"""
comparar_correlacao_br.py - Shadow FX Terminal
=================================================
Compara a correlacao Spearman de brl_usd com:
    (a) volume Foxbit BR (dado brasileiro real, coletar_foxbit.py)
    (b) volume USDT global (yfinance, ja usado no projeto)

Responde a pergunta de falseabilidade da sabatina (grill-with-docs,
2026-08-09): o sinal Foxbit-BR supera o global? Se sim, justifica
somar como sinal adicional no IRF v2 numa rodada futura (fora de
escopo aqui - ver docs/wayfinder/shadow-fx-dado-brasil-especifico/
0004-integracao-no-pipeline.md).

Execute: python src/comparar_correlacao_br.py
"""
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_RAW, calcular_correlacao_spearman


def main():
    print("=" * 65)
    print("  Comparacao: Foxbit BR vs Volume Global")
    print("=" * 65)

    df_cambio = pd.read_csv(DATA_RAW / "cambio_brl_usd.csv", index_col="date", parse_dates=True)
    df_foxbit = pd.read_csv(DATA_RAW / "foxbit_brl.csv", index_col="date", parse_dates=True)
    df_global = pd.read_csv(DATA_RAW / "stablecoins_yfinance_real.csv", index_col="date", parse_dates=True)

    df = df_cambio[["brl_usd"]].join(
        df_foxbit[["foxbit_vol_total"]], how="inner"
    ).join(
        df_global[["usdt_volume"]], how="inner"
    ).dropna()

    print(f"\n  Linhas comparadas (intersecao das 3 series): {len(df)}")

    r_foxbit = calcular_correlacao_spearman(df["brl_usd"], df["foxbit_vol_total"])
    r_global = calcular_correlacao_spearman(df["brl_usd"], df["usdt_volume"])

    print(f"\n  brl_usd x foxbit_vol_total (BR real):  r={r_foxbit['coef']:+.3f}  p={r_foxbit['p_value']:.4f}  ({r_foxbit['forca']})")
    print(f"  brl_usd x usdt_volume (global):        r={r_global['coef']:+.3f}  p={r_global['p_value']:.4f}  ({r_global['forca']})")

    print()
    if abs(r_foxbit["coef"]) > abs(r_global["coef"]):
        print("  RESULTADO: Foxbit-BR supera o sinal global.")
        print("  Justifica avaliar inclusao no IRF v2 (fora de escopo aqui).")
    else:
        print("  RESULTADO: Foxbit-BR NAO supera o sinal global.")
        print("  Volume global continua sendo o proxy mais forte disponivel.")


if __name__ == "__main__":
    main()
