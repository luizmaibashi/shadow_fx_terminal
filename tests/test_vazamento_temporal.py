"""Disponibilidade temporal do macro, Copom e features do lote D+1."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from macro_disponibilidade import (  # noqa: E402
    OFFSET_DISPONIBILIDADE_DIAS, SERIES_DIARIAS, derivar_mensais,
    mensal_de_diaria, para_diaria_sem_lookahead,
)
from pipeline_compliance import camada1_filtros_bcb, engenharia_features  # noqa: E402
from utils import calcular_calibracao_irf_v2, calcular_irf_v2  # noqa: E402
import recalcular_irf  # noqa: E402


def macro_mensal():
    indice = pd.date_range("2022-01-01", periods=16, freq="MS")
    return pd.DataFrame({
        "ipca_mensal": np.arange(1, 17, dtype=float),
        "ibc_br": np.arange(100, 116, dtype=float),
        "divida_bruta_pib": np.arange(80, 96, dtype=float),
        "expectativa_ipca_12m": np.arange(4, 20, dtype=float),
        "selic_meta": np.full(16, 10.0),
    }, index=indice)


@pytest.mark.parametrize("coluna", list(OFFSET_DISPONIBILIDADE_DIAS) + list(SERIES_DIARIAS))
def test_perturbacao_futura_nao_muda_passado(coluna):
    mensal = macro_mensal()
    alterado = mensal.copy()
    alterado.loc["2022-03-01", coluna] += 100
    indice = pd.date_range("2022-01-01", "2023-04-30", freq="D")
    antes = para_diaria_sem_lookahead(derivar_mensais(mensal), indice)
    depois = para_diaria_sem_lookahead(derivar_mensais(alterado), indice)
    offset = OFFSET_DISPONIBILIDADE_DIAS.get(coluna, SERIES_DIARIAS.get(coluna))
    corte = pd.Timestamp("2022-03-01") + pd.Timedelta(days=offset)
    pd.testing.assert_frame_equal(antes.loc[antes.index < corte], depois.loc[depois.index < corte])


def test_derivadas_sao_mensais():
    derivado = derivar_mensais(macro_mensal())
    assert derivado.loc["2022-12-01", "ipca_acum_12m"] == sum(range(1, 13))
    assert pd.isna(derivado.loc["2022-11-01", "ipca_acum_12m"])
    assert derivado.loc["2022-02-01", "divida_pib_var"] == pytest.approx((81 / 80 - 1) * 100)
    assert derivado.loc["2022-02-01", "ibc_br_var"] == pytest.approx((101 / 100 - 1) * 100)


def test_antes_da_primeira_disponibilidade_e_nan():
    indice = pd.date_range("2022-01-01", "2022-03-31", freq="D")
    diario = para_diaria_sem_lookahead(derivar_mensais(macro_mensal()), indice)
    assert pd.isna(diario.loc["2022-01-01", "ipca_mensal"])
    assert pd.isna(diario.loc["2022-01-01", "selic_meta"])
    assert diario.loc["2022-02-15", "ipca_mensal"] == 1.0


def test_coluna_sem_offset_falha():
    mensal = macro_mensal().assign(novo_indicador=1.0)
    with pytest.raises(ValueError, match="sem offset"):
        mensal_de_diaria(mensal)


def test_mes_sem_dia_um_falha():
    diario = macro_mensal().drop(pd.Timestamp("2022-03-01"))
    with pytest.raises(ValueError, match="sem dia 1"):
        mensal_de_diaria(diario)


def test_recupera_mensais_e_preserva_selic_no_meio_do_mes():
    mensal = macro_mensal().iloc[:3]
    diario = mensal.resample("D").interpolate("time")
    diario.loc["2022-02-15":, "selic_meta"] = 11.0
    recuperado = mensal_de_diaria(diario)
    pd.testing.assert_series_equal(
        recuperado.loc[mensal.index, "ipca_mensal"], mensal["ipca_mensal"], check_freq=False,
    )
    assert recuperado.loc["2022-02-15", "selic_meta"] == 11.0
    expandido = para_diaria_sem_lookahead(derivar_mensais(recuperado), diario.index)
    assert expandido.loc["2022-02-15", "selic_meta"] == 10.0
    assert expandido.loc["2022-02-16", "selic_meta"] == 11.0


def test_copom_so_afeta_apos_seis_dias(monkeypatch, tmp_path):
    atas = pd.DataFrame({"data": ["2022-02-02", "2022-03-16"], "score_hawkish": [0.8, 0.2]})
    atas.to_csv(tmp_path / "atas_copom_index.csv", index=False)
    monkeypatch.setattr(recalcular_irf, "DATA_RAW", tmp_path)
    primeira = recalcular_irf.carregar_score_copom_diario()
    assert primeira.loc["2022-02-07"] == 0.5
    assert primeira.loc["2022-02-08"] == 0.8
    assert primeira.loc["2022-03-21"] == 0.8
    atas.loc[1, "score_hawkish"] = 0.9
    atas.to_csv(tmp_path / "atas_copom_index.csv", index=False)
    segunda = recalcular_irf.carregar_score_copom_diario()
    pd.testing.assert_series_equal(primeira.loc[:"2022-03-21"], segunda.loc[:"2022-03-21"])


def transacoes(timestamps, wallets):
    return pd.DataFrame({"user_id": ["u"] * len(timestamps), "timestamp": timestamps,
                         "valor_brl": [1000.0] * len(timestamps), "wallet_destino": wallets})


def features(tx, irf=None):
    if irf is None:
        irf = pd.DataFrame({"irf_v2": [50.0]}, index=pd.DatetimeIndex(["2024-01-01"]))
    return engenharia_features(camada1_filtros_bcb(tx), irf)


def test_entropia_nao_ve_dia_posterior_mas_ve_mesmo_dia():
    primeiro = transacoes(["2024-06-15 09:00"], ["w1"])
    futuro = transacoes(["2024-06-15 09:00", "2024-06-16 09:00"], ["w1", "w2"])
    mesmo_dia = transacoes(["2024-06-15 09:00", "2024-06-15 14:00"], ["w1", "w2"])
    base = features(primeiro).loc[0, "entropia_wallets"]
    assert features(futuro).loc[0, "entropia_wallets"] == pytest.approx(base)
    assert features(mesmo_dia).loc[0, "entropia_wallets"] > base


def test_lote_d_mais_um_mantem_r3_e_frequencia_do_dia():
    tx = transacoes(pd.date_range("2024-06-15 09:00", periods=6, freq="h"), [f"w{i}" for i in range(6)])
    resultado = features(tx)
    assert resultado["c1_razoes"].str.contains("R3:").all()
    assert resultado["n_transacoes_dia"].eq(6).all()


def test_p95_ignora_nan_e_irf_nao_zerifica_nan():
    sinais = pd.DataFrame({"divida_pib_var": [np.nan, *range(1, 36)]})
    calibracao = calcular_calibracao_irf_v2(sinais)
    assert calibracao["divida_p95"] == round(float(np.percentile(range(1, 36), 95)), 4)
    resultado = calcular_irf_v2(0.5, 1.0, np.nan, 1.0, 1.0, 1.0)
    assert np.isnan(resultado)


def test_nan_de_disponibilidade_chega_ao_irf_da_serie(caplog):
    indice = pd.date_range("2024-01-01", periods=35, freq="D")
    mestre = pd.DataFrame({
        "usdt_volume": np.arange(100.0, 135.0),
        "brl_usd": np.arange(5.0, 5.35, 0.01)[:35],
        "divida_pib_var": [0.1] * 35,
        "ibc_br_var": [0.1] * 35,
        "desvio_meta_ipca": [1.0] * 35,
        "brl_adj_dxy_30d": [1.0] * 35,
    }, index=indice)
    mestre.loc[indice[32], "desvio_meta_ipca"] = np.nan
    calculado, _ = recalcular_irf.calcular_serie_irf_v2(mestre, None)
    assert pd.isna(calculado.loc[indice[32], "irf_v2"])
    assert pd.notna(calculado.loc[indice[33], "irf_v2"])
    assert "dias com NaN" in caplog.text


def test_irf_fallback_50_e_asof_retrospetivo():
    tx = transacoes(["2024-01-20 09:00", "2024-01-25 09:00"], ["w1", "w1"])
    irf = pd.DataFrame({"irf_v2": [np.nan, 77.0, np.nan]},
                       index=pd.DatetimeIndex(["2024-01-01", "2024-01-10", "2024-01-11"]))
    assert features(tx, irf)["irf_contexto"].tolist() == [50.0, 77.0]
