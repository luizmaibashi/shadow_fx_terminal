"""Mundos sintéticos pareados para testar a contribuição do IRF (ADR-0011)."""

import numpy as np
import pandas as pd


INICIO = pd.Timestamp("2024-01-01")
FIM = pd.Timestamp("2025-06-30")
DIAS = pd.date_range(INICIO, FIM, freq="D")


def irf_calendario_diario(irf: pd.Series, inicio: pd.Timestamp, fim: pd.Timestamp,
                         max_gap_dias: int = 4) -> pd.Series:
    """Expande dias sem pregão só para o futuro, sem extrapolar a última observação."""
    if not isinstance(irf, pd.Series) or not isinstance(irf.index, pd.DatetimeIndex):
        raise ValueError("irf requer Series com DatetimeIndex")
    if irf.index.has_duplicates or max_gap_dias < 0:
        raise ValueError("datas duplicadas ou max_gap_dias negativo")
    observacoes = irf.sort_index().dropna()
    if observacoes.empty:
        raise ValueError("IRF sem observação válida")
    limite = min(pd.Timestamp(fim), observacoes.index.max())
    dias = pd.date_range(pd.Timestamp(inicio), limite, freq="D")
    if dias.empty:
        raise ValueError("período efetivo do IRF vazio")
    serie = observacoes.reindex(dias)
    faltantes = serie.isna().to_numpy()
    sequencia = 0
    ja_observado = False
    for ausente in faltantes:
        if ausente and ja_observado:
            sequencia += 1
            if sequencia > max_gap_dias:
                raise ValueError(f"IRF com buraco maior que {max_gap_dias} dias seguidos")
        elif not ausente:
            ja_observado = True
            sequencia = 0
    return serie.ffill()


def _irf_no_periodo(irf_diario: pd.Series) -> tuple[pd.DatetimeIndex, np.ndarray]:
    serie = irf_calendario_diario(irf_diario, INICIO, FIM)
    serie = serie.loc[max(INICIO, serie.first_valid_index()):]
    if serie.empty or serie.isna().any():
        raise ValueError("IRF sem cobertura para o período efetivo")
    valores = serie.to_numpy(dtype=float)
    if not np.isfinite(valores).all() or valores.std() == 0:
        raise ValueError("irf_diario requer valores finitos e variância positiva")
    return serie.index, (valores - valores.mean()) / valores.std()


def gerar_dataset_v2(
    irf_diario: pd.Series,
    acoplamento: bool,
    seed: int = 2026,
    n_poupadores: int = 1000,
    n_frac_classico: int = 100,
    n_frac_fora_regra: int = 100,
    n_institucionais: int = 50,
    beta: float = 0.7,
    gama: float = 0.3,
) -> pd.DataFrame:
    """Gera transações sem alterar o RNG global e sem usar rótulos como features."""
    dias, z = _irf_no_periodo(irf_diario)
    rng = np.random.default_rng(seed)
    rng_base = np.random.default_rng(seed + 1)
    pesos = np.exp(beta * z)
    taxa_dia = 12.0 / len(dias) * pesos / pesos.mean()
    taxa = taxa_dia if acoplamento else np.full(len(dias), taxa_dia.mean())
    multiplicadores = 1 + gama * np.maximum(z, 0)
    ticket_placebo = float(np.average(multiplicadores, weights=taxa_dia))
    registros = []

    def adicionar(usuario, tipo, classe, dia, hora, minuto, valor, wallet, fracionamento=False):
        timestamp = dias[int(dia)] + pd.Timedelta(hours=int(hora), minutes=int(minuto))
        registros.append({
            "user_id": usuario,
            "tipo_usuario": tipo,
            "timestamp": timestamp,
            "valor_brl": round(float(valor), 2),
            "wallet_destino": wallet,
            "hora": timestamp.hour,
            "eh_fracionamento": fracionamento,
            "classe_v2": classe,
            "z_irf_dia": float(z[int(dia)]),
        })

    for i in range(n_poupadores):
        usuario = f"POUPADOR_{i:04d}"
        wallet = f"0x{int(rng_base.integers(0x100000, 0xFFFFFF)):06X}"
        ticket = rng_base.uniform(800, 3500)
        quantidades = rng.poisson(taxa)
        for dia in np.flatnonzero(quantidades):
            for _ in range(int(quantidades[dia])):
                hora = int(np.clip(rng.normal(20, 3), 0, 23))
                fator = multiplicadores[dia] if acoplamento else ticket_placebo
                adicionar(usuario, "A_poupador_legitimo", "poupador", dia, hora,
                          rng.integers(0, 60), max(0.0, ticket * fator + rng.normal(0, 300)), wallet)

    # As classes sem resposta ao macro usam a mesma trajetória nos dois mundos.
    rng = np.random.default_rng(seed + 2)
    for i in range(n_institucionais):
        usuario = f"INSTITUCIONAL_{i:03d}"
        wallets = [f"0x{int(x):06X}" for x in rng.integers(0x100000, 0xFFFFFF, size=int(rng.integers(3, 8)))]
        ticket = rng.uniform(50_000, 500_000)
        for dia in rng.integers(0, len(dias), size=int(rng.integers(50, 200))):
            adicionar(usuario, "B_institucional_monitorar", "institucional", dia,
                      np.clip(rng.normal(11, 2), 0, 23), rng.integers(0, 60),
                      abs(rng.normal(ticket, 20_000)), rng.choice(wallets))

    for i in range(n_frac_classico):
        usuario = f"SUSPEITO_CLASSICO_{i:03d}"
        wallets = [f"0x{int(x):06X}" for x in rng.integers(0x100000, 0xFFFFFF, size=int(rng.integers(15, 40)))]
        for dia in rng.integers(0, len(dias), size=int(rng.integers(30, 80))):
            hora = int(np.clip(rng.normal(2, 2), 0, 23))
            minuto = int(rng.integers(0, 60))
            if rng.random() < 0.7:
                for _ in range(int(rng.integers(2, 6))):
                    adicionar(usuario, "C_suspeito_fracionamento", "frac_classico", dia,
                              hora, minuto, rng.uniform(8500, 9900), rng.choice(wallets), True)
            else:
                adicionar(usuario, "C_suspeito_fracionamento", "frac_classico", dia,
                          hora, minuto, abs(rng.normal(9200, 500)), rng.choice(wallets))

    for i in range(n_frac_fora_regra):
        usuario = f"SUSPEITO_FORA_{i:03d}"
        dias_rajada = rng.choice(len(dias), size=int(rng.integers(8, 16)), replace=False)
        for dia in dias_rajada:
            n_transacoes = int(rng.integers(3, 7))
            n_wallets = int(rng.integers(2, min(4, n_transacoes) + 1))
            codigos = set()
            while len(codigos) < n_wallets:
                codigos.add(int(rng.integers(0x100000, 0xFFFFFF)))
            wallets = [f"0x{x:06X}" for x in sorted(codigos)]
            destinos = [*wallets, *rng.choice(wallets, size=n_transacoes - n_wallets)]
            rng.shuffle(destinos)
            for wallet in destinos:
                adicionar(usuario, "C_suspeito_fracionamento", "frac_fora_regra", dia,
                          rng.integers(9, 19), rng.integers(0, 60), rng.uniform(4000, 7900),
                          wallet, True)

    if not registros:
        raise ValueError("ao menos um usuário é necessário")
    df = pd.DataFrame(registros).sort_values("timestamp").reset_index(drop=True)
    df["data"] = df["timestamp"].dt.date
    df["acima_limite_bcb"] = df["valor_brl"] >= 10_000
    df["madrugada"] = df["hora"].between(0, 5)
    df.attrs["periodo_efetivo"] = {"inicio": str(dias.min().date()), "fim": str(dias.max().date())}
    return df
