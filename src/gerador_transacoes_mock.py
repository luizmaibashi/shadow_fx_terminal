# -*- coding: utf-8 -*-
"""
gerador_transacoes_mock.py - Shadow FX Terminal (Fase 3)
=========================================================
Gera um dataset simulado de transacoes de stablecoins em exchanges brasileiras.
Simula tres tipos de usuarios conforme a tipologia descrita no paper:

    TIPO A - "Poupador Assustado" (LEGITIMO):
        Compras regulares de USDT pos-salario, tickets medios baixos,
        comportamento estrutural de hedge cambial descrito no paper.

    TIPO B - "Arbitragista Institucional" (LEGITIMO / MONITORAR):
        Grandes volumes em horarios comerciais, transacoes concentradas,
        padrao de mesa de operacoes.

    TIPO C - "Fracionador" (SUSPEITO - Alvo do AML):
        Multiplas transacoes logo abaixo do limite de notificacao (R$ 10.000),
        destinatarios distintos, horarios noturnos/madrugada.
        Tecnica classica de "smurfing" para evasao de divisas.

Saida: data/processed/transacoes_simuladas.csv
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_RAW, PROJECT_ROOT

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "transacoes_simuladas.csv"

np.random.seed(2024)

# Limite de notificacao obrigatorio pelas Resolucoes BCB 519-521/2026
LIMITE_BCB_BRL = 10_000.0

# Periodo de analise
START_DATE = pd.Timestamp("2024-01-01")
END_DATE   = pd.Timestamp("2025-06-30")
DIAS_TOTAL = (END_DATE - START_DATE).days


def gerar_usuario(
    user_id: str,
    tipo: str,
    n_transacoes: int,
    ticket_medio_brl: float,
    ticket_std_brl: float,
    hora_media: int,
    hora_std: int,
    n_wallets_destino: int,
    prob_fracionamento: float = 0.0,
) -> pd.DataFrame:
    """Gera um bloco de transacoes para um usuario de determinado perfil."""
    registros = []

    wallets_destino = [f"0x{np.random.randint(0x100000, 0xFFFFFF):06X}" for _ in range(n_wallets_destino)]

    for _ in range(n_transacoes):
        dia_offset  = np.random.randint(0, DIAS_TOTAL)
        data        = START_DATE + pd.Timedelta(days=int(dia_offset))
        hora        = int(np.clip(np.random.normal(hora_media, hora_std), 0, 23))
        minuto      = np.random.randint(0, 60)
        timestamp   = data + pd.Timedelta(hours=hora, minutes=minuto)

        # Logica de fracionamento: gerar multiplos tickets logo abaixo do limite
        if prob_fracionamento > 0 and np.random.random() < prob_fracionamento:
            # Fracionamento classico: 2-5 tickets entre R$ 8.500 e R$ 9.900
            n_frac = np.random.randint(2, 6)
            for f in range(n_frac):
                valor = np.random.uniform(8_500, LIMITE_BCB_BRL - 100)
                registros.append({
                    "user_id"          : user_id,
                    "tipo_usuario"     : tipo,
                    "timestamp"        : timestamp + pd.Timedelta(minutes=f * np.random.randint(5, 30)),
                    "valor_brl"        : round(valor, 2),
                    "wallet_destino"   : np.random.choice(wallets_destino),
                    "hora"             : hora,
                    "eh_fracionamento" : True,
                })
        else:
            valor = abs(np.random.normal(ticket_medio_brl, ticket_std_brl))
            registros.append({
                "user_id"          : user_id,
                "tipo_usuario"     : tipo,
                "timestamp"        : timestamp,
                "valor_brl"        : round(valor, 2),
                "wallet_destino"   : np.random.choice(wallets_destino),
                "hora"             : hora,
                "eh_fracionamento" : False,
            })

    return pd.DataFrame(registros)


def gerar_dataset() -> pd.DataFrame:
    frames = []

    # --- TIPO A: Poupadores (100 usuarios) ---
    for i in range(100):
        frames.append(gerar_usuario(
            user_id            = f"POUPADOR_{i:04d}",
            tipo               = "A_poupador_legitimo",
            n_transacoes       = np.random.randint(6, 18),       # ~1-2x por mes
            ticket_medio_brl   = np.random.uniform(800, 3_500),  # salario medio BR
            ticket_std_brl     = 300,
            hora_media         = 20,                             # pos-trabalho
            hora_std           = 3,
            n_wallets_destino  = 1,                              # sempre mesma wallet
            prob_fracionamento = 0.0,
        ))

    # --- TIPO B: Institucionais (15 usuarios) ---
    for i in range(15):
        frames.append(gerar_usuario(
            user_id            = f"INSTITUCIONAL_{i:03d}",
            tipo               = "B_institucional_monitorar",
            n_transacoes       = np.random.randint(50, 200),
            ticket_medio_brl   = np.random.uniform(50_000, 500_000),
            ticket_std_brl     = 20_000,
            hora_media         = 11,                             # horario comercial
            hora_std           = 2,
            n_wallets_destino  = np.random.randint(3, 8),
            prob_fracionamento = 0.0,
        ))

    # --- TIPO C: Fracionadores / Suspeitos (10 usuarios) ---
    for i in range(10):
        frames.append(gerar_usuario(
            user_id            = f"SUSPEITO_{i:03d}",
            tipo               = "C_suspeito_fracionamento",
            n_transacoes       = np.random.randint(30, 80),
            ticket_medio_brl   = 9_200,                          # logo abaixo do limite
            ticket_std_brl     = 500,
            hora_media         = 2,                              # madrugada
            hora_std           = 2,
            n_wallets_destino  = np.random.randint(15, 40),      # muitos destinos
            prob_fracionamento = 0.7,                            # fracionamento sistematico
        ))

    df = pd.concat(frames, ignore_index=True).sort_values("timestamp").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["data"]      = df["timestamp"].dt.date

    # Adicionar features derivadas
    df["acima_limite_bcb"] = df["valor_brl"] >= LIMITE_BCB_BRL
    df["madrugada"]        = df["hora"].between(0, 5)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Dataset gerado: {len(df)} transacoes -> {OUTPUT_PATH}")
    print(f"\nDistribuicao por tipo:")
    print(df["tipo_usuario"].value_counts().to_string())
    print(f"\nValor total movimentado: R$ {df['valor_brl'].sum():,.0f}")

    return df


if __name__ == "__main__":
    gerar_dataset()
