"""Ablacao por usuario e intervalos pareados, com dados sinteticos pequenos."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import medir_irf  # noqa: E402
from decisao import split_por_usuario  # noqa: E402
from gerador_v2 import DIAS, gerar_dataset_v2  # noqa: E402
from utils import FEATURES_ML  # noqa: E402


@pytest.fixture(scope="module")
def dados():
    irf = pd.Series(50 + 20 * np.sin(np.linspace(0, 6 * np.pi, len(DIAS))), index=DIAS)
    tx = gerar_dataset_v2(irf, True, n_poupadores=60, n_frac_classico=20,
                          n_frac_fora_regra=20, n_institucionais=5)
    return tx, pd.DataFrame({"irf_v2": irf})


def test_split_sem_usuarios_compartilhados(dados):
    cal, aval = split_por_usuario(dados[0], seed=42)
    assert len(cal.intersection(aval)) == 0
    assert len(cal) + len(aval) == dados[0]["user_id"].nunique()


def test_scaler_floresta_e_p_percentis_nao_veem_avaliacao():
    colunas = ["valor_brl", "irf_contexto"]
    calibracao = pd.DataFrame({"valor_brl": np.arange(10, dtype=float),
                               "irf_contexto": np.arange(10, dtype=float) * 2})
    avaliacao_alta = pd.DataFrame({"valor_brl": [10_000.0], "irf_contexto": [10_000.0]})
    avaliacao_baixa = pd.DataFrame({"valor_brl": [-10_000.0], "irf_contexto": [-10_000.0]})
    score_cal_alto, _ = medir_irf._treinar_e_pontuar(calibracao, avaliacao_alta, colunas)
    score_cal_baixo, _ = medir_irf._treinar_e_pontuar(calibracao, avaliacao_baixa, colunas)
    np.testing.assert_array_equal(score_cal_alto, score_cal_baixo)


def test_medicao_exclui_irf_no_modelo_sem_e_usa_engenharia_real(dados, monkeypatch):
    usadas = []

    def pontuar(cal, aval, colunas):
        usadas.append(list(colunas))
        assert "classe_v2" not in colunas and "z_irf_dia" not in colunas
        return np.full(len(cal), 0.5), np.full(len(aval), 0.5)

    monkeypatch.setattr(medir_irf, "_treinar_e_pontuar", pontuar)
    monkeypatch.setattr(medir_irf, "escolher_limiar_operacao", lambda *a, **k: 0.5)
    resultado = medir_irf.medir_mundo(*dados, B=5)
    assert usadas == [FEATURES_ML, [coluna for coluna in FEATURES_ML if coluna != "irf_contexto"]]
    assert resultado["n_calibracao"] + resultado["n_avaliacao"] == dados[0]["user_id"].nunique()
    assert resultado["periodo_efetivo"] == dados[0].attrs["periodo_efetivo"]
    assert resultado["diferencas"]["recall"]["ic95"] == [0.0, 0.0]


def test_estresse_usa_todos_os_dias_e_corte_identico_nos_mundos(dados, monkeypatch):
    tx_v2, irf = dados
    tx_placebo = gerar_dataset_v2(irf["irf_v2"], False, n_poupadores=60,
                                  n_frac_classico=20, n_frac_fora_regra=20,
                                  n_institucionais=5)
    monkeypatch.setattr(medir_irf, "_treinar_e_pontuar",
                        lambda cal, aval, cols: (np.full(len(cal), 0.5), np.full(len(aval), 0.5)))
    monkeypatch.setattr(medir_irf, "escolher_limiar_operacao", lambda *a, **k: 0.5)
    v2 = medir_irf.medir_mundo(tx_v2, irf, B=2)
    placebo = medir_irf.medir_mundo(tx_placebo, irf, B=2)
    assert v2["limiar_irf_estresse"] == placebo["limiar_irf_estresse"]
    assert v2["n_dias_estresse"] == placebo["n_dias_estresse"]
    assert v2["periodo_efetivo"] == placebo["periodo_efetivo"]
    apenas_uma_compra = tx_v2.iloc[:1].copy()
    apenas_uma_compra.attrs = tx_v2.attrs.copy()
    assert medir_irf._periodo_e_estresse(apenas_uma_compra, irf) == medir_irf._periodo_e_estresse(tx_v2, irf)


def test_limiar_none_falha_explicitamente(dados, monkeypatch):
    monkeypatch.setattr(medir_irf, "_treinar_e_pontuar",
                        lambda cal, aval, cols: (np.full(len(cal), 0.5), np.full(len(aval), 0.5)))
    monkeypatch.setattr(medir_irf, "escolher_limiar_operacao", lambda *a, **k: None)
    with pytest.raises(ValueError, match="nenhum limiar operacional"):
        medir_irf.medir_mundo(*dados, B=2)


def test_bootstrap_pareado_mesma_amostra_e_contagem():
    usuarios = pd.DataFrame({
        "classe_v2": ["poupador"] * 4 + ["frac_classico"] * 3 + ["frac_fora_regra"] * 3,
        "fraude": [False] * 4 + [True] * 6,
        "poupador": [True] * 4 + [False] * 6,
        "tem_alto": [True] * 10,
        "alerta_com_irf": [True, False, False, False, True, False, True, False, True, False],
        "alerta_sem_irf": [True, False, False, False, True, False, True, False, True, False],
        "alerta_alto_com_irf": [True, False, False, False, False, False, False, False, False, False],
        "alerta_alto_sem_irf": [True, False, False, False, False, False, False, False, False, False],
    }, index=[f"u{i}" for i in range(10)])
    primeiro = medir_irf.bootstrap_pareado(usuarios, B=100, seed=17)
    segundo = medir_irf.bootstrap_pareado(usuarios, B=100, seed=17)
    assert primeiro == segundo
    assert all(valor["ponto"] == 0 and valor["ic95"] == [0, 0] for valor in primeiro.values())
    rng = np.random.default_rng(17)
    grupos = [grupo.index.to_numpy() for _, grupo in usuarios.groupby("classe_v2", sort=True)]
    ids = np.concatenate([rng.choice(grupo, size=len(grupo), replace=True) for grupo in grupos])
    assert len(ids) == len(usuarios)
    assert pd.Series(ids).value_counts().sum() == len(usuarios)


@pytest.mark.parametrize("v2_recall,v2_fp,esperado", [
    ([0.02, 0.3], [-0.05, 0.01], (True, True, True)),
    ([-0.01, 0.3], [-0.05, 0.01], (True, False, True)),
    ([0.02, 0.3], [-0.05, 0.02], (True, True, False)),
])
def test_condicoes_fabricadas(v2_recall, v2_fp, esperado):
    placebo = {"diferencas": {"recall": {"ic95": [-0.1, 0.1]}}}
    v2 = {"diferencas": {"recall": {"ic95": v2_recall},
                          "fp_estresse": {"ic95": v2_fp}}}
    condicoes = medir_irf.avaliar_condicoes(v2, placebo)
    assert tuple(condicoes[chave]["passa"] for chave in "ABC") == esperado
    assert condicoes["B"]["limite_inferior_recall_v2"] == v2_recall[0]
    assert condicoes["C"]["limite_superior_fp_estresse_v2"] == v2_fp[1]
