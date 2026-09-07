# -*- coding: utf-8 -*-
"""
tests/test_app_smoke.py
========================
Smoke test do dashboard Streamlit (app.py). Não valida conteúdo visual —
só garante que cada uma das 4 páginas roda até o fim sem levantar exceção,
com os dados reais do pipeline (data/processed/, models/). Pula se esses
artefatos não existirem localmente (mesmo padrão do TestDatasetMestre em
test_pipeline_compliance.py — não roda no CI, que não gera data/raw/).
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).parent.parent
APP_PATH = PROJECT_ROOT / "app.py"
DADOS_PRONTOS = (
    (PROJECT_ROOT / "data" / "processed" / "dataset_irf_completo.csv").exists()
    and (PROJECT_ROOT / "models" / "isolation_forest_v1.joblib").exists()
)

PAGINAS = ["Dashboard", "Compliance Scanner", "Análise IRF", "Sobre o Projeto"]


@pytest.mark.skipif(not DADOS_PRONTOS, reason="Requer data/processed/ e models/ gerados localmente (pipeline completo)")
@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_roda_sem_excecao(pagina):
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    if pagina != PAGINAS[0]:
        at.sidebar.radio[0].set_value(pagina).run()
    assert not at.exception, f"Página '{pagina}' levantou exceção: {at.exception}"
