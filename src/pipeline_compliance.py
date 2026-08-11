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

import os
import sys
import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Adicionar src ao path para imports relativos funcionarem
sys.path.insert(0, str(Path(__file__).parent))
from utils import PROJECT_ROOT, FEATURES_ML, IRF_LAG_DAYS

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

    # R2: Volume acumulado por usuario (janela 30 dias CALENDARIO, nao 30 transacoes)
    df["data"] = pd.to_datetime(df["timestamp"]).dt.date
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for user_id, grupo in df.groupby("user_id"):
        grupo_ord = grupo.sort_values("timestamp")
        vol_30d = grupo_ord.set_index("timestamp")["valor_brl"].rolling("30D", min_periods=1).sum()
        idx_r2 = grupo_ord.index[vol_30d.values > 50_000]
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
# NOTA: FEATURES_ML esta centralizado em utils.py — unico ponto de verdade.


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

    # 2. Contexto Macro (IRF v2 com lag anti-leakage)
    # IRF_LAG_DAYS: macrovariaveis sao publicadas com atraso (IPCA ~15d, Divida/PIB ~30d).
    # Usar IRF[t] no dia exato incluiria info futura — deslocamos para tras.
    df_irf_copy = df_irf[["irf_v2"]].copy()
    df_irf_copy.index = pd.to_datetime(df_irf_copy.index)
    df["data_com_lag"] = df["data_ts"] - pd.Timedelta(days=IRF_LAG_DAYS)
    df["irf_contexto"] = df["data_com_lag"].map(
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


def carregar_calibracao_score() -> dict:
    """Carrega o range (p1/p99) do score_samples() calibrado no treino (treinar_modelo.py).

    Sem isso, normalizar por um range fixo assumido "na mao" desalinha do range
    real do modelo/dados treinados e satura o score.
    """
    calib_path = MODELS_DIR / "score_calibracao_v1.joblib"
    if not calib_path.exists():
        logger.warning(
            "Calibração de score não encontrada (rode treinar_modelo.py). "
            "Usando range genérico de fallback -0.5/0.5."
        )
        return {"score_min": -0.5, "score_max": 0.5}
    return joblib.load(calib_path)


def normalizar_score_anomalia(scores_brutos, calibracao: dict):
    """Normaliza score_samples() do Isolation Forest para [0, 100] (mais alto = mais suspeito).

    Única implementação — usada tanto no pipeline offline quanto na API online,
    para não divergir a calibração entre os dois (training-serving parity).
    """
    score_min, score_max = calibracao["score_min"], calibracao["score_max"]
    scores_norm = 100 * (1 - (scores_brutos - score_min) / (score_max - score_min))
    return np.clip(scores_norm, 0, 100)


def inferir_score(df_features: pd.DataFrame, modelo, scaler, calibracao: dict = None) -> pd.DataFrame:
    """Aplica o modelo e retorna scores de anomalia normalizados."""
    X = df_features[FEATURES_ML].fillna(0).values

    # Se nao houver modelo pre-treinado, gera score heuristico baseado em volume e IRF
    if modelo is None:
        logger.info("Executando Fallback Heuristico (Sem Modelo Joblib)")
        scores_norm = (df_features["valor_brl"] / 10000 * 50 + df_features["irf_contexto"] * 0.5).clip(0, 100)
    else:
        X_scaled = scaler.transform(X)
        scores_brutos = modelo.score_samples(X_scaled)
        calibracao = calibracao or carregar_calibracao_score()
        scores_norm = normalizar_score_anomalia(scores_brutos, calibracao)

    df_features = df_features.copy()
    df_features["c2_score_anomalia"] = np.round(scores_norm, 1)
    df_features["c2_classificacao"]  = pd.cut(
        df_features["c2_score_anomalia"],
        bins    = [0, 40, 70, 100],
        labels  = ["normal", "cinza", "suspeito"],
        include_lowest=True,
    )

    return df_features


# Flag para ativar/desativar chamada LLM real (evita dependencia de API no desenvolvimento)
LLM_JUDGE_ENABLED = os.getenv("LLM_JUDGE_ENABLED", "false").lower() == "true"

# ══════════════════════════════════════════════════════════════════
# CAMADA 3: LLM-AS-JUDGE (Julgamento qualitativo)
# ══════════════════════════════════════════════════════════════════

def executar_camada3_llm(df_cinza: pd.DataFrame) -> pd.DataFrame:
    """Executa o LLM-as-judge nos casos cinza, integrando o agente RAG.

    Requer LLM_JUDGE_ENABLED=true e GEMINI_API_KEY no .env.
    Se desabilitado ou sem API key, usa fallback heuristico.
    """
    try:
        from agente_rag import julgar_transacao_llm
    except ImportError:
        logger.warning("[C3] agente_rag.py nao encontrado. Usando fallback heuristico.")
        df_cinza["c3_veredito"] = "FALLBACK"
        df_cinza["c3_justificativa"] = "LLM nao disponivel (agente_rag.py ausente)"
        df_cinza["c3_rascunho_coaf"] = ""
        return df_cinza

    if not LLM_JUDGE_ENABLED:
        logger.info("[C3] LLM-as-judge desabilitado (LLM_JUDGE_ENABLED=false). Usando fallback.")
        df_cinza["c3_veredito"] = "FALLBACK"
        df_cinza["c3_justificativa"] = "Julgamento LLM desabilitado — analise manual requerida"
        df_cinza["c3_rascunho_coaf"] = ""
        return df_cinza

    logger.info(f"[C3] Executando LLM-as-judge em {len(df_cinza)} casos cinza...")
    for idx, row in df_cinza.iterrows():
        tx_dict = {
            "user_id": row.get("user_id", "N/A"),
            "data": str(row.get("data_ts", "")),
            "valor_brl": float(row.get("valor_brl", 0)),
            "hora": int(row.get("hora", 0)),
            "wallets_unicas": int(row.get("wallets_unicas", 1)),
            "score_ml": float(row.get("c2_score_anomalia", 0)),
            "razoes": str(row.get("c1_razoes", "")),
        }
        resultado = julgar_transacao_llm(tx_dict)
        df_cinza.at[idx, "c3_resposta_llm_bruta"] = resultado

        # Parse estruturado do resultado
        veredito = "REQUER_INVESTIGACAO"
        justificativa = ""
        rascunho = ""
        for linha in resultado.split("\n"):
            linha_stripped = linha.strip()
            if linha_stripped.startswith("VEREDITO:"):
                veredito = linha_stripped.replace("VEREDITO:", "").strip()
            elif linha_stripped.startswith("JUSTIFICATIVA:"):
                justificativa = linha_stripped.replace("JUSTIFICATIVA:", "").strip()
            elif linha_stripped.startswith("RASCUNHO COAF:"):
                rascunho = linha_stripped.replace("RASCUNHO COAF:", "").strip()

        df_cinza.at[idx, "c3_veredito"] = veredito
        df_cinza.at[idx, "c3_justificativa"] = justificativa
        df_cinza.at[idx, "c3_rascunho_coaf"] = rascunho

    logger.info(f"[C3] LLM-as-judge concluido. Vereditos: {df_cinza['c3_veredito'].value_counts().to_dict()}")
    return df_cinza

# preparar_prompt_llm() mora em agente_rag.py — e logica de prompt de LLM,
# co-localizada com o resto da logica de LLM/RAG (julgar_transacao_llm,
# recuperar_contexto_copom), nao mais duplicada/definida aqui.

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

    # Camada 3: Julgamento qualitativo via LLM-as-Judge
    # (com fallback heuristico se LLM desabilitado ou API indisponivel)
    mask_cinza = df_c2["c2_classificacao"] == "cinza"
    if mask_cinza.any():
        from agente_rag import preparar_prompt_llm
        df_c2.loc[mask_cinza, "c3_prompt_llm"] = df_c2[mask_cinza].apply(
            preparar_prompt_llm, axis=1
        )
        df_c2.loc[mask_cinza, "c3_resposta_llm_bruta"] = ""
        df_c2.loc[mask_cinza, "c3_veredito"] = "FALLBACK"
        df_c2.loc[mask_cinza, "c3_justificativa"] = "Aguardando julgamento LLM"
        df_c2.loc[mask_cinza, "c3_rascunho_coaf"] = ""

        df_cinza = executar_camada3_llm(df_c2.loc[mask_cinza].copy())
        for col in ["c3_resposta_llm_bruta", "c3_veredito", "c3_justificativa", "c3_rascunho_coaf"]:
            df_c2.loc[mask_cinza, col] = df_cinza[col]
        logger.info(f"[C3] {mask_cinza.sum()} casos cinza processados via LLM-as-judge.")
    else:
        logger.info("[C3] Nenhum caso cinza — Camada 3 nao acionada.")

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
