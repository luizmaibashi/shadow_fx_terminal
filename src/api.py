# -*- coding: utf-8 -*-
"""
src/api.py - Shadow FX Terminal
=================================
Backend FastAPI desacoplado do frontend.
Protocolo do Manual Operacional: Backend (FastAPI) independente do Frontend (Streamlit).

Endpoints:
    GET  /irf/atual       - IRF do dia atual (ou mais recente disponivel)
    GET  /irf/historico   - Serie historica completa do IRF
    POST /compliance/score - Pontua uma transacao individual
    GET  /compliance/top-alertas - Retorna as transacoes com maior score

Execute: uvicorn src.api:app --reload --port 8000
"""

import sys
import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ShadowFX-API")

# Adicionar src ao path para imports relativos funcionarem
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    PROJECT_ROOT, DATA_PROC, REPORTS_DIR, FEATURES_ML,
    calcular_indice_risco_fiscal,
    calcular_irf_v2,
)

MODELS_DIR = PROJECT_ROOT / "models"

# ── App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Shadow FX Terminal API",
    description=(
        "Motor de Compliance e Monitoramento de Risco Fiscal para Stablecoins. "
        "Alinhado com as Resoluções BCB nº 519, 520 e 521 (2026). "
        "v2: IRF recalculado com dados reais (BCB, yfinance, Google Trends BR)."
    ),
    version="2.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"], # Restrito ao Dashboard local por padrao
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Middleware de Segurança (API Key) ────────────────────────────────
from fastapi import Request
from fastapi.responses import JSONResponse
import os

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY_INTERNA")
if not API_KEY:
    logger.warning("API_KEY_INTERNA nao definida. Endpoints protegidos estao desabilitados.")
    logger.warning("Crie um arquivo .env com API_KEY_INTERNA=seu-valor ou defina a variavel de ambiente.")

@app.middleware("http")
async def verificar_api_key(request: Request, call_next):
    # Pular verificacao para docs, raiz e se API_KEY nao foi configurada
    if not API_KEY or request.url.path in ["/docs", "/openapi.json", "/"]:
        return await call_next(request)
    
    api_key_header = request.headers.get(API_KEY_NAME)
    if api_key_header != API_KEY:
        return JSONResponse(
            status_code=403,
            content={"detail": "Acesso negado: API Key invalida ou ausente."}
        )
    return await call_next(request)


# ── Carregamento de dados em memória (startup) ───────────────────────

_df_irf: Optional[pd.DataFrame] = None
_df_compliance: Optional[pd.DataFrame] = None
_modelo = None
_scaler = None
_calibracao: Optional[dict] = None


def _carregar_dados():
    global _df_irf, _df_compliance, _modelo, _scaler, _calibracao

    irf_path = DATA_PROC / "dataset_irf_completo.csv"
    compliance_path = DATA_PROC / "resultado_compliance.csv"
    modelo_path = MODELS_DIR / "isolation_forest_v1.joblib"
    scaler_path = MODELS_DIR / "scaler_v1.joblib"

    logger.info("Carregando dados e modelos para memória...")
    
    if irf_path.exists():
        _df_irf = pd.read_csv(irf_path, index_col="date", parse_dates=True)
        logger.info(f"     IRF carregado: {len(_df_irf)} registros.")
    else:
        logger.warning(f"     Arquivo IRF nao encontrado em: {irf_path}")

    if compliance_path.exists():
        _df_compliance = pd.read_csv(compliance_path, parse_dates=["timestamp"])
        logger.info(f"     Compliance carregado: {len(_df_compliance)} transacoes.")
    else:
        logger.warning(f"     Arquivo Compliance nao encontrado em: {compliance_path}")

    if modelo_path.exists() and scaler_path.exists():
        _modelo = joblib.load(modelo_path)
        _scaler = joblib.load(scaler_path)
        logger.info("     Modelo ML e Scaler carregados com sucesso.")

        from pipeline_compliance import carregar_calibracao_score
        _calibracao = carregar_calibracao_score()
    else:
        logger.warning("     Modelo ML ou Scaler nao encontrados em models/. Execute o pipeline primeiro.")


_carregar_dados()


# ── Schemas ───────────────────────────────────────────────────────────

class TransacaoInput(BaseModel):
    user_id: str = Field(example="USR_001")
    valor_brl: float = Field(gt=0, example=9500.0)
    n_transacoes_dia: int = Field(ge=1, example=8)
    irf_contexto: float = Field(ge=0, le=100, example=75.0)
    entropia_wallets: float = Field(ge=0, le=5, example=3.8)
    c1_flag_int: int = Field(ge=0, le=1, example=1)
    hora: int = Field(ge=0, le=23, example=2)
    wallets_unicas: int = Field(ge=1, example=3)


class IRFAtualResponse(BaseModel):
    data: str
    irf: float          # IRF v1 (compatibilidade)
    irf_v2: float       # IRF v2 (6 sinais reais calibrados)
    classificacao: str
    sinal_cambio_30d: float
    sinal_usdt_30d: float
    sinal_copom: float
    sinal_divida_pib: Optional[float] = None
    sinal_brl_adj_dxy: Optional[float] = None


class ScoreResponse(BaseModel):
    user_id: str
    score_ml: float
    alerta: str
    razao_principal: str
    explicacao_xai: Optional[str] = None
    prompt_llm: Optional[str]
    rascunho_coaf: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────

def _classificar_irf(irf: float) -> str:
    if irf >= 70:
        return "ALTO"
    elif irf >= 40:
        return "MODERADO"
    return "BAIXO"


# FEATURES_ML importado de utils.py (fonte unica)


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/", tags=["Status"])
def raiz():
    return {
        "projeto": "Shadow FX Terminal",
        "versao": "2.0.0",
        "status": "online",
        "dados_carregados": _df_irf is not None,
        "irf_v2_disponivel": _df_irf is not None and "irf_v2" in _df_irf.columns,
        "fonte_dados": "real (yfinance + BCB + Google Trends BR)",
    }


@app.get("/irf/atual", response_model=IRFAtualResponse, tags=["IRF"])
def irf_atual():
    """Retorna o Índice de Risco Fiscal do dia mais recente disponível."""
    if _df_irf is None:
        raise HTTPException(status_code=503, detail="Dados do IRF não carregados. Execute o pipeline primeiro.")

    ultima = _df_irf.iloc[-1]
    irf_v1 = round(float(ultima.get("irf", 0)), 1)
    irf_v2_val = round(float(ultima.get("irf_v2", irf_v1)), 1)
    return IRFAtualResponse(
        data=str(_df_irf.index[-1].date()),
        irf=irf_v1,
        irf_v2=irf_v2_val,
        classificacao=_classificar_irf(irf_v2_val),  # usa v2 para classificacao
        sinal_cambio_30d=round(float(ultima.get("variacao_cambio_30d", 0)), 2),
        sinal_usdt_30d=round(float(ultima.get("variacao_usdt_30d", 0)), 2),
        sinal_copom=round(float(ultima.get("score_copom", 0.5)), 3),
        sinal_divida_pib=round(float(ultima.get("divida_pib_var", 0) or 0), 4),
        sinal_brl_adj_dxy=round(float(ultima.get("brl_adj_dxy_30d", 0) or 0), 2),
    )


@app.get("/irf/historico", tags=["IRF"])
def irf_historico(limite: int = 365):
    """Retorna a série histórica do IRF (padrão: últimos 365 dias)."""
    if _df_irf is None:
        raise HTTPException(status_code=503, detail="Dados do IRF não carregados.")

    # Incluir irf_v2 se disponivel no dataset
    cols_irf = [c for c in ["irf", "irf_v2", "irf_v2_mm7d"] if c in _df_irf.columns]
    df = _df_irf.tail(limite)[cols_irf].copy()
    return {
        "total_registros": len(df),
        "inicio": str(df.index[0].date()),
        "fim": str(df.index[-1].date()),
        "irf_medio": round(df["irf"].mean(), 1),
        "irf_v2_medio": round(df["irf_v2"].mean(), 1) if "irf_v2" in df else None,
        "irf_max": round(df["irf"].max(), 1),
        "serie": df.reset_index().rename(columns={"date": "data"}).to_dict(orient="records"),
    }


@app.post("/compliance/score", response_model=ScoreResponse, tags=["Compliance"])
def score_transacao(tx: TransacaoInput):
    """
    Pontua uma transação individual pelo pipeline de compliance.
    Retorna score de 0-100 e classificação de alerta (VERDE/AMARELO/VERMELHO).
    """
    if _modelo is None or _scaler is None:
        raise HTTPException(status_code=503, detail="Modelo não carregado. Execute o pipeline de compliance primeiro.")

    features = np.array([[
        tx.valor_brl, tx.n_transacoes_dia, tx.irf_contexto, tx.entropia_wallets
    ]])

    from pipeline_compliance import (
        normalizar_score_anomalia, carregar_calibracao_score,
        gerar_explicacao_xai, preparar_prompt_llm, LIMITE_BCB_BRL,
    )

    features_scaled = _scaler.transform(features)
    score_bruto = _modelo.score_samples(features_scaled)[0]
    calibracao = _calibracao if _calibracao else carregar_calibracao_score()
    score_norm = round(float(normalizar_score_anomalia(score_bruto, calibracao)), 1)

    # Score final composto (C1 + ML)
    score_final = round(score_norm * 0.6 + tx.c1_flag_int * 40.0 * 0.4, 1)
    score_final = max(0.0, min(100.0, score_final))

    if score_final >= 70:
        alerta = "VERMELHO"
    elif score_final >= 40:
        alerta = "AMARELO"
    else:
        alerta = "VERDE"

    # Criar um dict simulando a linha (Series)
    row_dict = {
        "alerta_final": alerta,
        "c1_razoes": tx.c1_flag_int, # simplificação
        "c2_score_anomalia": score_norm,
        "irf_contexto": tx.irf_contexto,
        "wallets_unicas": tx.wallets_unicas,
        "user_id": tx.user_id,
        "valor_brl": tx.valor_brl,
        "n_transacoes_dia": tx.n_transacoes_dia,
        "entropia_wallets": tx.entropia_wallets,
    }

    # Mapear c1_flag_int para razao texto para o XAI.
    # Replica as regras de camada1_filtros_bcb() que dao pra checar com o payload
    # desta transacao isolada (R1, R3, R4, R5). R2 (volume 30d) exige historico
    # do usuario que a API nao tem sem persistencia (ver ADR-0001) — nesse caso
    # cai no fallback generico, e o texto fica menos especifico que o do pipeline batch.
    if tx.c1_flag_int == 1:
        motivos_c1 = []
        if tx.valor_brl >= LIMITE_BCB_BRL:
            motivos_c1.append("R1: valor acima do limite (R$ 10k)")
        if tx.wallets_unicas > 5:
            motivos_c1.append("R3: mais de 5 wallets distintas no dia")
        if LIMITE_BCB_BRL * 0.80 <= tx.valor_brl < LIMITE_BCB_BRL:
            motivos_c1.append("R4: fracionamento suspeito (80-99% do limite)")
        if tx.hora <= 5 and tx.valor_brl > 5000:
            motivos_c1.append("R5: alto valor na madrugada")
        row_dict["c1_razoes"] = " | ".join(motivos_c1) if motivos_c1 else (
            "Regra determinística violada (possível R2: volume 30d — "
            "não verificável sem histórico do usuário)"
        )
    else:
        row_dict["c1_razoes"] = "nenhuma"

    transacao_series = pd.Series(row_dict)
    explicacao = gerar_explicacao_xai(transacao_series)

    # Razão principal legada (para compatibilidade UI)
    razao = explicacao.split(" | ")[0]

    # Prompt para LLM-as-judge (zona cinza) — mesma função do pipeline offline
    prompt_llm = None
    if alerta == "AMARELO":
        prompt_llm = preparar_prompt_llm(transacao_series)

    # Ação PM: Rascunho COAF Automático (para casos suspeitos)
    rascunho_coaf = None
    if alerta in ["AMARELO", "VERMELHO"]:
        rascunho_coaf = (
            f"RELATÓRIO DE ATIVIDADE SUSPEITA (RAS) - RASCUNHO\n"
            f"--------------------------------------------------\n"
            f"ID USUÁRIO: {tx.user_id}\n"
            f"DATA DO ALERTA: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"RISCO DETECTADO: NÍVEL {alerta}\n\n"
            f"DESCRIÇÃO DA OPERAÇÃO:\n"
            f"Transferência de R$ {tx.valor_brl:,.2f} fragmentada em {tx.wallets_unicas} carteiras de destino.\n"
            f"Horário da operação: {tx.hora}h.\n\n"
            f"JUSTIFICATIVA DO MOTOR MLOPS (XAI):\n"
            f"{explicacao}\n\n"
            f"AVALIAÇÃO DE CONTEXTO MACROECONÔMICO:\n"
            f"Índice de Risco Fiscal (IRF) no momento: {tx.irf_contexto}/100.\n"
            f"O sistema indica desvio padrão comportamental com score anômalo de {score_norm}/100."
        )

    return ScoreResponse(
        user_id=tx.user_id,
        score_ml=score_final,
        alerta=alerta,
        razao_principal=razao,
        explicacao_xai=explicacao,
        prompt_llm=prompt_llm,
        rascunho_coaf=rascunho_coaf
    )


@app.get("/compliance/top-alertas", tags=["Compliance"])
def top_alertas(limite: int = 20, nivel: str = "VERMELHO"):
    """Retorna as transações com maior risco do dataset processado."""
    if _df_compliance is None:
        raise HTTPException(status_code=503, detail="Dados de compliance não carregados.")

    df = _df_compliance[_df_compliance["alerta_final"] == nivel]
    df = df.sort_values("score_final", ascending=False).head(limite)

    cols = ["user_id", "tipo_usuario", "valor_brl", "hora",
            "wallets_unicas", "irf_contexto", "c1_razoes",
            "c2_score_anomalia", "score_final", "alerta_final"]
    cols_existentes = [c for c in cols if c in df.columns]

    return {
        "nivel": nivel,
        "total": len(df),
        "transacoes": df[cols_existentes].to_dict(orient="records"),
    }


@app.get("/compliance/resumo", tags=["Compliance"])
def resumo_compliance():
    """Dashboard summary: distribuição de alertas e métricas gerais."""
    if _df_compliance is None:
        raise HTTPException(status_code=503, detail="Dados de compliance não carregados.")

    contagem = _df_compliance["alerta_final"].value_counts().to_dict()
    return {
        "total_transacoes": len(_df_compliance),
        "valor_total_brl": round(float(_df_compliance["valor_brl"].sum()), 2),
        "alertas": {
            "VERDE":    int(contagem.get("VERDE", 0)),
            "AMARELO":  int(contagem.get("AMARELO", 0)),
            "VERMELHO": int(contagem.get("VERMELHO", 0)),
        },
        "score_medio": round(float(_df_compliance["score_final"].mean()), 1),
    }
