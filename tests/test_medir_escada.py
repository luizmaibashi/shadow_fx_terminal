# -*- coding: utf-8 -*-
"""
tests/test_medir_escada.py - Shadow FX Terminal
Testa o IC de Wilson e trava os numeros publicados no README/PROBLEM.md
contra o snapshot versionado do demo.
Execute: pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from medir_escada import (  # noqa: E402
    CSV_PADRAO,
    carregar,
    degraus,
    irf_por_classe,
    medir_degrau,
    medir_ml_alem_da_regra,
    medir_por_usuario,
    medir_cascata,
    wilson,
)


class TestWilson:
    def test_valor_conhecido(self):
        # 1314/1327: referencia calculada a mao na revisao de 2026-10
        lo, hi = wilson(1314, 1327)
        assert round(100 * lo, 1) == 98.3
        assert round(100 * hi, 1) == 99.4

    def test_zero_sucessos_tem_teto_positivo(self):
        lo, hi = wilson(0, 100)
        assert lo == 0.0
        assert round(100 * hi, 1) == 3.7

    def test_todos_sucessos_tem_piso_abaixo_de_um(self):
        lo, hi = wilson(10, 10)
        assert hi == 1.0
        assert round(100 * lo, 1) == 72.2

    def test_intervalo_contem_a_proporcao(self):
        for k, n in [(1, 3), (7, 20), (500, 1000)]:
            lo, hi = wilson(k, n)
            assert lo <= k / n <= hi

    @pytest.mark.parametrize("k,n", [(0, 0), (-1, 10), (11, 10)])
    def test_entrada_invalida_falha(self, k, n):
        with pytest.raises(ValueError):
            wilson(k, n)


@pytest.mark.skipif(not CSV_PADRAO.exists(), reason="snapshot do demo ausente")
class TestNumerosPublicados:
    """Se o snapshot mudar, estes numeros mudam e o README precisa ser revisto."""

    @pytest.fixture(scope="class")
    def df(self):
        return carregar(CSV_PADRAO)

    def test_regra_sozinha_resolve_o_sintetico(self, df):
        m = medir_degrau(df, degraus(df)["Regra R3|R4|R5"])
        assert m["recall"] == (1314, 1315)
        assert m["precisao"] == (1314, 1327)
        assert m["fp_legitimos"] == (13, 3194)

    def test_score_final_fica_abaixo_da_regra(self, df):
        m = medir_degrau(df, degraus(df)["alerta_final != VERDE"])
        assert m["precisao"] == (654, 1460)
        assert m["recall"] == (654, 1315)

    def test_ml_nao_acrescenta_fraude_alem_da_regra(self, df):
        m = medir_ml_alem_da_regra(df)
        assert m["so o modelo acusa (score>70, sem regra): fraudes"] == (0, 225)

    def test_por_usuario(self, df):
        m = medir_por_usuario(df)
        assert m["fracionadores pegos"] == (10, 10)
        assert m["poupadores tocados"] == (0, 100)

    def test_irf_igual_entre_classes(self, df):
        _, _, p = irf_por_classe(df)
        assert p > 0.05

    def test_cascata_avaliada_fora_da_calibracao(self, df):
        limiar, tx, usr, extra = medir_cascata(df)
        assert limiar == 98.7
        assert tx == {"precisao": (693, 710), "recall": (693, 694),
                      "fp_legitimos": (17, 1597)}
        assert usr == {"precisao": (5, 12), "recall": (5, 5),
                       "fp_legitimos": (7, 57), "poupadores_tocados": (0, 50)}
        assert extra == {"zona_cinza_transacoes_C3": (688, 2291),
                         "zona_cinza_usuarios": (12, 62),
                         "fraudes_novas_por_100_cinza": (0, 688)}
