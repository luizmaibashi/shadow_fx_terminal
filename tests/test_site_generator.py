"""Contrato público do dashboard estático."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
GERADOR = ROOT / "scripts" / "site" / "gerar.py"


def carregar_gerador():
    spec = importlib.util.spec_from_file_location("gerar_site", GERADOR)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def criar_csvs(tmp_path: Path) -> Path:
    processed = tmp_path / "processed"
    raw = tmp_path / "raw"
    processed.mkdir()
    raw.mkdir()
    pd.DataFrame(
        {
            "date": ["2024-01-01", "2025-01-01"],
            "irf_v2": [42.5, 71.0],
            "brl_adj_dxy_30d": [1.0, 2.0],
            "ipca_desvio_meta": [0.2, 0.4],
            "variacao_usdt_30d": [3.0, 4.0],
            "divida_pib_var": [0.01, 0.02],
            "divida_bruta_pib": [85.0, 87.0],
            "ibc_br_var": [-0.1, -0.2],
            "score_copom": [0.7, 0.6],
        }
    ).to_csv(processed / "dataset_irf_completo.csv", index=False)
    pd.DataFrame(
        {
            "user_id": ["USR_1", "USR_2", "USR_3"],
            "tipo_usuario": ["normal", "fracionador", "normal"],
            "timestamp": ["2025-01-01 02:00", "2025-01-02 03:00", "2025-01-02 12:00"],
            "valor_brl": [1000, 9000, 500],
            "wallet_destino": ["nao-publicar", "nao-publicar", "nao-publicar"],
            "wallets_unicas": [1, 8, 2],
            "c1_razoes": ["", "R3", ""],
            "score_final": [10, 88, 45],
            "alerta_final": ["VERDE", "VERMELHO", "AMARELO"],
            "explicacao_xai": ["ok", "suspeita", "monitorar"],
        }
    ).to_csv(processed / "resultado_compliance.csv", index=False)
    pd.DataFrame(
        {
            "data": ["2025-01-01"],
            "decisao_selic": ["manter"],
            "tom": ["hawkish"],
            "score_hawkish": [0.8],
            "fonte": ["BCB"],
        }
    ).to_csv(raw / "atas_copom_index.csv", index=False)
    return tmp_path


def test_contrato_reduz_dados_e_preserva_metricas(tmp_path: Path):
    gerador = carregar_gerador()
    snapshot = gerador.construir_snapshot(criar_csvs(tmp_path))

    assert snapshot["resumo"]["total_transacoes"] == 3
    assert snapshot["resumo"]["alertas"]["VERMELHO"] == 1
    assert snapshot["irf"]["atual"]["valor"] == 71.0
    assert len(snapshot["alertas_vermelhos"]) == 1
    assert "wallet_destino" not in snapshot["alertas_vermelhos"][0]
    assert snapshot["metadados"]["versao_irf"] == "v2"
    assert snapshot["irf"]["serie"][-1]["divida_bruta_pib"] == 87.0


def test_template_expoe_historia_e_grafico_acessivel():
    html = (ROOT / "scripts" / "site" / "template.html").read_text(encoding="utf-8")

    assert 'id="chart-tooltip"' in html
    assert 'aria-describedby="chart-help"' in html
    assert 'tabindex="0"' in html
    assert "pointermove" in html
    assert "keydown" in html
    assert "Fundamentos fiscais" in html
    assert "Pressão e resposta monetária" in html
    assert "Reação do mercado" in html


def test_contrato_expoe_nivel_e_variacao_anual_da_divida_em_pontos_percentuais(tmp_path: Path):
    gerador = carregar_gerador()
    snapshot = gerador.construir_snapshot(criar_csvs(tmp_path))

    divida = snapshot["divida_bruta"]
    assert divida["nivel_pib"] == 87.0
    assert divida["variacao_12m_pp"] == 2.0
    assert divida["data_referencia"] == "2025-01-01T00:00:00"


def test_indicador_divida_declara_variacao_indisponivel_sem_historico_anual(tmp_path: Path):
    gerador = carregar_gerador()
    irf = pd.DataFrame({"date": pd.to_datetime(["2025-01-01"]), "divida_bruta_pib": [87.0]})

    indicador = gerador.indicador_divida_bruta(irf)

    assert indicador["nivel_pib"] == 87.0
    assert indicador["variacao_12m_pp"] is None


def test_indicador_divida_declara_dados_indisponiveis_sem_coluna_do_estoque(tmp_path: Path):
    gerador = carregar_gerador()
    irf = pd.DataFrame({"date": pd.to_datetime(["2025-01-01"]), "divida_pib_var": [0.0]})

    indicador = gerador.indicador_divida_bruta(irf)

    assert indicador == {"nivel_pib": None, "variacao_12m_pp": None, "data_referencia": None}


def test_contrato_preserva_lacuna_na_serie_irf(tmp_path: Path):
    gerador = carregar_gerador()
    dados = criar_csvs(tmp_path)
    caminho_irf = dados / "processed" / "dataset_irf_completo.csv"
    serie = pd.read_csv(caminho_irf)
    serie.loc[1, "irf_v2"] = None
    serie.to_csv(caminho_irf, index=False)

    snapshot = gerador.construir_snapshot(dados)

    assert snapshot["irf"]["serie"][1]["irf_v2"] is None


def test_renderizacao_embute_contrato_no_html(tmp_path: Path):
    gerador = carregar_gerador()
    dados = criar_csvs(tmp_path)
    template = tmp_path / "template.html"
    destino = tmp_path / "index.html"
    template.write_text("<script>const SNAP=__SNAPSHOT_JSON__;</script>", encoding="utf-8")

    gerador.gerar_site(dados, template, destino)

    html = destino.read_text(encoding="utf-8")
    assert "__SNAPSHOT_JSON__" not in html
    assert '"total_transacoes":3' in html
