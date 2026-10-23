"""Contrato dos ADRs 0008 e 0009."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from decisao import escolher_limiar_operacao, limiar_por_custo, split_por_usuario


def exemplo():
    return pd.DataFrame({
        "user_id": ["a1", "a2", "f1", "f2"],
        "tipo_usuario": ["A_poupador", "A_poupador", "C_suspeito", "C_suspeito"],
        "c2_score_anomalia": [20.0, 60.0, 80.0, 50.0],
    })


def test_limiar_otimo_e_teto():
    assert escolher_limiar_operacao(exemplo()) == 80.0
    assert escolher_limiar_operacao(exemplo(), x_max=0.5) == 50.0


def test_sem_limiar_util_devolve_none():
    df = exemplo()
    df.loc[df.user_id.str.startswith("f"), "c2_score_anomalia"] = 10.0
    assert escolher_limiar_operacao(df) is None


def test_empate_prefere_maior_limiar():
    df = exemplo()
    df.loc[df.user_id == "f2", "c2_score_anomalia"] = 80.0
    assert escolher_limiar_operacao(df) == 80.0


def test_k_max_muda_escolha():
    df = exemplo()
    assert escolher_limiar_operacao(df, x_max=0.5) == 50.0
    assert escolher_limiar_operacao(df, x_max=0.5, k_max=25) == 80.0


def test_limiar_so_usa_usuarios_calibracao():
    df = exemplo()
    calibracao = ["a1", "f1"]
    esperado = escolher_limiar_operacao(df, usuarios=calibracao)
    df.loc[df.user_id == "f2", "tipo_usuario"] = "A_poupador"
    assert escolher_limiar_operacao(df, usuarios=calibracao) == esperado


def test_split_estratificado_reprodutivel():
    df = pd.concat([exemplo(), exemplo().assign(user_id=["a3", "a4", "f3", "f4"])])
    cal, aval = split_por_usuario(df)
    assert cal.intersection(aval).empty
    assert set(cal).union(aval) == set(df.user_id)
    assert cal.equals(split_por_usuario(df)[0])
    for tipo, grupo in df.groupby("tipo_usuario"):
        ids = set(grupo.user_id)
        assert ids.intersection(cal) and ids.intersection(aval), tipo


@pytest.mark.parametrize("kwargs,mensagem", [
    ({"x_max": 0}, "x_max"), ({"x_max": 1.1}, "x_max"),
    ({"k_max": 0}, "k_max"), ({"score_col": "ausente"}, "score_col"),
])
def test_entrada_invalida(kwargs, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        escolher_limiar_operacao(exemplo(), **kwargs)


def test_score_nan_falha():
    df = exemplo()
    df.loc[0, "c2_score_anomalia"] = float("nan")
    with pytest.raises(ValueError, match="NaN"):
        escolher_limiar_operacao(df)


def test_custo_contado_por_usuario():
    assert limiar_por_custo(exemplo(), "c2_score_anomalia", 1) == 80.0
    assert limiar_por_custo(exemplo(), "c2_score_anomalia", 10) == 50.0
