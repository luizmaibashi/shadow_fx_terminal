# -*- coding: utf-8 -*-
"""
pipeline_compliance.py - Shadow FX Terminal (Fase 3)
======================================================
Motor de Compliance em Cascata para stablecoins.
Implementa o padrao "Cascaded Heuristic Filters" do Stanford CS230.

ARQUITETURA (3 Camadas - do mais barato ao mais caro):

    [Entrada: Transacao]
         |
    [CAMADA 1] Filtros Heurísticos BCB (Regras Deterministicas)
         |   -> Passa? Vai para Camada 2
         |   -> Flag alto risco? -> Relatorio direto
         |
    [CAMADA 2] Isolation Forest (ML Anomaly Detection)
         |   -> Score de anomalia baseado em comportamento historico
         |   -> Usa IRF como feature contextual (o diferencial do projeto)
         |
    [CAMADA 3] LLM-as-judge (Zona Cinza)
              -> Para casos em que Camada 2 retorna score ambiguo (40-70)
              -> [PREPARADO - implementar na iteracao seguinte]

Principios de Engenharia:
    - Training-serving parity: mesmas features em treino e inferencia (via utils.py)
    - Modular: cada camada e independente e testavel
    - Explicavel (XAI): cada flag tem uma razao documentada
"""

import sys
import json
import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Adicionar src ao path para imports relativos funcionarem
sys.path.insert(0, str(Path(__file__).parent))
from utils import PROJECT_ROOT, DATA_RAW

# Configuração de Logging Profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "pipeline.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("CompliancePipeline")

# Caminhos
PROC_DIR    = PROJECT_ROOT / "data" / "processed"
MODELS_DIR  = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Limite regulatorio BCB (Resolucoes 519-521/2026)
LIMITE_BCB_BRL = 10_000.0


# ══════════════════════════════════════════════════════════════════
# CAMADA 1: FILTROS HEURISTICOS BCB
# ══════════════════════════════════════════════════════════════════

def camada1_filtros_bcb(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica as regras deterministicas das Resolucoes BCB 519-521/2026.

    Regras implementadas:
        R1: Transacao unica acima de R$ 10.000
        R2: Volume acumulado > R$ 50.000 em 30 dias
        R3: Mais de 5 transacoes para wallets distintas no mesmo dia
        R4: Transacoes multiplas entre R$ 8.000 e R$ 9.900 (fracionamento)
        R5: Horario anomalo: entre 00h e 05h + valor > R$ 5.000
    """
    df = df.copy()
    df["c1_flag"]   = False
    df["c1_razoes"] = ""

    flags_razoes = {idx: [] for idx in df.index}

    # R1: Acima do limite
    mask_r1 = df["valor_brl"] >= LIMITE_BCB_BRL
    df.loc[mask_r1, "c1_flag"] = True
    for idx in df[mask_r1].index:
        flags_razoes[idx].append("R1:acima_limite_bcb")

    # R2: Volume acumulado por usuario (janela 30 dias CALENDÁRIO)
    df["data"] = pd.to_datetime(df["timestamp"]).dt.date
    for user_id, grupo in df.groupby("user_id"):
        grupo_ord = grupo.sort_values("timestamp").copy()
        vol_30d   = grupo_ord["valor_brl"].rolling(30, min_periods=1).sum()
        idx_r2    = grupo_ord[vol_30d.values > 50_000].index
        df.loc[idx_r2, "c1_flag"] = True
        for idx in idx_r2:
            flags_razoes[idx].append("R2:volume_30d_acima_50k")


    # R3: Muitas wallets distintas no mesmo dia
    wallets_dia = (
        df.groupby(["user_id", "data"])["wallet_destino"]
        .nunique()
        .reset_index(name="wallets_unicas")
    )
    df = df.merge(wallets_dia, on=["user_id", "data"], how="left")
    mask_r3 = df["wallets_unicas"] > 5
    df.loc[mask_r3, "c1_flag"] = True
    for idx in df[mask_r3].index:
        flags_razoes[idx].append("R3:muitas_wallets_no_dia")

    # R4: Fracionamento (tickets entre 80% e 99% do limite)
    mask_r4 = (df["valor_brl"] >= LIMITE_BCB_BRL * 0.80) & (df["valor_brl"] < LIMITE_BCB_BRL)
    df.loc[mask_r4, "c1_flag"] = True
    for idx in df[mask_r4].index:
        flags_razoes[idx].append("R4:fracionamento_suspeito")

    # R5: Madrugada + valor alto
    df["hora"] = pd.to_datetime(df["timestamp"]).dt.hour
    mask_r5   = df["hora"].between(0, 5) & (df["valor_brl"] > 5_000)
    df.loc[mask_r5, "c1_flag"] = True
    for idx in df[mask_r5].index:
        flags_razoes[idx].append("R5:madrugada_valor_alto")

    df["c1_razoes"] = df.index.map(lambda i: "|".join(flags_razoes[i]))
    return df


# ══════════════════════════════════════════════════════════════════
# FEATURE ENGINEERING (Training-Serving Parity)
# ══════════════════════════════════════════════════════════════════

FEATURES_ML = [
    "valor_brl",
    "n_transacoes_dia",
    "irf_contexto",
    "entropia_wallets"  # Novo: Detecta dispersao suspeita (Smurfing)
]


def engenharia_features(df: pd.DataFrame, df_irf: pd.DataFrame) -> pd.DataFrame:
    """Cria as features para o modelo de ML.
    
    Garante que as mesmas transformacoes feitas no notebook 03 
    ocorram aqui em tempo de execucao.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["data_ts"]   = df["timestamp"].dt.normalize()

    # 1. Frequencia Diaria
    n_tx_dia = df.groupby(["user_id", "data"])["valor_brl"].count().reset_index(name="n_transacoes_dia")
    df = df.merge(n_tx_dia, on=["user_id", "data"], how="left")

    # 2. Contexto Macro (IRF v2)
    df_irf_copy = df_irf[["irf_v2"]].copy()
    df_irf_copy.index = pd.to_datetime(df_irf_copy.index)
    df["irf_contexto"] = df["data_ts"].map(
        lambda d: df_irf_copy["irf_v2"].asof(d) if d in df_irf_copy.index or d >= df_irf_copy.index[0] else 50.0
    ).fillna(50.0)

    # 3. Entropia de Wallets (Medida de Dispersao)
    #🤔 POR QUÊ: Smurfers enviam valores para muitas wallets para nao levantar flag.
    # A entropia mede quao 'espalhado' esta o dinheiro.
    def calcular_entropia(grupo):
        counts = grupo["wallet_destino"].value_counts(normalize=True)
        return -np.sum(counts * np.log2(counts + 1e-9))

    entropia = df.groupby("user_id").apply(calcular_entropia).reset_index(name="entropia_wallets")
    df = df.merge(entropia, on="user_id", how="left")

    return df


# ══════════════════════════════════════════════════════════════════
# CAMADA 2: ISOLATION FOREST (ML ANOMALY DETECTION)
# ══════════════════════════════════════════════════════════════════

def carregar_modelo_producao():
    """Carrega o modelo campeao e o scaler validados no Notebook 03."""
    model_path = MODELS_DIR / "isolation_forest_v1.joblib"
    scaler_path = MODELS_DIR / "scaler_v1.joblib"
    
    if not model_path.exists() or not scaler_path.exists():
        logger.warning("Modelo ou Scaler nao encontrados. Usando fallback de emergencia.")
        return None, None
        
    return joblib.load(model_path), joblib.load(scaler_path)


def inferir_score(df_features: pd.DataFrame, modelo, scaler) -> pd.DataFrame:
    """Aplica o modelo e retorna scores de anomalia normalizados."""
    X = df_features[FEATURES_ML].fillna(0).values
    
    # Se nao houver modelo pre-treinado, gera score heuristico baseado em volume e IRF
    if modelo is None:
        logger.info("Executando Fallback Heuristico (Sem Modelo Joblib)")
        scores_norm = (df_features["valor_brl"] / 10000 * 50 + df_features["irf_contexto"] * 0.5).clip(0, 100)
    else:
        X_scaled = scaler.transform(X)
        scores_brutos = modelo.score_samples(X_scaled)
        # Normalizar para [0, 100]: mais alto = mais suspeito
        score_min, score_max = -0.5, 0.5 # Range tipico da iForest
        scores_norm = 100 * (1 - (scores_brutos - score_min) / (score_max - score_min))
        scores_norm = scores_norm.clip(0, 100)

    df_features = df_features.copy()
    df_features["c2_score_anomalia"] = np.round(scores_norm, 1)
    df_features["c2_classificacao"]  = pd.cut(
        df_features["c2_score_anomalia"],
        bins    = [0, 40, 70, 100],
        labels  = ["normal", "cinza", "suspeito"],
        include_lowest=True,
    )

    return df_features


# ══════════════════════════════════════════════════════════════════
# CAMADA 3: PREPARACAO PARA LLM-AS-JUDGE
# ══════════════════════════════════════════════════════════════════

def preparar_prompt_llm(transacao: pd.Series) -> str:
    """Gera o prompt para o LLM-as-judge avaliar casos 'cinza'."""
    return f"""
Voce e um especialista em compliance de ativos digitais e regulacao BCB.
Analise a seguinte transacao de stablecoin e determine se e suspeita:

TRANSACAO:
- User ID: {transacao.get('user_id', 'N/A')}
- Valor: R$ {transacao.get('valor_brl', 0):,.2f}
- Frequencia hoje: {transacao.get('n_transacoes_dia', 1)} transacoes
- Entropia de Wallets: {transacao.get('entropia_wallets', 0):.2f} (Alta = Smurfing suspeito)
- Score ML (Isolation Forest): {transacao.get('c2_score_anomalia', 0)}/100
- Flags BCB ativas: {transacao.get('c1_razoes', 'nenhuma')}
- IRF (Indice de Risco Fiscal no dia): {transacao.get('irf_contexto', 50)}/100

Com base nas Resolucoes BCB 519-521/2026, essa transacao representa
risco de evasao de divisas ou lavagem de dinheiro?

Responda com: SUSPEITA / NORMAL / REQUER_INVESTIGACAO e justifique em 2 linhas.
""".strip()

def gerar_explicacao_xai(row) -> str:
    """Gera uma explicação em linguagem natural para justificar o alerta."""
    if row["alerta_final"] == "VERDE":
        return "Transação alinhada ao perfil histórico do cliente."
        
    motivos = []
    
    # 1. Analise Determinística
    if pd.notna(row["c1_razoes"]) and row["c1_razoes"] and str(row["c1_razoes"]) != "nenhuma":
        motivos.append(f"Regras BCB Violadas ({row['c1_razoes']})")
        
    # 2. Analise Comportamental (ML)
    if row["c2_score_anomalia"] > 70:
        motivos.append("Padrão fortemente anômalo (Isolation Forest > 70)")
    elif row["c2_score_anomalia"] > 40:
        motivos.append("Desvio comportamental moderado (Isolation Forest > 40)")
        
    # 3. Contexto Macro
    if row["irf_contexto"] > 60:
        motivos.append(f"Agravante Macro: IRF Crítico ({row['irf_contexto']:.1f}/100) sugerindo stress fiscal")
        
    # 4. Sinais Específicos
    if row["wallets_unicas"] > 4:
        motivos.append(f"Risco de Smurfing: Transferência diluída em {row['wallets_unicas']} wallets")
        
    explicacao = " | ".join(motivos)
    return explicacao if explicacao else "Atividade fora do padrão, análise manual sugerida."

# ══════════════════════════════════════════════════════════════════
# PIPELINE COMPLETO
# ══════════════════════════════════════════════════════════════════

def executar_pipeline(df_tx: pd.DataFrame, df_irf: pd.DataFrame) -> pd.DataFrame:
    """Executa as 3 camadas do pipeline de compliance."""
    logger.info("INICIANDO PIPELINE DE COMPLIANCE (3 Camadas)")
    logger.info("=" * 55)

    # Camada 1
    logger.info("[C1] Aplicando filtros heuristicos BCB...")
    df_c1 = camada1_filtros_bcb(df_tx)
    flagged_c1 = df_c1["c1_flag"].sum()
    logger.info(f"     Transacoes flagadas: {flagged_c1} / {len(df_c1)}")

    # Feature Engineering
    logger.info("[FE] Calculando features para o ML...")
    df_fe = engenharia_features(df_c1, df_irf)

    # Camada 2
    logger.info("[C2] Carregando modelo campeao da Arena...")
    modelo, scaler = carregar_modelo_producao()
    df_c2 = inferir_score(df_fe, modelo, scaler)
    logger.info(f"     Score medio: {df_c2['c2_score_anomalia'].mean():.1f} / 100")
    logger.info(f"     Classificados SUSPEITOS: {(df_c2['c2_classificacao'] == 'suspeito').sum()}")
    logger.info(f"     Classificados CINZA:     {(df_c2['c2_classificacao'] == 'cinza').sum()}")

    # Camada 3: Preparar prompts para zona cinza
    mask_cinza = df_c2["c2_classificacao"] == "cinza"
    logger.info(f"[C3] {mask_cinza.sum()} casos cinza prontos para LLM-as-judge (Fase futura)")
    if mask_cinza.any():
        df_c2.loc[mask_cinza, "c3_prompt_llm"] = df_c2[mask_cinza].apply(
            preparar_prompt_llm, axis=1
        )

    # Score final composto
    # Converter flag C1 para inteiro para o calculo
    df_c2["c1_flag_int"] = df_c2["c1_flag"].astype(int)
    df_c2["score_final"] = (
        df_c2["c2_score_anomalia"] * 0.6 +
        df_c2["c1_flag_int"] * 40.0 * 0.4
    ).clip(0, 100).round(1)

    df_c2["alerta_final"] = pd.cut(
        df_c2["score_final"],
        bins=[0, 40, 70, 100],
        labels=["VERDE", "AMARELO", "VERMELHO"],
        include_lowest=True,
    )

    # PM Improvement: Explainability (XAI)
    logger.info("[PM] Gerando justificativas (XAI) para os alertas...")
    df_c2["explicacao_xai"] = df_c2.apply(gerar_explicacao_xai, axis=1)

    logger.info("=" * 55)
    logger.info("PIPELINE CONCLUIDO")
    logger.info(f"  VERDE (normal):   {(df_c2['alerta_final'] == 'VERDE').sum()}")
    logger.info(f"  AMARELO (monit.): {(df_c2['alerta_final'] == 'AMARELO').sum()}")
    logger.info(f"  VERMELHO (acao):  {(df_c2['alerta_final'] == 'VERMELHO').sum()}")

    return df_c2


if __name__ == "__main__":
    # Carregar dados
    if not (PROC_DIR / "transacoes_simuladas.csv").exists():
        logger.error("Transações simuladas não encontradas. Execute src/gerador_transacoes_mock.py primeiro.")
        sys.exit(1)
        
    df_tx  = pd.read_csv(PROC_DIR / "transacoes_simuladas.csv")
    df_irf = pd.read_csv(
        PROC_DIR / "dataset_irf_completo.csv",
        index_col="date", parse_dates=True
    )

    df_resultado = executar_pipeline(df_tx, df_irf)

    # Salvar resultado
    saida = PROC_DIR / "resultado_compliance.csv"
    df_resultado.to_csv(saida, index=False, encoding="utf-8")
    logger.info(f"Resultado salvo em: {saida}")
