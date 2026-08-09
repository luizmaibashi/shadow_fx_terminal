# EDA — macro_bcb

Fonte: `data/raw/macro_bcb.csv` (1277 linhas, 8 colunas). 2022-01-01 a 2025-06-30. Indicadores macro do Banco Central (via `python-bcb`) — insumo dos sinais #1, #3, #6 do IRF v2 (`docs/adr/0003-irf-v2-seis-sinais.md`).

| # | Item | Achado |
|---|---|---|
| 1 | Duplicatas (chave e linha inteira) | 0 duplicatas de linha inteira, 0 duplicatas de `date` |
| 2 | Colunas constantes / quase constantes | Nenhuma |
| 3 | Valores sentinela em numéricas | `ipca_mensal == 0.0` em 1 linha (2023-06-13) e `desvio_meta_ipca == 0.0` em 1 linha (2025-05-22) — checados individualmente, são valores reais plausíveis (mês sem inflação / desvio zero da meta), não sentinela |
| 4 | Códigos de ausência mascarados | N/A — sem coluna categórica |
| 5 | Outliers implausíveis (critério relacional) | `selic_meta` 9,25%-15%, `ipca_acum_12m` -7,56% a 18,73% — ambos plausíveis pro período (Selic subiu forte em 2022, IPCA teve deflação pontual em 2023 e pico em 2022). Sem outlier isolado destoando |
| 6 | Perfil de nulos por coluna | `ipca_acum_12m`/`desvio_meta_ipca`: 11 nulos, todos nas primeiras linhas (jan/2022) — warmup do acumulado de 12 meses, esperado, não erro |
| 7 | Redundância entre colunas | **`desvio_meta_ipca` = `ipca_acum_12m` - 3,0 (meta do Copom), sempre, exatamente (correlação 1,00, diferença constante = 3,0 em 1266/1266 linhas não-nulas)** — é transformação linear pura, não informação nova. `ipca_mensal` correlaciona 0,98 com `ipca_acum_12m` (esperado, mesma série em janelas diferentes) mas não é redundância total |
| 8 | Relação de cada bloco com o alvo | Sem alvo neste dataset isoladamente. Por ADR-0003: `divida_bruta_pib` é sinal #1 (peso 30%, r=+0,707 — o mais forte do IRF v2), `desvio_meta_ipca`/`ipca_acum_12m` alimentam sinal #3 (peso 15%), `ibc_br` alimenta sinal #6 (peso 10%). `selic_meta` e `expectativa_ipca_12m` não aparecem na tabela de 6 sinais do ADR — checar se ainda são usados ou são coleta órfã (ver seção de conexão com negócio) |

## Tipos e parsing

- `date`: string ISO, 100% parseável.
- Demais colunas: `float64`, sem cast necessário.

## Conclusão

Achado que precisa virar decisão de feature engineering: usar `ipca_acum_12m` OU `desvio_meta_ipca`, nunca os dois — são a mesma informação. `selic_meta` e `expectativa_ipca_12m` estão no dataset mas não aparecem nos 6 sinais documentados no ADR-0003 — investigar na sabatina se são coleta morta ou se o ADR ficou desatualizado.
