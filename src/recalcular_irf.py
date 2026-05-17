# -*- coding: utf-8 -*-
"""
recalcular_irf.py - Shadow FX Terminal
==========================================
Recalcula a serie historica completa do Indice de Risco Fiscal
usando o IRF (6 sinais com dados reais) e salva como:
    data/processed/dataset_irf_completo_v2.csv e dataset_irf_completo.csv

Inputs (todos de data/raw/ — dados reais):
    - cambio_brl_usd.csv          (BRL/USD diario)
    - stablecoins_yfinance_real.csv (Volume USDT/USDC)
    - variaveis_globais.csv        (DXY, VIX)
    - brl_ajustado_dxy.csv         (BRL adj DXY — Risco Brasil Puro)
    - macro_bcb.csv                (IPCA, Selic, IBC-Br, Divida/PIB)
    - atas_copom_index.csv         (Tom Copom — score_hawkish)

Outputs:
    - data/processed/dataset_irf_completo_v2.csv
    - data/processed/dataset_irf_completo.csv

Execute: python src/recalcular_irf.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_RAW, DATA_PROC,
    carregar_dataset_mestre,
    calcular_irf_v2,
    calcular_indice_risco_fiscal,
)


def carregar_score_copom_diario() -> pd.Series:
    """
    Carrega o score hawkish do Copom e propaga para serie diaria (ffill).

    O Copom se reune a cada ~45 dias. Entre reunioes, o tom nao muda
    oficialmente — forward fill e o tratamento correto para dados de painel.
    """
    copom_path = DATA_RAW / "atas_copom_index.csv"
    if not copom_path.exists():
        print("  AVISO: atas_copom_index.csv nao encontrado. Score Copom = 0.5 (neutro).")
        return None

    df_copom = pd.read_csv(copom_path, parse_dates=["data"])
    df_copom = df_copom.sort_values("data")

    # Redirecionar para serie diaria com ffill
    idx_diario = pd.date_range("2022-01-01", "2025-06-30", freq="D")
    serie = pd.Series(
        df_copom["score_hawkish"].values,
        index=pd.DatetimeIndex(df_copom["data"].values),
        name="score_copom"
    )
    serie_diaria = serie.reindex(idx_diario).ffill().bfill()
    return serie_diaria


def calcular_serie_irf_v2(df_mestre: pd.DataFrame, score_copom_diario: pd.Series) -> pd.DataFrame:
    """
    Aplica calcular_irf_v2() linha a linha sobre o dataset mestre.

    Deriva os sinais de entrada necessarios:
        - variacao_usdt_30d:  pct_change(30) do volume USDT
        - divida_pib_var:     pct_change(1) mensal da Divida/PIB
        - ibc_br_var:         pct_change(1) do IBC-Br

    Para cada dia, chama calcular_irf_v2() e tambem calcular_indice_risco_fiscal()
    (v1) para manter compatibilidade e comparacao.
    """
    df = df_mestre.copy()

    # --- Derivar variacoes ---
    df["variacao_usdt_30d"] = df["usdt_volume"].pct_change(30) * 100
    df["variacao_cambio_30d"] = df["brl_usd"].pct_change(30) * 100

    if "divida_bruta_pib" in df.columns:
        df["divida_pib_var"] = df["divida_bruta_pib"].pct_change(1) * 100
    else:
        df["divida_pib_var"] = 0.0

    if "ibc_br" in df.columns:
        df["ibc_br_var"] = df["ibc_br"].pct_change(1) * 100
    else:
        df["ibc_br_var"] = 0.0

    # Usar desvio_meta_ipca se disponivel, senao usar ipca_mensal - 3.0
    if "desvio_meta_ipca" in df.columns:
        df["ipca_desvio_meta"] = df["desvio_meta_ipca"].fillna(0.0)
    elif "ipca_mensal" in df.columns:
        df["ipca_desvio_meta"] = (df["ipca_mensal"].rolling(12).sum() - 3.0).fillna(0.0)
    else:
        df["ipca_desvio_meta"] = 0.0

    # brl_adj_dxy_30d: usa coluna calculada ou deriva do BRL/DXY
    if "brl_adj_dxy_30d" not in df.columns or df["brl_adj_dxy_30d"].isna().all():
        df["brl_adj_dxy_30d"] = (
            df["variacao_cambio_30d"] - df.get("dxy_var_30d", pd.Series(0.0, index=df.index))
        )

    # Associar score Copom diario
    df = df.join(score_copom_diario.rename("score_copom"), how="left")
    df["score_copom"] = df["score_copom"].fillna(0.5)

    # --- Calcular IRF v2 linha a linha ---
    irf_v2_vals = []
    irf_v1_vals = []

    for _, row in df.iterrows():
        score_copom = float(row["score_copom"])

        # IRF v2
        irf_v2 = calcular_irf_v2(
            score_tom_copom   = score_copom,
            brl_adj_dxy_30d   = float(row.get("brl_adj_dxy_30d", 0) or 0),
            ipca_desvio_meta  = float(row.get("ipca_desvio_meta", 0) or 0),
            variacao_usdt_30d = float(row.get("variacao_usdt_30d", 0) or 0),
            divida_pib_var    = float(row.get("divida_pib_var", 0) or 0),
            ibc_br_var        = float(row.get("ibc_br_var", 0) or 0),
        )

        # IRF v1 (compatibilidade)
        irf_v1 = calcular_indice_risco_fiscal(
            score_tom_copom    = score_copom,
            variacao_cambio_30d= float(row.get("variacao_cambio_30d", 0) or 0),
            variacao_usdt_30d  = float(row.get("variacao_usdt_30d", 0) or 0),
        )

        irf_v2_vals.append(irf_v2)
        irf_v1_vals.append(irf_v1)

    df["irf_v2"]       = irf_v2_vals
    df["irf"]          = irf_v1_vals  # Manter coluna "irf" para compatibilidade com pipeline
    df["irf_v2_mm7d"]  = df["irf_v2"].rolling(7, min_periods=1).mean().round(2)
    df["irf_v2_mm30d"] = df["irf_v2"].rolling(30, min_periods=1).mean().round(2)

    # Classificacao semaforo
    df["irf_v2_nivel"] = pd.cut(
        df["irf_v2"],
        bins=[0, 30, 60, 100],
        labels=["BAIXO", "MEDIO", "ALTO"],
        include_lowest=True,
    )

    return df


def main():
    print("=" * 65)
    print("  IRF v2 — Recalculo com Dados Reais")
    print("=" * 65)

    # 1. Carregar dataset mestre (todos os sinais reais)
    print("\n[1/4] Carregando dataset mestre...")
    df_mestre = carregar_dataset_mestre()
    print(f"      {len(df_mestre)} dias | {len(df_mestre.columns)} colunas")

    # 2. Carregar score Copom diario
    print("\n[2/4] Carregando score Copom (forward fill)...")
    score_copom = carregar_score_copom_diario()
    if score_copom is not None:
        print(f"      27 reunioes -> serie diaria de {len(score_copom)} dias")

    # 3. Calcular IRF v2 diario
    print("\n[3/4] Calculando IRF v2 (6 sinais reais)...")
    df_irf = calcular_serie_irf_v2(df_mestre, score_copom)

    # Estatisticas
    print(f"      IRF v2 medio: {df_irf['irf_v2'].mean():.1f}")
    print(f"      IRF v2 max:   {df_irf['irf_v2'].max():.1f}")
    print(f"      IRF v2 min:   {df_irf['irf_v2'].min():.1f}")
    alto = (df_irf["irf_v2_nivel"] == "ALTO").sum()
    medio = (df_irf["irf_v2_nivel"] == "MEDIO").sum()
    baixo = (df_irf["irf_v2_nivel"] == "BAIXO").sum()
    print(f"      Nivel ALTO:   {alto} dias ({alto/len(df_irf)*100:.1f}%)")
    print(f"      Nivel MEDIO:  {medio} dias ({medio/len(df_irf)*100:.1f}%)")
    print(f"      Nivel BAIXO:  {baixo} dias ({baixo/len(df_irf)*100:.1f}%)")

    # Comparar v1 vs v2 por semestre
    print("\n      Comparacao IRF v1 vs IRF v2 por semestre:")
    for sem in sorted(df_irf["semestre"].unique()):
        sub = df_irf[df_irf["semestre"] == sem]
        v1_m = sub["irf"].mean()
        v2_m = sub["irf_v2"].mean()
        print(f"      {sem}: v1={v1_m:.1f}  v2={v2_m:.1f}  delta={v2_m-v1_m:+.1f}")

    # 4. Salvar
    print("\n[4/4] Salvando...")
    out_v2 = DATA_PROC / "dataset_irf_completo_v2.csv"
    df_irf.to_csv(out_v2)
    print(f"      -> {out_v2.name} ({len(df_irf)} linhas, {len(df_irf.columns)} colunas)")

    # Tambem sobrescrever o arquivo padrao que o pipeline usa
    # (para que o pipeline pegue o IRF real automaticamente)
    out_padrao = DATA_PROC / "dataset_irf_completo.csv"
    df_irf.to_csv(out_padrao)
    print(f"      -> {out_padrao.name} (atualizado com IRF v2 + backward compat.)")

    print("\n" + "=" * 65)
    print("  CONCLUIDO")
    print("=" * 65)
    return df_irf


if __name__ == "__main__":
    main()
