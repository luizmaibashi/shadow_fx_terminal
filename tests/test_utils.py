# -*- coding: utf-8 -*-
"""
tests/test_utils.py - Shadow FX Terminal
Suite de testes unitarios para o modulo central utils.py.
Execute: pytest tests/ -v
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import (
    get_semestre,
    adicionar_features_temporais,
    normalizar_min_max,
    calcular_correlacao_spearman,
    calcular_indice_risco_fiscal,
    PROJECT_ROOT, DATA_RAW, DATA_PROC,
)


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def serie_crescente():
    idx = pd.date_range("2024-01-01", periods=60, freq="D")
    return pd.Series(range(60), index=idx, dtype=float)


@pytest.fixture
def df_base():
    idx = pd.date_range("2024-01-01", periods=120, freq="D")
    return pd.DataFrame(
        {"brl_usd": np.random.uniform(4.8, 6.2, 120),
         "usdt_supply": np.random.uniform(78e9, 120e9, 120)},
        index=idx
    )


# ── get_semestre ────────────────────────────────────────────────────

class TestGetSemestre:
    def test_s1(self):
        assert get_semestre(pd.Timestamp("2024-01-01")) == "2024-S1"
        assert get_semestre(pd.Timestamp("2024-06-30")) == "2024-S1"

    def test_s2(self):
        assert get_semestre(pd.Timestamp("2024-07-01")) == "2024-S2"
        assert get_semestre(pd.Timestamp("2024-12-31")) == "2024-S2"

    def test_multiplos_anos(self):
        assert get_semestre(pd.Timestamp("2022-03-15")) == "2022-S1"
        assert get_semestre(pd.Timestamp("2025-11-01")) == "2025-S2"


# ── normalizar_min_max ──────────────────────────────────────────────

class TestNormalizarMinMax:
    def test_range_correto(self):
        s = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        r = normalizar_min_max(s)
        assert r.min() == pytest.approx(0.0)
        assert r.max() == pytest.approx(1.0)

    def test_constante_retorna_neutro(self):
        s = pd.Series([5.0, 5.0, 5.0])
        assert (normalizar_min_max(s) == 0.5).all()


# ── calcular_correlacao_spearman ────────────────────────────────────

class TestCorrelacaoSpearman:
    def test_perfeita_positiva(self, serie_crescente):
        r = calcular_correlacao_spearman(serie_crescente, serie_crescente)
        assert r["coef"] == pytest.approx(1.0)
        assert bool(r["significativo"]) is True  # scipy retorna np.True_, não bool nativo
        assert r["forca"] == "Forte"

    def test_amostra_insuficiente(self):
        s = pd.Series(range(10), dtype=float)
        r = calcular_correlacao_spearman(s, s)
        assert r["coef"] is None
        assert r["forca"] == "Insuficiente"


# ── calcular_indice_risco_fiscal ────────────────────────────────────

class TestIRF:
    """O IRF e o nucleo do projeto. Estes testes protegem a logica de negocio."""

    def test_range_invariante(self):
        """IRF SEMPRE deve estar entre 0 e 100, independente dos inputs."""
        for _ in range(200):
            irf = calcular_indice_risco_fiscal(
                np.random.uniform(0, 1),
                np.random.uniform(-5, 15),
                np.random.uniform(-3, 10)
            )
            assert 0 <= irf <= 100

    def test_cenario_alto_risco(self):
        """Copom dovish + real caindo + fuga de capital = IRF alto."""
        irf = calcular_indice_risco_fiscal(0.1, 10.0, 5.0)
        assert irf > 70, f"Alto risco esperado > 70, obtido {irf}"

    def test_cenario_baixo_risco(self):
        """Copom hawkish + real estavel + USDT estagnado = IRF baixo."""
        irf = calcular_indice_risco_fiscal(0.9, 0.0, 0.0)
        assert irf < 30, f"Baixo risco esperado < 30, obtido {irf}"

    def test_simetria_copom(self):
        """Copom mais hawkish deve sempre reduzir o IRF (ceteris paribus)."""
        irf_dovish  = calcular_indice_risco_fiscal(0.1, 5.0, 3.0)
        irf_hawkish = calcular_indice_risco_fiscal(0.9, 5.0, 3.0)
        assert irf_dovish > irf_hawkish

    def test_monotonia_cambio(self):
        """Mais desvalorizacao cambial = mais risco."""
        assert calcular_indice_risco_fiscal(0.5, 8.0, 2.0) >= \
               calcular_indice_risco_fiscal(0.5, 1.0, 2.0)

    def test_pesos_customizados(self):
        irf = calcular_indice_risco_fiscal(0.5, 5.0, 2.5,
                                           pesos={"cambio": 0.5, "usdt": 0.3, "copom": 0.2})
        assert 0 <= irf <= 100


# ── features temporais ──────────────────────────────────────────────

class TestFeaturesTemporas:
    def test_colunas_criadas(self, df_base):
        r = adicionar_features_temporais(df_base)
        for col in ["semestre", "trimestre", "ano", "mes_num"]:
            assert col in r.columns

    def test_imutavel(self, df_base):
        cols_antes = list(df_base.columns)
        adicionar_features_temporais(df_base)
        assert list(df_base.columns) == cols_antes


# ── configuracao de paths ───────────────────────────────────────────

class TestConfiguracao:
    def test_project_root_existe(self):
        assert PROJECT_ROOT.exists()

    def test_data_raw_existe(self):
        assert DATA_RAW.exists()

    def test_data_proc_existe(self):
        assert DATA_PROC.exists()


# ── calcular_irf_v2 ─────────────────────────────────────────────────

from utils import calcular_irf_v2


class TestIRFv2:
    """Testes para o IRF v2 (6 sinais calibrados com dados reais)."""

    def test_range_invariante(self):
        """IRF v2 SEMPRE deve estar entre 0 e 100, independente dos inputs."""
        for _ in range(300):
            irf = calcular_irf_v2(
                score_tom_copom   = np.random.uniform(0, 1),
                brl_adj_dxy_30d   = np.random.uniform(-10, 15),
                ipca_desvio_meta  = np.random.uniform(-2, 8),
                variacao_usdt_30d = np.random.uniform(-60, 500),
                divida_pib_var    = np.random.uniform(-0.2, 0.2),
                ibc_br_var        = np.random.uniform(-0.1, 0.1),
            )
            assert 0 <= irf <= 100, f"IRF v2 fora do range: {irf}"

    def test_cenario_alto_risco(self):
        """Dominancia fiscal + real caindo + Copom dovish = IRF v2 alto."""
        irf = calcular_irf_v2(
            score_tom_copom   = 0.1,   # Copom dovish
            brl_adj_dxy_30d   = 10.0,  # BRL caindo forte (alem do DXY)
            ipca_desvio_meta  = 5.0,   # Inflacao 5pp acima da meta
            variacao_usdt_30d = 200.0, # USDT explodindo
            divida_pib_var    = 0.15,  # Divida/PIB subindo
            ibc_br_var        = -0.08, # Recessao
        )
        assert irf > 50, f"Alto risco esperado > 50, obtido {irf}"

    def test_cenario_baixo_risco(self):
        """Dominancia fiscal controlada + real estavel + Copom hawkish = IRF v2 baixo."""
        irf = calcular_irf_v2(
            score_tom_copom   = 0.9,   # Copom hawkish
            brl_adj_dxy_30d   = 0.0,   # BRL estavel
            ipca_desvio_meta  = 0.0,   # Inflacao na meta
            variacao_usdt_30d = 0.0,   # Sem crescimento de USDT
            divida_pib_var    = 0.0,   # Divida controlada
            ibc_br_var        = 0.0,   # Atividade estavel
        )
        assert irf < 20, f"Baixo risco esperado < 20, obtido {irf}"

    def test_divida_pib_aumenta_risco(self):
        """Maior variacao da Divida/PIB deve aumentar o IRF v2."""
        base = dict(score_tom_copom=0.5, brl_adj_dxy_30d=2.0,
                    ipca_desvio_meta=1.0, variacao_usdt_30d=10.0, ibc_br_var=0.0)
        irf_baixo = calcular_irf_v2(**base, divida_pib_var=0.0)
        irf_alto  = calcular_irf_v2(**base, divida_pib_var=0.15)
        assert irf_alto > irf_baixo

    def test_simetria_copom(self):
        """Copom mais hawkish deve sempre reduzir o IRF v2."""
        base = dict(brl_adj_dxy_30d=3.0, ipca_desvio_meta=2.0,
                    variacao_usdt_30d=20.0, divida_pib_var=0.05, ibc_br_var=0.0)
        irf_dovish  = calcular_irf_v2(score_tom_copom=0.1, **base)
        irf_hawkish = calcular_irf_v2(score_tom_copom=0.9, **base)
        assert irf_dovish > irf_hawkish

    def test_consistencia_v1_v2_ordenacao(self):
        """IRF v2 e v1 devem concordar na ordenacao (cenario A > B implica ambos)."""
        from utils import calcular_indice_risco_fiscal
        # Cenario de alto risco
        v2_alto = calcular_irf_v2(0.1, 8.0, 4.0, 100.0, 0.1, -0.05)
        v2_baixo = calcular_irf_v2(0.9, 0.0, 0.0, 0.0, 0.0, 0.0)
        v1_alto  = calcular_indice_risco_fiscal(0.1, 8.0, 5.0)
        v1_baixo = calcular_indice_risco_fiscal(0.9, 0.0, 0.0)
        assert v2_alto > v2_baixo, "IRF v2: alto risco deve ser maior que baixo risco"
        assert v1_alto > v1_baixo, "IRF v1: alto risco deve ser maior que baixo risco"


# ── calcular_correlacao_parcial ─────────────────────────────────────

from utils import calcular_correlacao_parcial


class TestCorrelacaoParcial:
    """Testes para a correlacao parcial (controle de confundidor)."""

    def test_sem_confundidor_preserva_correlacao(self):
        """Controlando por variavel sem correlacao, o coef parcial deve ~= bruto."""
        np.random.seed(42)
        n = 100
        x = pd.Series(np.random.randn(n))
        y = x * 0.8 + np.random.randn(n) * 0.2
        z = pd.Series(np.random.randn(n))  # Sem relacao com x ou y
        res = calcular_correlacao_parcial(x, y, z)
        assert res["coef_parcial"] is not None
        assert abs(res["reducao_pct"]) < 20, "Reducao > 20% sem confundidor real"

    def test_com_confundidor_reduz_correlacao(self):
        """Controlando pelo confundidor real, o coef parcial deve cair."""
        np.random.seed(0)
        n = 120
        z = pd.Series(np.random.randn(n))  # Confundidor verdadeiro
        x = z * 0.9 + np.random.randn(n) * 0.1
        y = z * 0.9 + np.random.randn(n) * 0.1
        res = calcular_correlacao_parcial(x, y, z)
        assert res["reducao_pct"] is not None
        assert res["reducao_pct"] > 30, "Confundidor real deve reduzir a correlacao"

    def test_amostra_insuficiente(self):
        """Menos de 30 observacoes deve retornar None."""
        s = pd.Series(range(20), dtype=float)
        res = calcular_correlacao_parcial(s, s, s)
        assert res["coef_parcial"] is None
        assert "insuficiente" in res["interpretacao"].lower()

    def test_retorna_todas_as_chaves(self):
        """Resultado deve conter todas as chaves esperadas."""
        np.random.seed(1)
        n = 60
        x = pd.Series(np.random.randn(n))
        y = pd.Series(np.random.randn(n))
        z = pd.Series(np.random.randn(n))
        res = calcular_correlacao_parcial(x, y, z)
        for key in ["coef_bruto", "coef_parcial", "p_parcial", "reducao_pct", "interpretacao"]:
            assert key in res, f"Chave ausente: {key}"


# ── carregar_dataset_mestre ──────────────────────────────────────────

from utils import carregar_dataset_mestre


class TestDatasetMestre:
    """Testes de integracao para o dataset mestre unificado."""

    def test_carrega_sem_erro(self):
        df = carregar_dataset_mestre()
        assert df is not None
        assert len(df) > 500

    def test_colunas_obrigatorias(self):
        df = carregar_dataset_mestre()
        for col in ["brl_usd", "usdt_volume", "semestre", "trimestre", "ano"]:
            assert col in df.columns, f"Coluna obrigatoria ausente: {col}"

    def test_sem_nan_criticos(self):
        df = carregar_dataset_mestre()
        nan_brl = df["brl_usd"].isna().sum()
        nan_usdt = df["usdt_volume"].isna().sum()
        assert nan_brl == 0, f"BRL/USD tem {nan_brl} NaN"
        assert nan_usdt == 0, f"USDT volume tem {nan_usdt} NaN"

    def test_tipos_corretos(self):
        df = carregar_dataset_mestre()
        assert df["brl_usd"].dtype == float
        # pandas 2.x usa datetime64[us] em vez de datetime64[ns]
        assert hasattr(df.index, 'dtype')
        assert "datetime64" in str(df.index.dtype)

    def test_periodo_coberto(self):
        df = carregar_dataset_mestre()
        assert df.index.min().year <= 2022
        assert df.index.max().year >= 2025
