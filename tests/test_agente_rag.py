# -*- coding: utf-8 -*-
"""
tests/test_agente_rag.py - Shadow FX Terminal
Testes para o agente RAG de compliance (Camada 3).
Foco: fallback heuristico, parse de resposta, recuperacao de contexto.
Execute: pytest tests/ -v
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestFallbackHeuristico:
    """Testes para o fallback do agente RAG quando LLM esta indisponivel."""

    def test_fallback_smurfing_detectado(self):
        from agente_rag import _fallback_heuristico
        tx = {"score_ml": 85, "wallets_unicas": 12, "valor_brl": 50000,
              "user_id": "USR_SMURF", "hora": 3, "razoes": "smurfing"}
        resultado = _fallback_heuristico(tx)
        assert "SUSPEITO" in resultado
        assert "Fallback Mode" in resultado

    def test_fallback_score_intermediario(self):
        from agente_rag import _fallback_heuristico
        tx = {"score_ml": 50, "wallets_unicas": 2, "valor_brl": 5000,
              "user_id": "USR_NORMAL", "hora": 14, "razoes": ""}
        resultado = _fallback_heuristico(tx)
        assert "REQUER_INVESTIGACAO" in resultado
        assert "Fallback Mode" in resultado

    def test_fallback_score_baixo_mas_muitas_wallets(self):
        from agente_rag import _fallback_heuristico
        tx = {"score_ml": 30, "wallets_unicas": 7, "valor_brl": 50000,
              "user_id": "USR_TEST", "hora": 10, "razoes": ""}
        resultado = _fallback_heuristico(tx)
        assert "SUSPEITO" in resultado or "REQUER_INVESTIGACAO" in resultado


class TestRecuperacaoContexto:
    def test_contexto_indisponivel_sem_arquivo(self):
        """Sem arquivo de atas, deve retornar string padrao."""
        from agente_rag import recuperar_contexto_copom
        contexto = recuperar_contexto_copom(pd.Timestamp("2024-06-15"))
        assert isinstance(contexto, str)
        assert len(contexto) > 0

    def test_formato_contexto(self):
        from agente_rag import recuperar_contexto_copom
        contexto = recuperar_contexto_copom(pd.Timestamp("2024-06-15"))
        # Deve retornar ou "indisponivel" ou conter "Copom"
        assert ("indisponível" in contexto.lower() or
                "Copom" in contexto)
