"""Gera a página estática do Shadow FX Terminal a partir do snapshot público."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ARQUIVOS = (
    Path("processed/dataset_irf_completo.csv"),
    Path("processed/resultado_compliance.csv"),
    Path("raw/atas_copom_index.csv"),
)


def _json(valor: Any) -> Any:
    """Converte valores pandas para o contrato JSON sem vazar NaN."""
    if valor is None or pd.isna(valor):
        return None
    if isinstance(valor, (pd.Timestamp, datetime, date)):
        return valor.isoformat()
    if hasattr(valor, "item"):
        return valor.item()
    return valor


def _registros(df: pd.DataFrame, colunas: list[str]) -> list[dict[str, Any]]:
    selecionadas = [coluna for coluna in colunas if coluna in df.columns]
    return [
        {coluna: _json(valor) for coluna, valor in linha.items()}
        for linha in df[selecionadas].to_dict(orient="records")
    ]


def indicador_divida_bruta(irf: pd.DataFrame) -> dict[str, Any]:
    """Expõe nível e tendência anual sem reutilizar a variação diária do IRF."""
    if "divida_bruta_pib" not in irf.columns:
        return {"nivel_pib": None, "variacao_12m_pp": None, "data_referencia": None}

    serie = irf[["date", "divida_bruta_pib"]].dropna().sort_values("date")
    if serie.empty:
        return {"nivel_pib": None, "variacao_12m_pp": None, "data_referencia": None}

    atual = serie.iloc[-1]
    alvo = atual["date"] - pd.DateOffset(months=12)
    historico = serie[serie["date"] <= alvo]
    anterior = historico.iloc[-1] if not historico.empty else None

    return {
        "nivel_pib": _json(atual["divida_bruta_pib"]),
        "variacao_12m_pp": _json(atual["divida_bruta_pib"] - anterior["divida_bruta_pib"]) if anterior is not None else None,
        "data_referencia": _json(atual["date"]),
        "data_base_12m": _json(anterior["date"]) if anterior is not None else None,
    }


def encontrar_diretorio_dados(raiz: Path = ROOT) -> Path:
    """Prefere o pipeline local; no clone público usa o snapshot do Space."""
    candidatos = (raiz / "data", raiz / "deploy" / "hf_space" / "data")
    for candidato in candidatos:
        if all((candidato / arquivo).exists() for arquivo in ARQUIVOS):
            return candidato
    esperados = ", ".join(str(arquivo) for arquivo in ARQUIVOS)
    raise FileNotFoundError(f"Não encontrei o snapshot público: {esperados}")


def construir_snapshot(dados: Path) -> dict[str, Any]:
    """Reduz os três CSVs ao contrato mínimo da página pública."""
    irf = pd.read_csv(dados / ARQUIVOS[0], parse_dates=["date"]).sort_values("date")
    compliance = pd.read_csv(dados / ARQUIVOS[1], parse_dates=["timestamp"], low_memory=False)
    copom = pd.read_csv(dados / ARQUIVOS[2], parse_dates=["data"]).sort_values("data")

    coluna_irf = "irf_v2" if "irf_v2" in irf.columns else "irf"
    atual = irf.iloc[-1]
    alertas = compliance["alerta_final"].value_counts().to_dict()
    vermelhos = compliance[compliance["alerta_final"] == "VERMELHO"].copy()
    vermelhos = vermelhos.sort_values("score_final", ascending=False).head(15)

    return {
        "metadados": {
            "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
            "fonte": "snapshot público isolado do projeto",
            "versao_irf": "v2",
            "observacao": "Transações sintéticas; contexto macroeconômico histórico.",
        },
        "resumo": {
            "total_transacoes": int(len(compliance)),
            "alertas": {chave: int(valor) for chave, valor in alertas.items()},
            "periodo_irf": {"inicio": _json(irf["date"].iloc[0]), "fim": _json(atual["date"])},
        },
        "irf": {
            "atual": {"data": _json(atual["date"]), "valor": _json(atual[coluna_irf])},
            "serie": _registros(
                irf,
                ["date", coluna_irf, "brl_adj_dxy_30d", "ipca_desvio_meta", "variacao_usdt_30d", "divida_pib_var", "divida_bruta_pib", "ibc_br_var", "score_copom"],
            ),
        },
        "divida_bruta": indicador_divida_bruta(irf),
        "alertas_vermelhos": _registros(
            vermelhos,
            ["user_id", "tipo_usuario", "timestamp", "valor_brl", "wallets_unicas", "c1_razoes", "score_final", "explicacao_xai"],
        ),
        "atas_copom": _registros(copom, ["data", "decisao_selic", "tom", "score_hawkish", "fonte"]),
    }


def gerar_site(dados: Path, template: Path, destino: Path) -> dict[str, Any]:
    snapshot = construir_snapshot(dados)
    payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.read_text(encoding="utf-8").replace("__SNAPSHOT_JSON__", payload)
    if "__SNAPSHOT_JSON__" in html:
        raise ValueError("Template sem marcador __SNAPSHOT_JSON__")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=None)
    parser.add_argument("--template", type=Path, default=ROOT / "scripts/site/template.html")
    parser.add_argument("--saida", type=Path, default=ROOT / "docs/index.html")
    args = parser.parse_args()
    dados = args.dados or encontrar_diretorio_dados()
    snapshot = gerar_site(dados, args.template, args.saida)
    print(f"Página gerada: {args.saida} ({len(snapshot['irf']['serie'])} pontos de IRF)")


if __name__ == "__main__":
    main()
