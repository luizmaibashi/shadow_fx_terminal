"""Contrato do mundo v2 e do placebo, sem dados reais ou rede."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gerador_v2 import DIAS, gerar_dataset_v2, irf_calendario_diario  # noqa: E402
from macro_disponibilidade import OFFSET_DISPONIBILIDADE_DIAS, derivar_mensais, mensal_de_diaria  # noqa: E402
from pipeline_compliance import camada1_filtros_bcb  # noqa: E402
from utils import FEATURES_ML  # noqa: E402


@pytest.fixture(scope="module")
def onda():
    return pd.Series(np.sin(np.linspace(0, 6 * np.pi, len(DIAS))), index=DIAS)


@pytest.fixture(scope="module")
def mundos(onda):
    parametros = dict(n_poupadores=60, n_frac_classico=20,
                      n_frac_fora_regra=20, n_institucionais=5)
    return (gerar_dataset_v2(onda, True, **parametros),
            gerar_dataset_v2(onda, False, **parametros))


def test_offsets_meta_e_compatibilidade_csv_antigo(caplog):
    assert OFFSET_DISPONIBILIDADE_DIAS["ibc_br"] == 90
    assert OFFSET_DISPONIBILIDADE_DIAS["divida_bruta_pib"] == 70
    assert OFFSET_DISPONIBILIDADE_DIAS["meta_inflacao"] == 0
    indice = pd.date_range("2022-01-01", periods=12, freq="MS")
    mensal = pd.DataFrame({"ipca_mensal": [5 / 12] * 12,
                           "meta_inflacao": [3.5] * 12}, index=indice)
    derivado = derivar_mensais(mensal)
    assert derivado.loc["2022-12-01", "desvio_meta_ipca"] == pytest.approx(1.5)
    antigo = mensal.rename(columns={"meta_inflacao": "expectativa_ipca_12m"})
    assert "meta_inflacao" in mensal_de_diaria(antigo)
    sem_meta = derivar_mensais(mensal.drop(columns="meta_inflacao"))
    assert sem_meta.loc["2022-12-01", "desvio_meta_ipca"] == pytest.approx(2.0)
    assert "meta_inflacao ausente" in caplog.text


def test_determinismo_e_rng_global(onda):
    parametros = dict(n_poupadores=5, n_frac_classico=2, n_frac_fora_regra=2,
                      n_institucionais=1)
    estado_antes = np.random.get_state()
    primeiro = gerar_dataset_v2(onda, True, seed=7, **parametros)
    segundo = gerar_dataset_v2(onda, True, seed=7, **parametros)
    terceiro = gerar_dataset_v2(onda, True, seed=8, **parametros)
    estado_depois = np.random.get_state()
    pd.testing.assert_frame_equal(primeiro, segundo)
    assert not primeiro.equals(terceiro)
    assert all(np.array_equal(a, b) for a, b in zip(estado_antes, estado_depois))


def test_acoplamento_e_placebo(mundos):
    acoplado, placebo = mundos
    ordem = ["timestamp", "user_id", "valor_brl", "wallet_destino"]
    sem_poup_v2 = (acoplado.loc[acoplado["classe_v2"] != "poupador"]
                   .sort_values(ordem).reset_index(drop=True))
    sem_poup_plac = (placebo.loc[placebo["classe_v2"] != "poupador"]
                     .sort_values(ordem).reset_index(drop=True))
    pd.testing.assert_frame_equal(sem_poup_v2, sem_poup_plac)
    for df, acoplado_flag in ((acoplado, True), (placebo, False)):
        for classe in ("poupador", "frac_classico", "frac_fora_regra"):
            parte = df.loc[df["classe_v2"] == classe]
            contagem = parte.groupby("data").size().reindex(DIAS.date, fill_value=0)
            rho = spearmanr(np.sin(np.linspace(0, 6 * np.pi, len(DIAS))), contagem).statistic
            if classe == "poupador" and acoplado_flag:
                assert rho > 0.3
            else:
                assert abs(rho) < 0.1
    poup_v2 = acoplado.loc[acoplado["classe_v2"] == "poupador"]
    poup_plac = placebo.loc[placebo["classe_v2"] == "poupador"]
    assert abs(len(poup_plac) / len(poup_v2) - 1) <= 0.05
    assert abs(poup_plac["valor_brl"].sum() / poup_v2["valor_brl"].sum() - 1) <= 0.05


def test_fora_da_regra_e_colunas_sem_vazamento(mundos):
    df = mundos[0]
    assert {"user_id", "tipo_usuario", "timestamp", "valor_brl", "wallet_destino",
            "hora", "eh_fracionamento", "data", "acima_limite_bcb", "madrugada",
            "classe_v2", "z_irf_dia"} == set(df.columns)
    assert "z_irf_dia" not in FEATURES_ML and "classe_v2" not in FEATURES_ML
    regras = camada1_filtros_bcb(df)
    motivo = regras["c1_razoes"].str.contains("R3:|R4:|R5:")
    fora = regras["classe_v2"] == "frac_fora_regra"
    classico = regras["classe_v2"] == "frac_classico"
    assert (~motivo[fora]).mean() >= 0.8
    assert motivo[classico].mean() >= 0.8
    por_dia = regras.loc[fora].groupby(["user_id", "data"])["wallet_destino"]
    assert por_dia.size().between(3, 6).all()
    assert por_dia.nunique().between(2, 4).all()


def test_irf_com_dia_ausente_falha(onda):
    curto = onda.drop(pd.date_range("2024-06-15", "2024-06-18"))
    assert pd.notna(irf_calendario_diario(curto, DIAS.min(), DIAS.max()).loc["2024-06-18"])
    longo = onda.drop(pd.date_range("2024-06-15", "2024-06-19"))
    with pytest.raises(ValueError, match="buraco maior"):
        gerar_dataset_v2(longo, True,
                         n_poupadores=1, n_frac_classico=0,
                         n_frac_fora_regra=0, n_institucionais=0)


def test_calendario_irf_ffill_sem_bfill_e_sem_extrapolar_fim():
    sexta = pd.Timestamp("2024-01-05")
    segunda = pd.Timestamp("2024-01-08")
    uteis = pd.Series([10.0, 20.0], index=pd.DatetimeIndex([sexta, segunda]))
    diario = irf_calendario_diario(uteis, pd.Timestamp("2024-01-04"),
                                  pd.Timestamp("2024-01-10"))
    assert pd.isna(diario.loc["2024-01-04"])
    assert diario.loc["2024-01-06"] == diario.loc["2024-01-07"] == 10.0
    assert diario.index.max() == segunda
    feriado = pd.Series([10.0, 20.0], index=pd.DatetimeIndex(["2024-01-01", "2024-01-06"]))
    assert irf_calendario_diario(feriado, feriado.index.min(), feriado.index.max()).loc["2024-01-05"] == 10.0
    falha = pd.Series([10.0, 20.0], index=pd.DatetimeIndex(["2024-01-01", "2024-01-07"]))
    with pytest.raises(ValueError, match="buraco maior"):
        irf_calendario_diario(falha, falha.index.min(), falha.index.max())


def test_periodo_efetivo_termina_na_ultima_observacao(onda):
    curto = onda.loc[:"2025-06-27"]
    df = gerar_dataset_v2(curto, False, n_poupadores=2, n_frac_classico=1,
                          n_frac_fora_regra=1, n_institucionais=1)
    assert df.attrs["periodo_efetivo"] == {"inicio": "2024-01-01", "fim": "2025-06-27"}
    assert df["timestamp"].max().date() <= pd.Timestamp("2025-06-27").date()
