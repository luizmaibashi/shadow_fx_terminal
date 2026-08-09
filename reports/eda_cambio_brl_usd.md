# EDA — cambio_brl_usd

Fonte: `data/raw/cambio_brl_usd.csv` (907 linhas, 3 colunas). Série diária de câmbio BRL/USD, 2022-01-03 a 2025-06-27, usada como insumo do IRF (Índice de Risco Fiscal) e do pipeline de compliance AML.

| # | Item | Achado |
|---|---|---|
| 1 | Duplicatas (chave e linha inteira) | 0 duplicatas de linha inteira, 0 duplicatas de `date` — série sem repetição de dia |
| 2 | Colunas constantes / quase constantes | Nenhuma — `brl_usd` e `brl_usd_mm30` têm variância plena (std 0.35 e 0.34) |
| 3 | Valores sentinela em numéricas | Nenhum `0`/`-1`/`9999` em `brl_usd` ou `brl_usd_mm30` |
| 4 | Códigos de ausência mascarados | N/A — sem coluna categórica |
| 5 | Outliers implausíveis (critério relacional) | `brl_usd` no range 4,59–6,30 (2022–2025) é plausível pra BRL/USD no período; sem outlier isolado destoando da vizinhança temporal |
| 6 | Perfil de nulos por coluna | 0 nulos em todas as 3 colunas |
| 7 | Redundância entre colunas | `brl_usd_mm30` é média móvel de 30 dias de `brl_usd` (correlação 0,94) — redundante por construção, mas não é cópia: carrega informação de tendência que `brl_usd` bruto não tem. Não descartar. |
| 8 | Relação de cada bloco com o alvo | Não há alvo neste dataset isoladamente — ele é insumo do IRF (feature macro), calculado em `src/`. Relação com o alvo fica para a EDA do dataset que consome o IRF. |

## Tipos e parsing

- `date`: string ISO (`YYYY-MM-DD`), 100% parseável (`pd.to_datetime`, 0 falhas).
- `brl_usd`, `brl_usd_mm30`: `float64`, sem cast necessário.

## Conclusão

Dataset limpo, sem achado que exija tratamento (sem nulo pra decidir, sem outlier implausível pra virar nulo, sem constante pra descartar). Segue pronto pra dicionário de colunas (`reports/dicionario_cambio_brl_usd.md`).
