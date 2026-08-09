# -*- coding: utf-8 -*-
"""
coletar_foxbit.py - Shadow FX Terminal (Dado Brasil-Especifico)
==================================================================
Coleta volume REAL negociado na Foxbit (exchange brasileira) para os
pares USDT/BRL e USDC/BRL, via API publica (sem autenticacao).

PROBLEMA QUE ESTE SCRIPT RESOLVE:
    O volume de stablecoin usado hoje no projeto (stablecoins_yfinance_real.csv)
    e GLOBAL - nao identifica se foi o Brasil que comprou. A Foxbit e uma
    exchange brasileira (~41% do volume USDT/USDC negociado no pais, fonte:
    docs/wayfinder/shadow-fx-dado-brasil-especifico/0002-fontes-de-dado-br.md)
    - seu volume e brasileiro por jurisdicao, nao por proxy.

METODOLOGIA:
    Endpoint publico de candlesticks diarios (OHLCV + numero de trades),
    paginado em blocos de ate 500 dias (limite do endpoint - requisicao
    unica sem paginacao trunca silenciosamente em 100 linhas).

LIMITACOES DESTA ABORDAGEM (documentadas):
    1. Cobre so 1 exchange (Foxbit) - nao e 100% do volume BR, e uma amostra.
    2. Nao inclui volume P2P nem outras exchanges brasileiras.
    3. API nao documenta SLA formal de uptime/estabilidade historica.

Execute: python src/coletar_foxbit.py
"""
import sys
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_RAW

START_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
END_DATE   = datetime(2025, 6, 30, tzinfo=timezone.utc)
BASE_URL   = "https://api.foxbit.com.br/rest/v3/markets/{symbol}/candlesticks"
LIMITE_PAGINA_DIAS = 500  # maximo aceito pelo endpoint (erro 400 acima disso)


def coletar_candles(symbol: str) -> pd.DataFrame:
    """Coleta candles diarios paginados de um mercado Foxbit (ex.: 'usdtbrl').

    Retorna DataFrame com colunas: date, volume, close, n_trades.
    """
    linhas = []
    cursor = START_DATE

    while cursor < END_DATE:
        fim_pagina = min(cursor + timedelta(days=LIMITE_PAGINA_DIAS), END_DATE)
        params = {
            "interval": "1d",
            "start_time": cursor.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": fim_pagina.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": LIMITE_PAGINA_DIAS,
        }
        resp = requests.get(BASE_URL.format(symbol=symbol), params=params, timeout=30)
        resp.raise_for_status()
        pagina = resp.json()

        for candle in pagina:
            open_time_ms, _open, _high, _low, close, _close_time_ms, base_vol, _quote_vol, n_trades, _tbv, _tqv = candle
            linhas.append({
                "date": pd.to_datetime(int(open_time_ms), unit="ms"),
                "volume": float(base_vol),
                "close": float(close),
                "n_trades": int(n_trades),
            })

        print(f"    {symbol}: pagina {cursor.date()} -> {fim_pagina.date()} ({len(pagina)} candles)")
        cursor = fim_pagina

    df = pd.DataFrame(linhas).drop_duplicates(subset=["date"]).sort_values("date")
    df = df.set_index("date")
    return df


def main():
    print("=" * 65)
    print("  SHADOW FX TERMINAL - Foxbit BR (Dado Brasil-Especifico)")
    print("=" * 65)
    print(f"  Periodo: {START_DATE.date()} -> {END_DATE.date()}")
    print()

    print("  Coletando USDT/BRL...")
    df_usdt = coletar_candles("usdtbrl")
    print(f"    OK: {len(df_usdt)} dias")

    print("  Coletando USDC/BRL...")
    df_usdc = coletar_candles("usdcbrl")
    print(f"    OK: {len(df_usdc)} dias")

    df = df_usdt.add_prefix("foxbit_usdt_").join(
        df_usdc.add_prefix("foxbit_usdc_"), how="outer"
    )
    df["foxbit_vol_total"] = (
        df["foxbit_usdt_volume"].fillna(0) + df["foxbit_usdc_volume"].fillna(0)
    )

    out = DATA_RAW / "foxbit_brl.csv"
    df.to_csv(out)
    print(f"\n  OK: {len(df)} dias salvos -> {out.name}")
    print(f"  Colunas: {list(df.columns)}")


if __name__ == "__main__":
    main()
