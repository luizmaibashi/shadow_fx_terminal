# -*- coding: utf-8 -*-
"""
coletar_google_trends_br.py - Shadow FX Terminal (Atribuicao Geografica)
=========================================================================
Coleta dados do Google Trends FILTRADOS PARA O BRASIL (geo='BR') como
evidencia de atribuicao geografica do fenomeno de dolarizacao informal.

PROBLEMA QUE ESTE SCRIPT RESOLVE:
    Os dados de volume do USDT (yfinance, CoinGecko, Glassnode) sao GLOBAIS.
    Nao e possivel identificar pelos dados on-chain se foi o Brasil que
    comprou USDT. Esta e uma limitacao explicita do paper de Britto (2026),
    que usa dados de busca web como proxy de demanda geolocalizada.

METODOLOGIA:
    Google Trends fornece o indice de interesse de busca por palavras-chave
    filtrado por pais (geo='BR'). Se o IPCA sobe, o BRL cai e SIMULTANEAMENTE
    o brasileiro busca mais por "USDT" e "comprar dolar" no Google, isso e
    evidencia de atribuicao geografica da demanda.

LIMITACOES DESTA ABORDAGEM (documentadas):
    1. Google Trends retorna INDICE RELATIVO (0-100), nao volume absoluto.
    2. Dados sao semanais, nao diarios — granularidade menor.
    3. Nem todo brasileiro que compra USDT pesquisa no Google antes.
    4. Pode haver ruido de outras regioes de lingua portuguesa.
    5. pytrends e uma API nao-oficial — sujeita a rate limiting (429).

Execute: python src/coletar_google_trends_br.py
"""

import sys
import time
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_RAW


# -------------------------------------------------------------------
# CONFIGURACOES
# -------------------------------------------------------------------
START_DATE = "2022-01-01"
END_DATE   = "2025-06-30"
GEO        = "BR"  # FUNDAMENTAL: filtra exclusivamente para o Brasil

# Palavras-chave representativas de interesse em dolarizacao
# Agrupadas em lotes de 5 (limite do Google Trends por requisicao)
GRUPOS_KW = [
    # Grupo 1: Interesse direto em stablecoins/USDT
    ["USDT", "stablecoin", "comprar dolar", "Tether", "dolarizacao"],
    # Grupo 2: Contexto macroeconomico brasileiro
    ["real desvalorizado", "inflacao Brasil", "cambio dolar", "hedge cambial", "fuga de capital"],
]


def coletar_trends_grupo(kw_list: list, grupo_num: int, retries: int = 3) -> pd.DataFrame | None:
    """
    Coleta o interesse de busca semanal para um grupo de palavras-chave no Brasil.

    Args:
        kw_list:   Lista de palavras-chave (max 5).
        grupo_num: Numero do grupo (para logging).
        retries:   Tentativas em caso de rate limit (429).

    Returns:
        DataFrame semanal com colunas = palavras-chave, index = data.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("    ERRO: pytrends nao instalado. Execute: pip install pytrends")
        return None

    print(f"\n  Grupo {grupo_num}: {kw_list}")

    for attempt in range(retries):
        try:
            # Aguardar entre requisicoes para evitar rate limit
            wait = 5 + (attempt * 15)
            time.sleep(wait)

            pt = TrendReq(hl="pt-BR", tz=180, timeout=(15, 40))
            pt.build_payload(
                kw_list,
                timeframe=f"{START_DATE} {END_DATE}",
                geo=GEO,  # BRASIL
                cat=0,
                gprop="",
            )

            time.sleep(3)
            df = pt.interest_over_time()

            if df is None or df.empty:
                print(f"    Tentativa {attempt+1}: sem dados retornados.")
                continue

            # Remover coluna 'isPartial' do Google Trends
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])

            df.index.name = "date"
            n = len(df)
            print(f"    OK: {n} semanas de dados (geo=BR)")
            return df

        except Exception as e:
            err_name = type(e).__name__
            print(f"    Tentativa {attempt+1} falhou ({err_name}): {str(e)[:80]}")
            if "429" in str(e) or "TooManyRequests" in err_name:
                espera = 60 + (attempt * 30)
                print(f"    Rate limit detectado. Aguardando {espera}s...")
                time.sleep(espera)

    print(f"    FALHA: grupo {grupo_num} nao coletado apos {retries} tentativas.")
    return None


def consolidar_trends(frames: list) -> pd.DataFrame | None:
    """
    Consolida os grupos de keywords em um unico DataFrame.
    Adiciona metrica composta 'indice_interesse_dolarizacao'.
    """
    validos = [f for f in frames if f is not None]
    if not validos:
        return None

    # Join por data (indice semanal)
    df_all = validos[0]
    for df_extra in validos[1:]:
        df_all = df_all.join(df_extra, how="outer")

    # Indice composto: media das colunas de interesse em stablecoins (grupo 1)
    cols_stablecoin = ["USDT", "stablecoin", "Tether"]
    cols_existentes = [c for c in cols_stablecoin if c in df_all.columns]

    if cols_existentes:
        df_all["indice_interesse_dolarizacao"] = df_all[cols_existentes].mean(axis=1)
        # Media movel de 4 semanas (aproximadamente 30 dias)
        df_all["indice_interesse_mm4s"] = df_all["indice_interesse_dolarizacao"].rolling(4, min_periods=1).mean()

    return df_all


def main():
    print("=" * 65)
    print("  SHADOW FX TERMINAL - Google Trends BR (Atribuicao Geografica)")
    print("=" * 65)
    print(f"  Periodo: {START_DATE} -> {END_DATE}")
    print(f"  Filtro geografico: geo='{GEO}' (exclusivo Brasil)")
    print()
    print("  NOTA METODOLOGICA:")
    print("  Este script busca EVIDENCIA de que a demanda por USDT e")
    print("  localmente brasileira. O volume on-chain (USDT-USD) e global")
    print("  e nao permite identificar o pais comprador por si so.")
    print()

    frames = []
    for i, grupo in enumerate(GRUPOS_KW, 1):
        df_grupo = coletar_trends_grupo(grupo, i)
        frames.append(df_grupo)
        # Pausa entre grupos
        if i < len(GRUPOS_KW):
            print("  Aguardando 30s entre grupos...")
            time.sleep(30)

    df_trends = consolidar_trends(frames)

    if df_trends is None:
        print("\n  FALHA: Nenhum dado coletado. Tente novamente mais tarde.")
        return

    # Filtrar pelo periodo do paper
    df_trends = df_trends[
        (df_trends.index >= START_DATE) & (df_trends.index <= END_DATE)
    ]

    out = DATA_RAW / "google_trends_br_stablecoin.csv"
    df_trends.to_csv(out)

    print(f"\n  OK: {len(df_trends)} semanas salvas -> {out.name}")
    print(f"\n  Colunas: {list(df_trends.columns)}")
    print()
    print("  PROXIMO PASSO:")
    print("  Correlacionar 'indice_interesse_dolarizacao' com BRL/USD")
    print("  para testar se o interesse de busca BR co-move com o cambio.")


if __name__ == "__main__":
    main()
