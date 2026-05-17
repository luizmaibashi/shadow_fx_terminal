# -*- coding: utf-8 -*-
"""
src/treinar_modelo.py - Shadow FX Terminal
===========================================
Treina o modelo campeão (Isolation Forest) usando os dados simulados
e salva os artefatos v1 para produção.

Este script garante a paridade entre o experimento (Notebook 03) 
e a produção (API/Pipeline).
"""

import sys
import joblib
import logging
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Training")

# Setup de caminhos
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils import DATA_PROC
from pipeline_compliance import FEATURES_ML, engenharia_features

MODELS_DIR = PROJECT_ROOT / "models"

def main():
    logger.info("Iniciando treinamento do modelo campeão (v1)...")

    # 1. Carregar dados
    tx_path = DATA_PROC / "transacoes_simuladas.csv"
    irf_path = DATA_PROC / "dataset_irf_completo.csv"

    if not tx_path.exists() or not irf_path.exists():
        logger.error("Dados não encontrados. Execute o setup de dados primeiro.")
        return

    df_tx = pd.read_csv(tx_path)
    df_irf = pd.read_csv(irf_path, index_col="date", parse_dates=True)

    # 2. Engenharia de Features (Paridade garantida via pipeline_compliance)
    logger.info(f"Executando engenharia de features em {len(df_tx)} transações...")
    df_features = engenharia_features(df_tx, df_irf)
    
    X = df_features[FEATURES_ML].fillna(0).values

    # 3. Treinamento
    logger.info("Treinando Isolation Forest (Contamination=0.07)...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Parametros baseados no benchmark do Notebook 03
    modelo = IsolationForest(
        n_estimators=200,
        contamination=0.07,
        random_state=42,
        n_jobs=-1
    )
    modelo.fit(X_scaled)

    # 4. Persistência v1
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_out = MODELS_DIR / "isolation_forest_v1.joblib"
    scaler_out = MODELS_DIR / "scaler_v1.joblib"

    joblib.dump(modelo, model_out)
    joblib.dump(scaler, scaler_out)

    logger.info(f"✅ Modelo salvo em: {model_out}")
    logger.info(f"✅ Scaler salvo em: {scaler_out}")
    logger.info("Treinamento concluído com sucesso.")

if __name__ == "__main__":
    main()
