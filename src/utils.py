# -*- coding: utf-8 -*-
"""
utils.py - Shadow FX Terminal
==============================
Modulo central de feature engineering e funcoes utilitarias.
Isolamos aqui toda a complexidade de processamento para garantir:
- Reutilizacao entre notebooks e scripts (DRY)
- Training-serving parity (mesma logica em todos os contextos)
- Testabilidade unitaria

Principio: Este modulo nao deve ter side-effects. Apenas funcoes puras.

v2 (2026-05-05):
    - Adicionada calcular_correlacao_parcial() para controle de confundidores (ex: DXY)
    - Adicionada calcular_irf_v2() com 6 sinais ortogonais ao risco fiscal brasileiro
    - Adicionada calcular_brl_ajustado_dxy() para isolar o sinal de risco local
"""

import warnings
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path
import hashlib

# -------------------------------------------------------------------
# SEGURANCA E PRIVACIDADE (LGPD)
# -------------------------------------------------------------------
def mascarar_user_id(user_id: str) -> str:
    """Aplica hash SHA-256 para anonimizar identificadores de usuario (LGPD)."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


# -------------------------------------------------------------------
# CONFIGURACOES CENTRAIS
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW     = PROJECT_ROOT / "data" / "raw"
DATA_PROC    = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR  = PROJECT_ROOT / "reports"

# Garantir que os diretorios existam
DATA_PROC.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# FEATURE ENGINEERING: TEMPO
# -------------------------------------------------------------------
def get_semestre(date: pd.Timestamp) -> str:
    """Converte uma data para string de semestre no formato 'YYYY-SN'.
    
    Exemplo:
        >>> get_semestre(pd.Timestamp('2024-08-15'))
        '2024-S2'
    """
    return f"{date.year}-S{1 if date.month <= 6 else 2}"


def adicionar_features_temporais(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas de features temporais ao DataFrame.
    
    Colunas adicionadas: semestre, trimestre, ano, mes_num.
    O DataFrame deve ter um DatetimeIndex.
    """
    df = df.copy()
    df['semestre']   = df.index.map(get_semestre)
    df['trimestre']  = df.index.quarter
    df['ano']        = df.index.year
    df['mes_num']    = df.index.month
    return df


# -------------------------------------------------------------------
# FEATURE ENGINEERING: SERIES FINANCEIRAS
# -------------------------------------------------------------------
def calcular_media_movel(series: pd.Series, janela: int = 30) -> pd.Series:
    """Calcula a media movel simples de uma serie."""
    return series.rolling(window=janela, min_periods=1).mean()


def normalizar_min_max(series: pd.Series) -> pd.Series:
    """Normaliza uma serie para o intervalo [0, 1] usando Min-Max scaling.

    Util para comparar series em escalas diferentes (ex: BRL e bilhoes de USDT).

    AVISO DE PRODUÇÃO:
        Esta função recalcula min/max a cada chamada usando os dados da própria série.
        Em inferência com transações novas (1 por vez), isso faz a série sempre retornar
        0 ou 1 (ou 0.5 se constante), perdendo o sentido de escala.
        Em produção, armazene os min/max do dataset de treino junto com o scaler (joblib)
        e passe-os como parâmetros fixos para garantir consistência.
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(0.5, index=series.index)
    return (series - min_val) / (max_val - min_val)


def calcular_retorno_percentual(series: pd.Series, periodos: int = 1) -> pd.Series:
    """Calcula a variacao percentual entre periodos."""
    return series.pct_change(periods=periodos) * 100


# -------------------------------------------------------------------
# ANALISE ESTATISTICA
# -------------------------------------------------------------------
def calcular_correlacao_spearman(
    serie_x: pd.Series,
    serie_y: pd.Series
) -> dict:
    """Calcula a Correlacao de Spearman entre duas series.
    
    Returns:
        dict com 'coef', 'p_value', 'significativo', 'forca'.
    """
    # Alinhar e remover nulos
    df_temp = pd.DataFrame({'x': serie_x, 'y': serie_y}).dropna()
    
    if len(df_temp) < 30:
        return {'coef': None, 'p_value': None, 'significativo': False, 'forca': 'Insuficiente'}
    
    coef, p_value = spearmanr(df_temp['x'], df_temp['y'])
    
    abs_coef = abs(coef)
    if abs_coef >= 0.7:
        forca = 'Forte'
    elif abs_coef >= 0.4:
        forca = 'Moderada'
    else:
        forca = 'Fraca'
    
    return {
        'coef'        : round(coef, 3),
        'p_value'     : round(p_value, 4),
        'significativo': p_value < 0.05,
        'forca'       : forca
    }


def calcular_correlacao_parcial(
    serie_x: pd.Series,
    serie_y: pd.Series,
    serie_controle: pd.Series
) -> dict:
    """
    Calcula a Correlação de Spearman Parcial de X e Y, controlando por Z.

    Metodologia (Partial Rank Correlation):
        1. Regride os resíduos de X ~ Z (via regressão de ranks).
        2. Regride os resíduos de Y ~ Z.
        3. Calcula Spearman entre os resíduos — a correlação 'limpa' de Z.

    Caso de uso principal do projeto:
        calcular_correlacao_parcial(
            usdt_supply, brl_usd, dxy
        )
        → Responde: "O USDT ainda cresce com o BRL *mesmo após remover* o
          efeito do dólar global (DXY)?"
        Se sim: a dolarização informal no Brasil é um fenômeno LOCAL.
        Se não: a correlação pode ser apenas reflexo do DXY global.

    Args:
        serie_x:        Série principal (ex: supply USDT).
        serie_y:        Série target (ex: BRL/USD).
        serie_controle: Confundidor a ser removido (ex: DXY).

    Returns:
        dict com 'coef_parcial', 'coef_bruto', 'reducao_pct', 'interpretacao'.
    """
    df_temp = pd.DataFrame({
        'x': serie_x, 'y': serie_y, 'z': serie_controle
    }).dropna()

    if len(df_temp) < 30:
        return {
            'coef_parcial': None, 'coef_bruto': None,
            'reducao_pct': None,
            'interpretacao': 'Amostra insuficiente (<30)'
        }

    # Correlação bruta (baseline)
    coef_bruto, _ = spearmanr(df_temp['x'], df_temp['y'])

    # Resíduos via regressão linear de ranks
    from numpy.polynomial.polynomial import polyfit
    rank_x = df_temp['x'].rank()
    rank_y = df_temp['y'].rank()
    rank_z = df_temp['z'].rank()

    # Resíduos de X após remover Z
    coef_xz = np.polyfit(rank_z, rank_x, 1)
    residuo_x = rank_x - np.polyval(coef_xz, rank_z)

    # Resíduos de Y após remover Z
    coef_yz = np.polyfit(rank_z, rank_y, 1)
    residuo_y = rank_y - np.polyval(coef_yz, rank_z)

    # Correlação parcial entre os resíduos
    coef_parcial, p_parcial = spearmanr(residuo_x, residuo_y)

    reducao = abs(coef_bruto - coef_parcial)
    reducao_pct = (reducao / abs(coef_bruto) * 100) if coef_bruto != 0 else 0

    if reducao_pct > 50:
        interpretacao = (
            f"⚠️  Alta redução ({reducao_pct:.1f}%): grande parte da correlação "
            "original era efeito do confundidor."
        )
    elif reducao_pct > 20:
        interpretacao = (
            f"Redução moderada ({reducao_pct:.1f}%): o confundidor explica parte "
            "da correlação, mas o sinal local persiste."
        )
    else:
        interpretacao = (
            f"✅ Baixa redução ({reducao_pct:.1f}%): a correlação é ROBUSTA ao "
            "controle do confundidor — evidência de fenômeno local."
        )

    return {
        'coef_bruto'   : round(coef_bruto, 3),
        'coef_parcial' : round(coef_parcial, 3),
        'p_parcial'    : round(p_parcial, 4),
        'reducao_pct'  : round(reducao_pct, 1),
        'interpretacao': interpretacao,
    }


def correlacao_por_semestre(
    df: pd.DataFrame,
    col_x: str,
    col_y: str,
    min_obs: int = 30
) -> pd.DataFrame:
    """Calcula correlacao de Spearman por semestre.
    
    O DataFrame deve ter a coluna 'semestre' (use adicionar_features_temporais).
    
    Returns:
        DataFrame indexado por semestre com resultados da correlacao.
    """
    if 'semestre' not in df.columns:
        df = adicionar_features_temporais(df)
    
    resultados = []
    for semestre in sorted(df['semestre'].unique()):
        amostra = df[df['semestre'] == semestre]
        if len(amostra) >= min_obs:
            resultado = calcular_correlacao_spearman(amostra[col_x], amostra[col_y])
            resultado['semestre'] = semestre
            resultado['n_obs']    = len(amostra)
            resultados.append(resultado)
    
    return pd.DataFrame(resultados).set_index('semestre')


# -------------------------------------------------------------------
# CARREGAMENTO DE DADOS
# -------------------------------------------------------------------
def carregar_dados_base() -> pd.DataFrame:
    """Carrega e faz merge das duas bases de dados principais do projeto.

    v2 (2026-05-05): usa stablecoins_yfinance_real.csv (dados reais)
    em vez do glassnode_usdt_supply.csv (dados sinteticos da v1).

    Returns:
        DataFrame com cambio e volume USDT/USDC, indexado por data.

    Raises:
        FileNotFoundError: Se os CSVs nao existirem.
        Execute src/coletar_dados.py primeiro.
    """
    df_cambio = pd.read_csv(
        DATA_RAW / "cambio_brl_usd.csv",
        index_col="date",
        parse_dates=True
    )

    # v2: usar dados reais de stablecoins (yfinance)
    # Fallback para o mock se o arquivo real nao existir
    real_path = DATA_RAW / "stablecoins_yfinance_real.csv"
    mock_path = DATA_RAW / "glassnode_usdt_supply.csv"

    if real_path.exists():
        df_stable = pd.read_csv(real_path, index_col="date", parse_dates=True)
        # Normalizar nome da coluna principal para compatibilidade
        if "usdt_volume" in df_stable.columns and "usdt_supply" not in df_stable.columns:
            df_stable = df_stable.rename(columns={"usdt_volume": "usdt_supply"})
    else:
        import warnings
        warnings.warn(
            "Arquivo real nao encontrado. Usando mock (glassnode_usdt_supply.csv). "
            "Execute src/coletar_dados.py para obter dados reais.",
            UserWarning, stacklevel=2
        )
        df_stable = pd.read_csv(mock_path, index_col="date", parse_dates=True)

    df = df_cambio.join(df_stable, how="inner").dropna()
    df = adicionar_features_temporais(df)
    return df


def carregar_dataset_mestre() -> pd.DataFrame:
    """Carrega e unifica todos os datasets reais disponIveis (v2).

    Combina os 7 sinais do projeto em um unico DataFrame diario:
        1. BRL/USD + MM30 (cambio real - yfinance)
        2. USDT/USDC Volume + MM30 (stablecoins reais - yfinance)
        3. DXY + VIX + SP500 (variaveis globais - yfinance)
        4. BRL ajustado por DXY (risco Brasil puro - derivado)
        5. IPCA, Selic, IBC-Br, Divida/PIB (macro BCB - python-bcb)

    A Diferenco desta funcao vs. carregar_dados_base():
        carregar_dados_base() eh usada pelo pipeline de compliance
        e notebooks antigos (2 colunas). Esta funcao e usada nas
        analises mais ricas (correlacao parcial, IRF v2, exploracao).

    Returns:
        DataFrame com ate 12 colunas, indexado por data.
        Linhas com NaN em brl_usd ou usdt_volume sao removidas.
    """
    # --- Datasets obrigatorios ---
    df_cambio = pd.read_csv(
        DATA_RAW / "cambio_brl_usd.csv", index_col="date", parse_dates=True
    )
    df_stable = pd.read_csv(
        DATA_RAW / "stablecoins_yfinance_real.csv", index_col="date", parse_dates=True
    )
    # --- Datasets opcionais (nao falham se ausentes) ---
    dfs_opcionais = {}
    for nome, arquivo, colunas in [
        ("global",   "variaveis_globais.csv",       ["dxy", "vix", "dxy_var_30d"]),
        ("brl_adj",  "brl_ajustado_dxy.csv",         ["brl_adj_dxy_30d", "brl_usd_var_30d"]),
        ("macro",    "macro_bcb.csv",                ["ipca_mensal", "selic_meta", "ibc_br",
                                                      "divida_bruta_pib", "desvio_meta_ipca"]),
    ]:
        path = DATA_RAW / arquivo
        if path.exists():
            df_temp = pd.read_csv(path, index_col="date", parse_dates=True)
            cols_disponiveis = [c for c in colunas if c in df_temp.columns]
            dfs_opcionais[nome] = df_temp[cols_disponiveis]

    # --- Merge ---
    cols_stable = [
        c for c in ["usdt_volume", "usdc_volume", "usdt_volume_mm30",
                    "usdt_close", "stablecoin_vol_total", "stablecoin_vol_total_mm30"]
        if c in df_stable.columns
    ]
    df = df_cambio.join(df_stable[cols_stable], how="inner")
    for nome, df_opt in dfs_opcionais.items():
        df = df.join(df_opt, how="left")

    df = df.dropna(subset=["brl_usd", "usdt_volume"])
    df = adicionar_features_temporais(df)
    return df


# -------------------------------------------------------------------
# INDICE DE RISCO FISCAL v1 (Fase 2 — Compatibilidade)
# -------------------------------------------------------------------
def calcular_indice_risco_fiscal(
    score_tom_copom: float,
    variacao_cambio_30d: float,
    variacao_usdt_30d: float,
    pesos: dict = None
) -> float:
    """Calcula o Indice de Risco Fiscal Composto v1 (3 sinais).
    
    Mantida para compatibilidade retroativa com os testes e notebooks.
    Para análises novas, prefira calcular_irf_v2() que é mais robusto.
    
    Combina tres sinais em um indice normalizado de 0 a 100:
    - Tom hawkish/dovish da ata do Copom
    - Variacao cambial nos ultimos 30 dias
    - Crescimento do Supply de USDT nos ultimos 30 dias
    
    Args:
        score_tom_copom: Nota de 0 (altamente dovish/risco) a 1 (hawkish/ancora).
        variacao_cambio_30d: Variacao % do BRL/USD nos ultimos 30 dias.
        variacao_usdt_30d: Variacao % do supply USDT nos ultimos 30 dias.
        pesos: Dicionario com pesos para cada componente. Padrao: 40/35/25.
    
    Returns:
        Indice de 0 a 100 (maior = mais risco de fuga de capital).
    """
    if pesos is None:
        pesos = {'cambio': 0.40, 'usdt': 0.35, 'copom': 0.25}
    
    # Normalizar cada componente para [0, 1]
    sinal_cambio = min(max(variacao_cambio_30d / 10, 0), 1)
    sinal_usdt   = min(max(variacao_usdt_30d   /  5, 0), 1)
    sinal_copom  = 1 - score_tom_copom
    
    indice = (
        sinal_cambio * pesos['cambio'] +
        sinal_usdt   * pesos['usdt']   +
        sinal_copom  * pesos['copom']
    ) * 100
    
    return round(indice, 2)


# -------------------------------------------------------------------
# INDICE DE RISCO FISCAL v2 (Modelo Multidimensional — 6 sinais)
# -------------------------------------------------------------------
def calcular_irf_v2(
    score_tom_copom: float,
    brl_adj_dxy_30d: float,
    ipca_desvio_meta: float,
    variacao_usdt_30d: float,
    divida_pib_var: float = 0.0,
    ibc_br_var: float = 0.0,
    pesos: dict = None
) -> float:
    """
    Calcula o Índice de Risco Fiscal v2 com 6 sinais ortogonais.

    Evolução sobre o IRF v1:
        - brl_adj_dxy_30d: variação do BRL *descontando* o dólar global (DXY).
          Isso isola o 'Risco Brasil Puro', eliminando o confundidor global.
        - ipca_desvio_meta: quão longe a inflação está da meta (3%).
          Inflação desancorada = perda de credibilidade = fuga para USDT.
        - divida_pib_var: variação da Dívida Bruta/PIB.
          Trajetória fiscal explosiva = dominância fiscal = risco crônico.
        - ibc_br_var: variação da atividade econômica.
          Recessão + câmbio em alta = combinação que acelera dolarização.

    Args:
        score_tom_copom:  Score 0-1 (0=dovish/risco, 1=hawkish/âncora).
        brl_adj_dxy_30d:  Variação % do BRL/USD ajustada pelo DXY nos últimos 30d.
                          Positivo = real perdendo mais que o efeito global.
        ipca_desvio_meta: IPCA acumulado 12m menos a meta do BCB (ex: 4.8 - 3.0 = 1.8).
        variacao_usdt_30d: Variação % do market cap do USDT nos últimos 30d.
        divida_pib_var:   Variação mensal da Dívida Bruta/PIB (pp). Default: 0.
        ibc_br_var:       Variação % do IBC-Br (atividade econômica). Default: 0.
                          Negativo = recessão = maior fuga de capital.
        pesos:            Pesos por componente. Devem somar 1.0.

    Returns:
        Índice de 0 a 100 (maior = mais risco de fuga de capital).
    """
    if pesos is None:
        # Pesos calibrados empiricamente com base na força da correlação:
        # Dívida/PIB: r=+0.707 (melhor preditor) → peso maior
        # BRL adj DXY: sinal puro de risco local → peso relevante
        # Demais: sinais complementares
        pesos = {
            'divida':   0.30,  # Dominância fiscal estrutural — mais forte (r=+0.707)
            'cambio':   0.20,  # BRL ajustado por DXY — risco Brasil puro
            'ipca':     0.15,  # Inflação desancorada
            'copom':    0.15,  # Tom da política monetária
            'expectat': 0.10,  # Demanda por hedge (volume USDT)
            'atividade':0.10,  # Atividade econômica
        }

    # Thresholds de normalização calibrados empiricamente (p95 dos dados reais 2022-2025):
    # Cada sinal é mapeado para [0,1] onde 1 = nível de stress do percentil 95.

    # 1. Sinal Dívida/PIB: variação mensal (p95 ≈ 0.10 pp)
    #    Dividimos por 0.12 para que p95 ≈ 0.83 (abaixo de 1, mas próximo)
    sinal_divida = min(max(divida_pib_var / 0.12, 0), 1)

    # 2. Sinal Câmbio ajustado DXY: desvalorização LOCAL do BRL (p95 ≈ +6.7%)
    sinal_cambio = min(max(brl_adj_dxy_30d / 7.0, 0), 1)

    # 3. Sinal IPCA: desvio da meta (meta = 3%; p95 histórico ≈ +4-5 pp)
    sinal_ipca = min(max(ipca_desvio_meta / 4.5, 0), 1)

    # 4. Sinal Copom: dovish = risco (sem âncora)
    sinal_copom = 1 - score_tom_copom

    # 5. Sinal USDT/Stablecoins: variação 30d (p95 ≈ +150%)
    #    Logaritmo suaviza os outliers extremos (ex: +421% em pico FTX)
    import math
    usdt_log = math.log1p(max(variacao_usdt_30d, 0)) / math.log1p(150)
    sinal_usdt = min(usdt_log, 1)

    # 6. Sinal Atividade: recessão (IBC-Br, variação; p95 negativo ≈ -0.04)
    sinal_atividade = min(max(-ibc_br_var / 0.05, 0), 1)

    indice = (
        sinal_divida    * pesos['divida']   +
        sinal_cambio    * pesos['cambio']   +
        sinal_ipca      * pesos['ipca']     +
        sinal_copom     * pesos['copom']    +
        sinal_usdt      * pesos['expectat'] +
        sinal_atividade * pesos['atividade']
    ) * 100

    return round(indice, 2)
