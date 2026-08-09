# Dicionário de colunas — variaveis_globais

Fonte: `data/raw/variaveis_globais.csv`. EDA em `reports/eda_variaveis_globais.md`.

## Colunas (pós-limpeza)

| Coluna | Tipo | Significado | Interpretação de negócio |
|---|---|---|---|
| `date` | string ISO | Data de referência | Chave temporal |
| `dxy` | float64 | US Dollar Index | Duplicado de `brl_ajustado_dxy.csv > dxy` (EDA, item 7) — mesma fonte, tratamento de nulo diferente |
| `vix` | float64 | Índice de volatilidade implícita (CBOE) — "índice do medo" | Estresse do mercado financeiro global, independente de Brasil |
| `sp500` | float64 | Índice S&P 500 | Apetite a risco global |
| `dxy_var_30d` | float64 | Variação % do DXY em 30 dias | Velocidade do movimento do dólar global |
| `vix_var_30d` | float64 | Variação % do VIX em 30 dias | Velocidade de mudança do "medo" do mercado — picos reais em eventos como o unwind do carry trade do iene (ago/2024) |

## Conexão com objetivo de negócio

Doc de origem: `docs/adr/0003-irf-v2-seis-sinais.md` (contexto) — nenhuma destas colunas é sinal formal do IRF v2, mas `dxy` alimenta indiretamente o cálculo de `brl_adj_dxy_30d` (via `brl_ajustado_dxy.csv`, dataset separado).

**Hipótese que este dataset testa**: nenhuma diretamente — é dado de contexto/controle. Serve pra checar se um movimento de câmbio ou volume USDT é "coisa do Brasil" ou "coisa do mundo" (mercado de risco global em estresse). Sem esse contexto, a hipótese "Poupador Assustado" corre risco de confundir desvalorização específica do Real com desvalorização de moedas emergentes em geral.

**Colunas candidatas a feature** (checado via grep no código, não suposição): `vix` **já é usada** — entra na seleção de `carregar_dataset_mestre()` (`src/utils.py:348`) e em `analise_correlacao.py`. `sp500` **é coletada e nunca consumida** — mesmo padrão órfão de `expectativa_ipca_12m` em `macro_bcb` (não aparece em `utils.py`, `analise_correlacao.py` nem notebooks). `vix_var_30d` também não está selecionada em `utils.py` — candidata a feature nova não explorada ainda, diferente de `sp500` que nem tem uso planejado visível. `dxy`/`dxy_var_30d` não devem virar feature nova aqui — já são consumidos via `brl_ajustado_dxy.csv`, usar os dois seria contar o mesmo sinal duas vezes.

## Features criadas

Nenhuma criada por nós — dataset é insumo bruto de yfinance.
