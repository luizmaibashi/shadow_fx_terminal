"""Disponibilidade temporal dos sinais macro usados no IRF."""

import pandas as pd


# Estimativas conservadoras; conferir no calendário oficial antes da Fase 3.
OFFSET_DISPONIBILIDADE_DIAS = {
    "ipca_mensal": 45,
    "ibc_br": 80,
    "divida_bruta_pib": 65,
    "expectativa_ipca_12m": 35,
}
SERIES_DIARIAS = {"selic_meta": 1}
DERIVADAS_RECALCULADAS = {"ipca_acum_12m", "desvio_meta_ipca", "divida_pib_var", "ibc_br_var"}
ORIGEM_DERIVADAS = {
    "ipca_acum_12m": "ipca_mensal",
    "desvio_meta_ipca": "ipca_mensal",
    "divida_pib_var": "divida_bruta_pib",
    "ibc_br_var": "ibc_br",
}


def _validar_colunas(df: pd.DataFrame) -> None:
    desconhecidas = set(df.columns) - set(OFFSET_DISPONIBILIDADE_DIAS) - set(SERIES_DIARIAS) - DERIVADAS_RECALCULADAS
    if desconhecidas:
        raise ValueError(f"coluna macro sem offset de disponibilidade: {sorted(desconhecidas)}")


def mensal_de_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """Retém observações mensais do dia 1 e toda a série diária da Selic."""
    _validar_colunas(df)
    if not isinstance(df.index, pd.DatetimeIndex) or df.index.has_duplicates:
        raise ValueError("macro requer DatetimeIndex sem duplicatas")
    fontes = [c for c in OFFSET_DISPONIBILIDADE_DIAS if c in df]
    diario = [c for c in SERIES_DIARIAS if c in df]
    mensais = df.loc[df.index.day == 1, fontes].copy()
    if fontes:
        meses = pd.period_range(df.index.min().to_period("M"), df.index.max().to_period("M"), freq="M")
        faltantes = [str(m) for m in meses if m.to_timestamp() not in mensais.index]
        if faltantes:
            raise ValueError(f"macro sem dia 1 nos meses: {faltantes}")
    if diario:
        selic = df[diario].dropna(how="all")
        return mensais.join(selic, how="outer").sort_index()
    return mensais


def derivar_mensais(mensal: pd.DataFrame) -> pd.DataFrame:
    """Calcula derivadas sobre observações mensais, nunca sobre dias interpolados."""
    _validar_colunas(mensal)
    resultado = mensal.drop(columns=list(DERIVADAS_RECALCULADAS & set(mensal.columns))).copy()
    if "ipca_mensal" in resultado:
        ipca = resultado["ipca_mensal"].dropna()
        resultado["ipca_acum_12m"] = ipca.rolling(12, min_periods=12).sum()
        resultado["desvio_meta_ipca"] = resultado["ipca_acum_12m"] - 3.0
    if "divida_bruta_pib" in resultado:
        divida = resultado["divida_bruta_pib"].dropna()
        resultado["divida_pib_var"] = divida.pct_change(fill_method=None) * 100
    if "ibc_br" in resultado:
        ibc = resultado["ibc_br"].dropna()
        resultado["ibc_br_var"] = ibc.pct_change(fill_method=None) * 100
    return resultado


def para_diaria_sem_lookahead(mensal: pd.DataFrame, indice_diario: pd.DatetimeIndex) -> pd.DataFrame:
    """Publica cada sinal no offset contratado e propaga só para o futuro."""
    _validar_colunas(mensal)
    if not isinstance(indice_diario, pd.DatetimeIndex):
        raise ValueError("indice_diario requer DatetimeIndex")
    resultado = pd.DataFrame(index=indice_diario)
    for coluna in mensal:
        origem = ORIGEM_DERIVADAS.get(coluna, coluna)
        offset = OFFSET_DISPONIBILIDADE_DIAS.get(origem, SERIES_DIARIAS.get(origem))
        if offset is None:
            raise ValueError(f"coluna macro sem offset de disponibilidade: {coluna}")
        observacoes = mensal[coluna].dropna()
        observacoes.index = observacoes.index + pd.Timedelta(days=offset)
        resultado[coluna] = observacoes.reindex(observacoes.index.union(indice_diario)).sort_index().ffill().reindex(indice_diario)
    return resultado
