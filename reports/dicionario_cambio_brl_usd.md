# Dicionário de colunas — cambio_brl_usd

Fonte: `data/raw/cambio_brl_usd.csv`. EDA em `reports/eda_cambio_brl_usd.md`.

## Colunas (pós-limpeza)

| Coluna | Tipo | Significado | Interpretação de negócio |
|---|---|---|---|
| `date` | string ISO (`YYYY-MM-DD`) | Data do pregão/cotação, série diária 2022-01-03 a 2025-06-27 | Chave temporal da série — junta com os outros datasets macro (`macro_bcb`, `variaveis_globais`) por esta coluna pra compor o IRF |
| `brl_usd` | float64 | Cotação de fechamento BRL/USD do dia | Câmbio bruto — é o sinal primário de desvalorização do Real que motiva o "Poupador Assustado" comprar USDT como hedge (ver `AGENTS.md`, Linguagem Ubíqua) |
| `brl_usd_mm30` | float64 | Média móvel de 30 dias de `brl_usd` | Suaviza ruído de curto prazo — usada pra distinguir tendência de desvalorização estrutural de oscilação de dia único. Não é coluna nova derivada por nós: já vem calculada no CSV bruto |

## Features criadas

Nenhuma ainda — este teste cobriu só EDA + dicionário de colunas originais, sem feature engineering nova. Seção fica vazia até a próxima tarefa que criar feature a partir deste dataset (ex.: lag pro IRF, `IRF_LAG_DAYS=14` por `AGENTS.md`).
