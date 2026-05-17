# -*- coding: utf-8 -*-
"""
validacao_estatistica.py - Shadow FX Terminal
==================================================
Valida a correlacao com dados reais e executa a analise de correlacao parcial
(controlando DXY) para testar a robustez do fenomeno de dolarizacao informal.

Execute: python src/validacao_estatistica.py
"""
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_RAW, calcular_correlacao_spearman,
    calcular_correlacao_parcial, adicionar_features_temporais
)

def main():
    print("=" * 65)
    print("  VALIDACAO ESTATISTICA v2 -- DADOS REAIS")
    print("=" * 65)

    # Carregar os datasets reais
    df_cambio  = pd.read_csv(DATA_RAW / "cambio_brl_usd.csv", index_col="date", parse_dates=True)
    df_stable  = pd.read_csv(DATA_RAW / "stablecoins_yfinance_real.csv", index_col="date", parse_dates=True)
    df_global  = pd.read_csv(DATA_RAW / "variaveis_globais.csv", index_col="date", parse_dates=True)
    df_brl_adj = pd.read_csv(DATA_RAW / "brl_ajustado_dxy.csv", index_col="date", parse_dates=True)

    # Alinhar
    df = df_cambio[["brl_usd", "brl_usd_mm30"]].join(
        df_stable[["usdt_volume", "usdt_volume_mm30"]], how="inner"
    ).join(
        df_global[["dxy", "dxy_var_30d"]], how="left"
    ).join(
        df_brl_adj[["brl_adj_dxy_30d", "brl_usd_var_30d"]], how="left"
    ).dropna(subset=["brl_usd", "usdt_volume"])

    df = adicionar_features_temporais(df)
    inicio = df.index[0].date()
    fim    = df.index[-1].date()
    print(f"\nDataset unificado: {len(df)} registros ({inicio} -> {fim})")

    # --- CORRELACAO BRUTA TOTAL ---
    print("\n--- 1. CORRELACAO SPEARMAN BRUTA (BRL/USD x Volume USDT) ---")
    res = calcular_correlacao_spearman(df["brl_usd"], df["usdt_volume"])
    print(f"  Coef: {res['coef']}  |  p={res['p_value']}  |  sig={res['significativo']}  |  Forca: {res['forca']}")

    # --- CORRELACAO POR SEMESTRE ---
    print("\n--- 2. CORRELACAO POR SEMESTRE (dados reais) ---")
    for sem in sorted(df["semestre"].unique()):
        sub = df[df["semestre"] == sem]
        r = calcular_correlacao_spearman(sub["brl_usd"], sub["usdt_volume"])
        sig = "SIM" if r["significativo"] else "NAO"
        coef_str = f"{r['coef']:+.3f}" if r["coef"] is not None else "  N/A "
        print(f"  {sem}: r={coef_str}  |  sig={sig}  |  n={len(sub):3d}  |  {r['forca']}")

    # --- CORRELACAO PARCIAL (controlando DXY) ---
    print("\n--- 3. CORRELACAO PARCIAL: BRL x USDT | controlando DXY ---")
    df_p = df[["brl_usd", "usdt_volume", "dxy"]].dropna()
    if len(df_p) >= 30:
        res_p = calcular_correlacao_parcial(
            df_p["usdt_volume"],
            df_p["brl_usd"],
            df_p["dxy"]
        )
        print(f"  Coef Bruto:    {res_p['coef_bruto']}")
        print(f"  Coef Parcial:  {res_p['coef_parcial']}  (apos remover efeito do DXY global)")
        print(f"  Reducao:       {res_p['reducao_pct']}%")
        print(f"  {res_p['interpretacao']}")

    # --- CORRELACAO MM30 (suavizado, metodologia do paper) ---
    print("\n--- 4. CORRELACAO MM30 (Media Movel 30d, metodologia Britto 2026) ---")
    df_mm = df[["brl_usd_mm30", "usdt_volume_mm30", "dxy"]].dropna()
    res_mm = calcular_correlacao_spearman(df_mm["brl_usd_mm30"], df_mm["usdt_volume_mm30"])
    print(f"  Coef MM30: {res_mm['coef']}  |  sig={res_mm['significativo']}  |  {res_mm['forca']}")

    if len(df_mm) >= 30:
        res_p_mm = calcular_correlacao_parcial(
            df_mm["usdt_volume_mm30"],
            df_mm["brl_usd_mm30"],
            df_mm["dxy"]
        )
        print(f"  Parcial MM30:  {res_p_mm['coef_parcial']}  (apos DXY)")
        print(f"  Reducao:       {res_p_mm['reducao_pct']}%")
        print(f"  {res_p_mm['interpretacao']}")

    print("\n" + "=" * 65)
    print("  VALIDACAO CONCLUIDA")
    print("=" * 65)

if __name__ == "__main__":
    main()
