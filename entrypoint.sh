#!/bin/sh
# Roda o pipeline de setup automaticamente na primeira execucao (data/models
# chegam vazios num clone novo, so tem .gitkeep). Evita a etapa manual
# "docker-compose run setup" antes do primeiro "docker-compose up --build".
set -e

DATASET="data/processed/dataset_irf_completo.csv"
MODELO="models/isolation_forest_v1.joblib"

if [ ! -f "$DATASET" ] || [ ! -f "$MODELO" ]; then
    echo "[entrypoint] dado/modelo ausente — rodando setup (primeira vez, ~2min)..."
    python src/coletar_dados.py
    python src/scraper_copom.py
    python src/coletar_google_trends_br.py
    python src/gerador_transacoes_mock.py
    python src/treinar_modelo.py
    python src/pipeline_compliance.py
    echo "[entrypoint] setup concluido."
else
    echo "[entrypoint] dado/modelo ja existentes, pulando setup."
fi

exec "$@"
