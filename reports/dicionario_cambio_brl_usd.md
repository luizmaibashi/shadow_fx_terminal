# Dicionário de colunas — cambio_brl_usd

Fonte: `data/raw/cambio_brl_usd.csv`. EDA em `reports/eda_cambio_brl_usd.md`.

## Colunas (pós-limpeza)

| Coluna | Tipo | Significado | Interpretação de negócio |
|---|---|---|---|
| `date` | string ISO (`YYYY-MM-DD`) | Data do pregão/cotação, série diária 2022-01-03 a 2025-06-27 | Chave temporal da série — junta com os outros datasets macro (`macro_bcb`, `variaveis_globais`) por esta coluna pra compor o IRF |
| `brl_usd` | float64 | Cotação de fechamento BRL/USD do dia | Câmbio bruto — é o sinal primário de desvalorização do Real que motiva o "Poupador Assustado" comprar USDT como hedge (ver `AGENTS.md`, Linguagem Ubíqua) |
| `brl_usd_mm30` | float64 | Média móvel de 30 dias de `brl_usd` | Suaviza ruído de curto prazo — usada pra distinguir tendência de desvalorização estrutural de oscilação de dia único. Não é coluna nova derivada por nós: já vem calculada no CSV bruto |

## Conexão com objetivo de negócio

Sabatina 2026-08-09, confirmada com o usuário. Fonte: `docs/adr/0003-irf-v2-seis-sinais.md` + uso real em `src/utils.py` (`carregar_dados_base()`, `carregar_dataset_mestre()` — sinal #1).

**Hipótese que este dataset testa**: "Poupador Assustado" (`AGENTS.md`) — quando o Real desvaloriza frente ao dólar, parte do público compra USDT como hedge. `brl_usd` (câmbio bruto, nominal) é o dado certo pra essa hipótese — é o que o poupador vê e reage, não uma versão ajustada.

**Por que bruto e não `brl_ajustado_dxy`**: existe um segundo dataset (`brl_ajustado_dxy.csv`) que isola o risco Brasil do movimento global do dólar (DXY) — usado no IRF v2 (ADR-0003, sinal #2, peso 20%) pra evitar falso positivo quando o dólar sobe globalmente sem ligação com risco fiscal brasileiro. Papel diferente: `cambio_brl_usd` é o sinal comportamental direto (pareado com volume USDT em `carregar_dados_base()`); `brl_ajustado_dxy` é insumo de contexto macro pro índice de risco.

**Colunas candidatas a feature**: `brl_usd` pareado com volume/variação de USDT (`stablecoins_yfinance_real.csv`) é a combinação que testa a hipótese diretamente. `brl_usd_mm30` serve pra distinguir tendência estrutural de ruído de curto prazo antes de disparar alerta de compliance.

## Features criadas

Nenhuma ainda — este teste cobriu só EDA + dicionário de colunas originais, sem feature engineering nova. Seção fica vazia até a próxima tarefa que criar feature a partir deste dataset (ex.: lag pro IRF, `IRF_LAG_DAYS=14` por `AGENTS.md`).
