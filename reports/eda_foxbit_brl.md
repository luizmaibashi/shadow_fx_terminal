# EDA — foxbit_brl

Fonte: `data/raw/foxbit_brl.csv` (1277 linhas, 7 colunas). 2022-01-01 a 2025-06-30. Volume real negociado na Foxbit (exchange brasileira) — dado Brasil-específico, coletado via `src/coletar_foxbit.py` (ver `docs/wayfinder/shadow-fx-dado-brasil-especifico/`).

| # | Item | Achado |
|---|---|---|
| 1 | Duplicatas (chave e linha inteira) | 0 duplicatas de linha inteira, 0 duplicatas de índice (`date`) |
| 2 | Colunas constantes / quase constantes | Nenhuma |
| 3 | Valores sentinela em numéricas | Nenhum `0`/`-1`/`9999` em nenhuma coluna |
| 4 | Códigos de ausência mascarados | N/A — sem coluna categórica |
| 5 | Outliers implausíveis (critério relacional) | 18 dias de `foxbit_usdt_volume` e 4 de `foxbit_usdc_volume` passam de 20x a mediana — checado individualmente: **não é erro tipo o achado em `stablecoins_yfinance_real.csv`** (aquele era 1 dia isolado, ~1.000x, vizinhos normais). Aqui os picos estão concentrados em 2024-07 a 2024-12 (17 dos 18 outliers de USDT), coerente com **crescimento orgânico real** — volume médio anual sobe de ~98 mil (2022) pra ~1,02 milhão (2024), 10x em 3 anos, plausível pra exchange em expansão. `foxbit_usdt_close`/`foxbit_usdc_close` ficam sempre entre 4,61 e 6,33 — mesma faixa de `cambio_brl_usd.csv` (4,59-6,30), validação cruzada de sanidade |
| 6 | Perfil de nulos por coluna | 0 nulos em todas as 7 colunas — cobertura diária completa, sem gap (diferente do `dxy` do dataset global, que tem nulo em feriado de mercado americano; Foxbit roda 24/7 como exchange cripto) |
| 7 | Redundância entre colunas | `foxbit_vol_total` = `foxbit_usdt_volume` + `foxbit_usdc_volume` (diferença máxima ~9e-10, epsilon de float) — soma determinística, não é sinal independente. **Diferente do dataset global**: `usdt_volume` x `usdc_volume` correlacionam 0,94 lá; aqui `foxbit_usdt_volume` x `foxbit_usdc_volume` correlacionam só 0,21 — os dois mercados da Foxbit não se movem juntos, cada um carrega informação própria |
| 8 | Relação de cada bloco com o alvo | Sem alvo formal neste dataset isoladamente — é candidato a sinal comparado contra `usdt_volume` (global) em `src/comparar_correlacao_br.py` (Task 4), não durante o EDA |

## Tipos e parsing

- `date` (índice): datetime, 100% parseável, sem gap.
- Demais colunas: `float64` (volume, close) e `int64` (`n_trades`), sem cast necessário.

## Conclusão

Dataset limpo, sem achado que exija tratamento. Diferente do outlier real encontrado em `stablecoins_yfinance_real.csv` (2 dias corrompidos, ~1000x, isolados) — aqui os valores altos são consistentes com o contexto (crescimento da exchange), não erro de coleta. Pronto pro dicionário de colunas.
