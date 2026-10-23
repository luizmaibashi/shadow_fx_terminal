"""Ponto de operação da Camada 2, medido por usuário (ADR-0008)."""

import numpy as np
import pandas as pd

from medir_escada import rotulos


def split_por_usuario(df, frac_calibracao=0.5, seed=42) -> tuple[pd.Index, pd.Index]:
    """Divide usuários por tipo, sem misturar transações do mesmo usuário."""
    if not 0 < frac_calibracao < 1:
        raise ValueError("frac_calibracao precisa estar entre 0 e 1")
    usuarios = df[["user_id", "tipo_usuario"]].drop_duplicates()
    if usuarios["user_id"].duplicated().any():
        raise ValueError("user_id possui mais de um tipo_usuario")
    rng = np.random.default_rng(seed)
    calibracao, avaliacao = [], []
    for _, grupo in usuarios.groupby("tipo_usuario", sort=True):
        ids = np.array(sorted(grupo["user_id"].tolist()))
        rng.shuffle(ids)
        n_cal = round(len(ids) * frac_calibracao)
        if len(ids) >= 2:
            n_cal = min(max(n_cal, 1), len(ids) - 1)
        calibracao.extend(ids[:n_cal])
        avaliacao.extend(ids[n_cal:])
    return pd.Index(calibracao), pd.Index(avaliacao)


def _dados(df, score_col, usuarios):
    if score_col not in df:
        raise ValueError(f"score_col ausente: {score_col}")
    if df[score_col].isna().any():
        raise ValueError(f"score_col contém NaN: {score_col}")
    base = df if usuarios is None else df.loc[df["user_id"].isin(usuarios)]
    if base.empty:
        raise ValueError("subconjunto de usuários vazio")
    fraude, poupador = rotulos(base)
    return base, fraude, poupador


def _contagens(base, fraude, poupador, score_col, limiar):
    positivo = base[score_col] >= limiar
    por_usuario = pd.DataFrame({
        "user_id": base["user_id"], "positivo": positivo,
        "fraude": fraude, "poupador": poupador,
    }).groupby("user_id").max()
    fn = int((por_usuario["fraude"] & ~por_usuario["positivo"]).sum())
    fp = int((~por_usuario["fraude"] & por_usuario["positivo"]).sum())
    recall = int((por_usuario["fraude"] & por_usuario["positivo"]).sum())
    poupadores = int((por_usuario["poupador"] & por_usuario["positivo"]).sum())
    n_poupadores = int(por_usuario["poupador"].sum())
    return fn, fp, recall, poupadores, n_poupadores, int(positivo.sum())


def _candidatos(base, score_col):
    return [float("inf"), *sorted(base[score_col].unique(), reverse=True)]


def escolher_limiar_operacao(df, score_col="c2_score_anomalia", x_max=0.05,
                             k_max=None, usuarios=None) -> float | None:
    """Maximiza recall por usuário sob teto de poupadores e de fila."""
    if not 0 < x_max <= 1:
        raise ValueError("x_max precisa estar em (0, 1]")
    if k_max is not None and k_max <= 0:
        raise ValueError("k_max precisa ser positivo")
    base, fraude, poupador = _dados(df, score_col, usuarios)
    melhor_recall = -1
    melhor_limiar = None
    for limiar in _candidatos(base, score_col):
        _, _, recall, n_poup_tocados, n_poup, n_alertas = _contagens(base, fraude, poupador, score_col, limiar)
        if n_poup and n_poup_tocados / n_poup > x_max:
            continue
        if k_max is not None and n_alertas * 100 / len(base) > k_max:
            continue
        if recall > melhor_recall:
            melhor_recall, melhor_limiar = recall, limiar
    return None if melhor_limiar is None or np.isinf(melhor_limiar) else float(melhor_limiar)


def limiar_por_custo(df, score_col, razao_fn_fp: float, usuarios=None) -> float:
    """Minimiza razao_fn_fp * FN + FP, ambos contados por usuário."""
    if not np.isfinite(razao_fn_fp) or razao_fn_fp <= 0:
        raise ValueError("razao_fn_fp precisa ser positiva e finita")
    base, fraude, poupador = _dados(df, score_col, usuarios)
    melhor_custo = float("inf")
    melhor_limiar = float("inf")
    for limiar in _candidatos(base, score_col):
        fn, fp, *_ = _contagens(base, fraude, poupador, score_col, limiar)
        custo = razao_fn_fp * fn + fp
        if custo < melhor_custo:
            melhor_custo, melhor_limiar = custo, limiar
    return float(melhor_limiar)
