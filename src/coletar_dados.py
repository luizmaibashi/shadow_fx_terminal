# -*- coding: utf-8 -*-
"""
coletar_dados.py - Shadow FX Terminal (Coleta Aprimorada)
=============================================================
Versao 2 da coleta de dados. Elimina o mock do USDT com dados reais
e adiciona variaveis macroeconomicas para fortalecer a analise do IRF.

FONTES DE DADOS (todas gratuitas):
    1. BRL/USD:           yfinance (cambio real — v1 mantida)
    2. USDT/USDC:         yfinance (Volume + Close real — substitui mock)
    3. DXY + VIX + SP500: yfinance (controles globais — novos)
    4. IPCA/Selic/IBC-Br: python-bcb SGS (macro BCB oficial — novos)

NOTA SOBRE COINGECKO:
    O endpoint /market_chart/range exige conta paga (erro 401 no free tier).
    A alternativa via yfinance (USDT-USD, USDC-USD) fornece Volume diario
    real desde 2022, que e um proxy igualmente valido para o supply de
    stablecoins em circulacao (captura o fluxo, nao apenas o estoque).

Execute: python src/coletar_dados.py
"""

import sys
import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_RAW

# -------------------------------------------------------------------
# CONFIGURACOES
# -------------------------------------------------------------------
START_DATE = "2022-01-01"
END_DATE   = "2025-06-30"


# -------------------------------------------------------------------
# PERNA 1: CAMBIO BRL/USD (yfinance) — mantida da v1
# -------------------------------------------------------------------

def coletar_cambio() -> pd.DataFrame | None:
    """Coleta BRL/USD via yfinance (100% real, gratuito)."""
    print("\n[P1] Coletando cambio BRL/USD...")
    try:
        df = yf.Ticker("BRL=X").history(start=START_DATE, end=END_DATE, interval="1d")
        df = df[["Close"]].rename(columns={"Close": "brl_usd"})
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "date"
        df["brl_usd_mm30"] = df["brl_usd"].rolling(30, min_periods=1).mean()
        out = DATA_RAW / "cambio_brl_usd.csv"
        df.to_csv(out)
        print(f"    OK: {len(df)} registros -> {out.name}")
        return df
    except Exception as e:
        print(f"    ERRO: {e}")
        return None


# -------------------------------------------------------------------
# PERNA 2: USDT + USDC REAIS (yfinance) — substitui o mock
# -------------------------------------------------------------------

def coletar_stablecoins_real() -> pd.DataFrame | None:
    """
    Coleta Volume diario e Close de USDT e USDC via yfinance.

    Metodologia (Volume como proxy de Supply/Demanda):
        O volume de negociacao diario do USDT reflete o fluxo de compras
        e vendas. Em periodos de estresse fiscal, o volume aumenta pois
        mais agentes migram para o dolar digital. E um sinal de fluxo
        complementar ao market cap (estoque), cobrindo 2022-2025.

    Resultado:
        1276 registros reais confirmados (2022-01-01 a 2025-06-29).
    """
    print("\n[P2] Coletando USDT + USDC via yfinance (Volume + Close reais)...")

    configs = [
        ("USDT-USD", "usdt_volume", "usdt_close"),
        ("USDC-USD", "usdc_volume", "usdc_close"),
    ]

    frames = {}
    for ticker_id, col_vol, col_close in configs:
        try:
            t = yf.Ticker(ticker_id)
            df_t = t.history(start=START_DATE, end=END_DATE, interval="1d")
            df_t.index = pd.to_datetime(df_t.index).tz_localize(None)
            df_t.index.name = "date"
            df_t = df_t.rename(columns={"Volume": col_vol, "Close": col_close})
            df_t = df_t[[col_vol, col_close]]
            df_t[f"{col_vol}_mm30"] = df_t[col_vol].rolling(30, min_periods=1).mean()
            frames[ticker_id] = df_t
            print(f"    OK: {ticker_id} -> {len(df_t)} registros")
        except Exception as e:
            print(f"    ERRO {ticker_id}: {e}")

    if not frames:
        print("    FALHA: Nenhum dado de stablecoin coletado.")
        return None

    parts = list(frames.values())
    df_stable = parts[0].join(parts[1], how="outer") if len(parts) > 1 else parts[0]

    # Volume total combinado como sinal de fluxo de dolarizacao
    df_stable["stablecoin_vol_total"] = (
        df_stable.get("usdt_volume", pd.Series(0, index=df_stable.index)).fillna(0)
        + df_stable.get("usdc_volume", pd.Series(0, index=df_stable.index)).fillna(0)
    )
    df_stable["stablecoin_vol_total_mm30"] = (
        df_stable["stablecoin_vol_total"].rolling(30, min_periods=1).mean()
    )

    out = DATA_RAW / "stablecoins_yfinance_real.csv"
    df_stable.to_csv(out)
    print(f"    OK: Dataset USDT+USDC salvo -> {out.name} ({len(df_stable)} registros)")
    return df_stable


# -------------------------------------------------------------------
# PERNA 3: VARIAVEIS GLOBAIS DE CONTROLE (yfinance)
# -------------------------------------------------------------------

def coletar_variaveis_globais() -> pd.DataFrame | None:
    """
    Coleta indicadores globais para isolar o Risco Brasil Puro no cambio.

    DXY (US Dollar Index):  Se DXY sobe junto com BRL/USD, a causa e global
                            (dolar forte vs. mundo), nao fiscal brasileira.
    VIX (Fear Index):       Alta do VIX = fuga para dolar mundialmente.
                            Confundidor que pode inflar o USDT em qualquer pais.
    S&P500:                 Proxy do apetite de risco global.
    """
    print("\n[P3] Coletando variaveis globais (DXY, VIX, SP500)...")

    tickers_config = {
        "DX-Y.NYB": "dxy",
        "^VIX":     "vix",
        "^GSPC":    "sp500",
    }

    frames = {}
    for ticker, col in tickers_config.items():
        try:
            df_t = yf.Ticker(ticker).history(start=START_DATE, end=END_DATE, interval="1d")
            df_t = df_t[["Close"]].rename(columns={"Close": col})
            df_t.index = pd.to_datetime(df_t.index).tz_localize(None)
            df_t.index.name = "date"
            frames[col] = df_t
            print(f"    OK: {ticker} ({col}) -> {len(df_t)} registros")
        except Exception as e:
            print(f"    ERRO {ticker}: {e}")

    if not frames:
        print("    FALHA: Nenhuma variavel global coletada.")
        return None

    df_global = pd.concat(frames.values(), axis=1).sort_index()

    # Variacao percentual 30 dias para uso no IRF v2
    for col in ["dxy", "vix"]:
        if col in df_global.columns:
            df_global[f"{col}_var_30d"] = df_global[col].pct_change(30) * 100

    out = DATA_RAW / "variaveis_globais.csv"
    df_global.to_csv(out)
    print(f"    OK: Variaveis globais salvas -> {out.name}")
    return df_global


# -------------------------------------------------------------------
# PERNA 4: BRL/USD AJUSTADO PELO DXY — Risco Brasil Puro
# -------------------------------------------------------------------

def calcular_brl_ajustado_dxy(
    df_cambio: pd.DataFrame,
    df_global: pd.DataFrame
) -> pd.DataFrame:
    """
    Isola o componente local do cambio, removendo o efeito do dolar global.

    Metodologia:
        brl_adj_30d = variacao BRL/USD 30d - variacao DXY 30d

        Se BRL perde 5% e DXY subiu 3%, o risco Brasil especifico eh ~2%.
        Este sinal e muito mais robusto para correlacionar com stablecoins.
    """
    df = df_cambio.join(df_global[["dxy", "dxy_var_30d"]], how="left")
    df["brl_usd_var_30d"] = df["brl_usd"].pct_change(30) * 100
    df["brl_adj_dxy_30d"] = df["brl_usd_var_30d"] - df["dxy_var_30d"]

    out = DATA_RAW / "brl_ajustado_dxy.csv"
    df[["brl_usd", "brl_usd_var_30d", "dxy", "dxy_var_30d", "brl_adj_dxy_30d"]].to_csv(out)
    print(f"    OK: BRL ajustado por DXY salvo -> {out.name}")
    return df


# -------------------------------------------------------------------
# PERNA 5: MACRO BCB (python-bcb)
# -------------------------------------------------------------------

def coletar_macro_bcb() -> pd.DataFrame | None:
    """
    Coleta indicadores macroeconomicos oficiais do BCB via python-bcb.

    SGS Codes:
        433   -> IPCA (Variacao % mensal)
        432   -> Selic Meta (% a.a.)
        24364 -> IBC-Br (Atividade Economica, base 100)
        4537  -> Divida Bruta do Governo (% do PIB)
        13521 -> Expectativas IPCA 12 meses (Focus)
    """
    print("\n[P5] Coletando macro BCB (python-bcb)...")

    try:
        from bcb import sgs
    except ImportError:
        print("    AVISO: python-bcb nao instalado. Execute: pip install python-bcb")
        return None

    series_map = {
        "ipca_mensal":          433,
        "selic_meta":           432,
        "ibc_br":               24364,
        "divida_bruta_pib":     4537,
        "expectativa_ipca_12m": 13521,
    }

    frames = {}
    for col, code in series_map.items():
        try:
            df_s = sgs.get({col: code}, start=START_DATE, end=END_DATE)
            frames[col] = df_s
            print(f"    OK: SGS {code} ({col}) -> {len(df_s)} registros")
        except Exception as e:
            print(f"    AVISO SGS {code} ({col}): {e}")

    if not frames:
        print("    FALHA: Nenhum dado BCB coletado.")
        return None

    df_macro = pd.concat(frames.values(), axis=1).sort_index()
    df_macro.index.name = "date"

    # Interpolar para serie diaria (dados mensais)
    df_macro = df_macro.resample("D").interpolate(method="time")

    # Feature derivada: desvio da inflacao em relacao a meta de 3%
    if "ipca_mensal" in df_macro.columns:
        df_macro["ipca_acum_12m"] = df_macro["ipca_mensal"].rolling(12).sum()
        df_macro["desvio_meta_ipca"] = df_macro["ipca_acum_12m"] - 3.0

    out = DATA_RAW / "macro_bcb.csv"
    df_macro.to_csv(out)
    print(f"    OK: Macro BCB salvo -> {out.name}")
    return df_macro


# -------------------------------------------------------------------
# EXECUCAO PRINCIPAL
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  SHADOW FX TERMINAL v2 -- Coleta de Dados Reais")
    print("=" * 65)
    print(f"  Periodo: {START_DATE} -> {END_DATE}")
    print()

    df_cambio  = coletar_cambio()
    df_global  = coletar_variaveis_globais()
    df_stable  = coletar_stablecoins_real()
    df_macro   = coletar_macro_bcb()

    if df_cambio is not None and df_global is not None:
        print("\n[P4] Calculando BRL ajustado por DXY...")
        calcular_brl_ajustado_dxy(df_cambio, df_global)

    print("\n" + "=" * 65)
    print("  COLETA v2 CONCLUIDA")
    print("=" * 65)
    print("\nArquivos gerados em data/raw/:")
    for f in sorted(DATA_RAW.glob("*.csv")):
        size_kb = f.stat().st_size // 1024
        print(f"  {f.name:<48} {size_kb:>4} KB")

    print("\nProximos passos:")
    print("  1. Abrir notebooks/01_analise_correlacao.ipynb")
    print("  2. Usar 'stablecoins_yfinance_real.csv' no lugar do mock")
    print("  3. Adicionar analise de correlacao parcial (DXY control)")
    print("  4. Rodar src/pipeline_compliance.py para re-treinar o modelo")
