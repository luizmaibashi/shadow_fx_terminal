# -*- coding: utf-8 -*-
"""
validacao_atribuicao_geografica.py - Shadow FX Terminal
=========================================================
Testa se o fenomeno de dolarizacao via stablecoins e especificamente brasileiro
usando Google Trends (geo=BR) como proxy de demanda geolocalizada.

CONTEXTO METODOLOGICO:
    O paper de Britto (2026) reconhece que dados on-chain (volume USDT global)
    nao permitem identificar o pais comprador. Para resolver isso, o paper
    cruza com dados de busca web geolocalizados. Este script replica e expande
    essa abordagem, com analise de correlacao parcial controlando o DXY.

Execute: python src/validacao_atribuicao_geografica.py
"""
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_RAW,
    calcular_correlacao_spearman,
    calcular_correlacao_parcial,
)


def main():
    print("=" * 65)
    print("  ATRIBUICAO GEOGRAFICA - Trends BR x BRL/USD")
    print("=" * 65)

    # Carregar dados
    df_trends = pd.read_csv(
        DATA_RAW / "google_trends_br_stablecoin.csv",
        index_col="date", parse_dates=True
    )
    df_cambio = pd.read_csv(
        DATA_RAW / "cambio_brl_usd.csv",
        index_col="date", parse_dates=True
    )
    df_global = pd.read_csv(
        DATA_RAW / "variaveis_globais.csv",
        index_col="date", parse_dates=True
    )

    # Trends e semanal: resamplear cambio e dxy para semanal
    brl_sem = df_cambio["brl_usd"].resample("W").mean()
    dxy_sem = df_global["dxy"].resample("W").mean()

    df = pd.DataFrame({"brl_usd": brl_sem, "dxy": dxy_sem})
    df = df.join(df_trends[[
        "USDT", "stablecoin", "comprar dolar",
        "indice_interesse_dolarizacao", "indice_interesse_mm4s"
    ]], how="inner")
    df = df.dropna(subset=["brl_usd", "USDT"])

    inicio = df.index[0].date()
    fim    = df.index[-1].date()
    print(f"\nDataset: {len(df)} semanas ({inicio} -> {fim})\n")

    # --- 1. Correlacao bruta por keyword ---
    print("--- 1. BRL/USD x Interesse BR (Google Trends geo=BR) ---")
    colunas = ["USDT", "stablecoin", "comprar dolar", "indice_interesse_dolarizacao"]
    for col in colunas:
        sub = df[["brl_usd", col]].dropna()
        r = calcular_correlacao_spearman(sub["brl_usd"], sub[col])
        sig = "SIM" if r["significativo"] else "NAO"
        coef = r["coef"] if r["coef"] is not None else 0.0
        print(f"  {col:<35} r={coef:+.3f}  sig={sig}  {r['forca']}")

    print()

    # --- 2. Correlacao Parcial controlando DXY ---
    print("--- 2. PARCIAL: Trends BR x BRL | DXY controlado ---")
    sub_p = df[["brl_usd", "indice_interesse_dolarizacao", "dxy"]].dropna()
    if len(sub_p) >= 30:
        rp = calcular_correlacao_parcial(
            sub_p["indice_interesse_dolarizacao"],
            sub_p["brl_usd"],
            sub_p["dxy"]
        )
        print(f"  Coef Bruto:    {rp['coef_bruto']}")
        print(f"  Coef Parcial:  {rp['coef_parcial']}  (apos remover efeito DXY global)")
        print(f"  Reducao:       {rp['reducao_pct']}%")
        print(f"  {rp['interpretacao']}")

    print()

    # --- 3. Analise Lead-Lag: o BRL cai ANTES do interesse subir? ---
    print("--- 3. LEAD-LAG: BRL/USD precede interesse BR? (lags 1-4 sem.) ---")
    col_interesse = "indice_interesse_dolarizacao"
    for lag in [1, 2, 3, 4]:
        brl_lag = df["brl_usd"].shift(lag)
        sub_lag = pd.DataFrame({
            "brl_lag": brl_lag,
            "interesse": df[col_interesse]
        }).dropna()
        r = calcular_correlacao_spearman(sub_lag["brl_lag"], sub_lag["interesse"])
        coef = r["coef"] if r["coef"] is not None else 0.0
        sig  = "SIM" if r["significativo"] else "NAO"
        print(f"  BRL defasado {lag} sem: r={coef:+.3f}  sig={sig}")

    print()
    print("=" * 65)
    print("  INTERPRETACAO METODOLOGICA")
    print("=" * 65)
    print("""
  O que prova cada resultado:

  1. Correlacao Bruta (Trends BR x BRL):
     - Mede se quando o BRL cai, o BRASILEIRO busca mais por USDT.
     - Diferente da correlacao volume USDT global x BRL, aqui o
       sinal de busca e EXCLUSIVO do Brasil (geo='BR').

  2. Correlacao Parcial (controlando DXY):
     - Mede se essa relacao existe alem do efeito do dolar global.
     - Baixa reducao = fenomeno domestico, nao reflexo do DXY.

  3. Lead-Lag:
     - Se o BRL defasado (BRL[t-1]) correlaciona mais com o
       interesse[t] do que o BRL contemporaneo, ha evidencia de
       que o cambio PRECEDE o interesse -- direcionalidade causal.

  LIMITE DESTA ABORDAGEM:
     - Google Trends e indice relativo (0-100), nao volume absoluto.
     - Representa inten~ao de compra, nao compra efetiva.
     - Complementa, mas nao substitui, dados on-chain reais.
    """)


if __name__ == "__main__":
    main()
