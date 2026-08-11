# -*- coding: utf-8 -*-
"""
tests/test_pipeline_compliance.py - Shadow FX Terminal
Testes para o pipeline de compliance (camadas 1, 2, 3 e fallback).
Execute: pytest tests/ -v
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline_compliance import (
    camada1_filtros_bcb,
    engenharia_features,
    inferir_score,
    gerar_explicacao_xai,
    LIMITE_BCB_BRL,
)
# preparar_prompt_llm mora em agente_rag.py (logica de prompt/LLM co-localizada)
from agente_rag import preparar_prompt_llm


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def df_transacoes():
    """Dataset sintetico basico para testes."""
    np.random.seed(42)
    n = 100
    base = pd.Timestamp("2024-06-01")
    users = [f"USR_{i:03d}" for i in range(1, 6)]
    data = {
        "user_id": np.random.choice(users, n),
        "timestamp": [base + timedelta(hours=np.random.randint(0, 720), minutes=np.random.randint(0, 60)) for _ in range(n)],
        "valor_brl": np.round(np.random.uniform(500, 25000, n), 2),
        "wallet_destino": [f"wallet_{np.random.randint(1, 50)}" for _ in range(n)],
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_irf():
    """IRF sintetico diario."""
    idx = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    return pd.DataFrame({"irf_v2": np.random.uniform(20, 90, len(idx))}, index=idx)


# ── Camada 1: Filtros BCB ──────────────────────────────────────────

class TestCamada1:
    def test_colunas_criadas(self, df_transacoes):
        df = camada1_filtros_bcb(df_transacoes)
        for col in ["c1_flag", "c1_razoes", "data", "hora"]:
            assert col in df.columns, f"Coluna ausente: {col}"

    def test_flag_acima_limite(self):
        """R1: valor >= 10k deve sempre flagar."""
        df = pd.DataFrame({
            "user_id": ["USR_001"],
            "timestamp": [pd.Timestamp("2024-06-15 14:00")],
            "valor_brl": [15000.0],
            "wallet_destino": ["wallet_1"],
        })
        df = camada1_filtros_bcb(df)
        assert df["c1_flag"].iloc[0]
        assert "R1" in df["c1_razoes"].iloc[0]

    def test_fracionamento(self):
        """R4: valor entre 80-99% do limite deve flagar."""
        df = pd.DataFrame({
            "user_id": ["USR_001"],
            "timestamp": [pd.Timestamp("2024-06-15 14:00")],
            "valor_brl": [LIMITE_BCB_BRL * 0.85],
            "wallet_destino": ["wallet_1"],
        })
        df = camada1_filtros_bcb(df)
        assert df["c1_flag"].iloc[0]
        assert "R4" in df["c1_razoes"].iloc[0]

    def test_madrugada(self):
        """R5: madrugada + valor > 5k deve flagar."""
        df = pd.DataFrame({
            "user_id": ["USR_001"],
            "timestamp": [pd.Timestamp("2024-06-15 03:00")],
            "valor_brl": [7000.0],
            "wallet_destino": ["wallet_1"],
        })
        df = camada1_filtros_bcb(df)
        assert df["c1_flag"].iloc[0]

    def test_transacao_normal(self):
        """Transacao normal nao deve flagar."""
        df = pd.DataFrame({
            "user_id": ["USR_001"],
            "timestamp": [pd.Timestamp("2024-06-15 14:00")],
            "valor_brl": [1500.0],
            "wallet_destino": ["wallet_1"],
        })
        df = camada1_filtros_bcb(df)
        assert not df["c1_flag"].iloc[0]

    def test_muitas_wallets_no_dia(self):
        """R3: >5 wallets no mesmo dia deve flagar."""
        base = pd.Timestamp("2024-06-15")
        df = pd.DataFrame({
            "user_id": ["USR_001"] * 7,
            "timestamp": [base + timedelta(hours=h) for h in range(7)],
            "valor_brl": [1000.0] * 7,
            "wallet_destino": [f"wallet_{i}" for i in range(7)],
        })
        df = camada1_filtros_bcb(df)
        assert df["c1_flag"].any()

    def test_r6_timestamp_malformado_nao_quebra_lote(self):
        """R6: timestamp malformado deve flagar a linha, nao derrubar o lote inteiro."""
        df = pd.DataFrame({
            "user_id": ["USR_001", "USR_001", "USR_002"],
            "timestamp": ["2024-06-15 14:00", "data-invalida-###", "2024-06-16 03:00"],
            "valor_brl": [1500.0, 2000.0, 6000.0],
            "wallet_destino": ["w1", "w1", "w2"],
        })
        df = camada1_filtros_bcb(df)  # nao deve lancar excecao
        assert df.loc[1, "c1_flag"]
        assert "R6:timestamp_malformado" in df.loc[1, "c1_razoes"]
        # A linha valida vizinha continua avaliada normalmente (R5: madrugada)
        assert df.loc[2, "c1_flag"]
        assert "R5" in df.loc[2, "c1_razoes"]


class TestEngenhariaFeatures:
    def _preparar(self, df_transacoes, df_irf):
        """Aplica camada1 antes da engenharia (cria coluna 'data' necessaria)."""
        df = camada1_filtros_bcb(df_transacoes)
        return engenharia_features(df, df_irf)

    def test_features_criadas(self, df_transacoes, df_irf):
        df = self._preparar(df_transacoes, df_irf)
        for col in ["n_transacoes_dia", "irf_contexto", "entropia_wallets"]:
            assert col in df.columns, f"Feature ausente: {col}"

    def test_irf_contexto_dentro_range(self, df_transacoes, df_irf):
        df = self._preparar(df_transacoes, df_irf)
        assert df["irf_contexto"].between(0, 100).all()

    def test_irf_com_lag(self, df_transacoes, df_irf):
        """IRF com lag deve usar valores de dias anteriores."""
        from utils import IRF_LAG_DAYS
        df = self._preparar(df_transacoes, df_irf)
        assert "data_com_lag" in df.columns
        lag_real = (df["data_ts"] - df["data_com_lag"]).dt.days
        assert (lag_real == IRF_LAG_DAYS).all()

    def test_entropia_positiva(self, df_transacoes, df_irf):
        df = self._preparar(df_transacoes, df_irf)
        assert (df["entropia_wallets"] >= 0).all()


class TestInferirScore:
    def _preparar(self, df_transacoes, df_irf):
        df = camada1_filtros_bcb(df_transacoes)
        return engenharia_features(df, df_irf)

    def test_sem_modelo_usa_fallback(self, df_transacoes, df_irf):
        df = self._preparar(df_transacoes, df_irf)
        df = inferir_score(df, None, None)
        assert "c2_score_anomalia" in df.columns
        assert df["c2_score_anomalia"].between(0, 100).all()

    def test_classificacao_tem_todos_labels(self, df_transacoes, df_irf):
        df = self._preparar(df_transacoes, df_irf)
        df = inferir_score(df, None, None)
        labels_esperados = {"normal", "cinza", "suspeito"}
        assert labels_esperados.issuperset(df["c2_classificacao"].unique())


class TestXAI:
    def test_transacao_verde(self):
        row = pd.Series({"alerta_final": "VERDE", "c1_razoes": "", "c2_score_anomalia": 20,
                         "irf_contexto": 30, "wallets_unicas": 1})
        saida = gerar_explicacao_xai(row)
        assert "alinhada" in saida.lower()

    def test_smurfing_detectado(self):
        row = pd.Series({"alerta_final": "VERMELHO", "c1_razoes": "R3:muitas_wallets_no_dia",
                         "c2_score_anomalia": 85, "irf_contexto": 70, "wallets_unicas": 12})
        saida = gerar_explicacao_xai(row)
        assert "smurfing" in saida.lower()

    def test_irf_critico_aparece(self):
        row = pd.Series({"alerta_final": "AMARELO", "c1_razoes": "",
                         "c2_score_anomalia": 50, "irf_contexto": 80, "wallets_unicas": 2})
        saida = gerar_explicacao_xai(row)
        assert "IRF" in saida


class TestPromptLLM:
    def test_estrutura_prompt(self):
        tx = pd.Series({"user_id": "USR_001", "valor_brl": 9500.0,
                        "n_transacoes_dia": 5, "entropia_wallets": 2.5,
                        "c2_score_anomalia": 65, "c1_razoes": "R4:fracionamento",
                        "irf_contexto": 75})
        prompt = preparar_prompt_llm(tx)
        assert "USR_001" in prompt
        assert "9.500" in prompt or "9,500" in prompt  # locale-aware
        assert "BCB" in prompt
        assert "SUSPEITA" in prompt or "NORMAL" in prompt

    def test_prompt_tem_todos_campos(self):
        tx = pd.Series({"user_id": "USR_TEST", "valor_brl": 5000.0,
                        "n_transacoes_dia": 1, "entropia_wallets": 0.0,
                        "c2_score_anomalia": 10, "c1_razoes": "nenhuma",
                        "irf_contexto": 30})
        prompt = preparar_prompt_llm(tx)
        # Usar os textos exatos do template do prompt (case-sensitive)
        for campo in ["User ID", "Valor", "IRF", "BCB", "Isolation Forest"]:
            assert campo in prompt, f"Campo ausente no prompt: {campo}"


class TestFallbackPipeline:
    """Testes de integração: pipeline completo com fallback."""

    def test_pipeline_executa_sem_modelo(self, df_transacoes, df_irf):
        """Pipeline deve funcionar mesmo sem modelo treinado (fallback)."""
        from pipeline_compliance import executar_pipeline
        df = executar_pipeline(df_transacoes, df_irf)
        assert len(df) == len(df_transacoes)
        for col in ["score_final", "alerta_final", "explicacao_xai"]:
            assert col in df.columns

    def test_score_final_sempre_entre_0_100(self, df_transacoes, df_irf):
        from pipeline_compliance import executar_pipeline
        df = executar_pipeline(df_transacoes, df_irf)
        assert df["score_final"].between(0, 100).all()

    def test_alertas_sao_validos(self, df_transacoes, df_irf):
        from pipeline_compliance import executar_pipeline
        df = executar_pipeline(df_transacoes, df_irf)
        assert df["alerta_final"].isin(["VERDE", "AMARELO", "VERMELHO"]).all()

    def test_camada3_fallback_sem_llm(self, df_transacoes, df_irf):
        """Camada 3 deve usar fallback quando LLM desabilitado."""
        # O teste verifica que o pipeline nao quebra sem LLM
        from pipeline_compliance import executar_pipeline
        df = executar_pipeline(df_transacoes, df_irf)
        # Se havia casos cinza, verificar que fallback foi aplicado
        mask_cinza = df["c2_classificacao"] == "cinza"
        if mask_cinza.any():
            assert (df.loc[mask_cinza, "c3_veredito"] == "FALLBACK").all()
