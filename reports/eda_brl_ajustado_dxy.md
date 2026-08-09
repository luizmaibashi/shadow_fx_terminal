# EDA — brl_ajustado_dxy

Fonte: `data/raw/brl_ajustado_dxy.csv` (907 linhas, 6 colunas). 2022-01-03 a 2025-06-27. Câmbio BRL/USD ajustado por força global do dólar (DXY) — insumo do sinal #2 do IRF v2 (`docs/adr/0003-irf-v2-seis-sinais.md`).

| # | Item | Achado |
|---|---|---|
| 1 | Duplicatas (chave e linha inteira) | 0 duplicatas de linha inteira, 0 duplicatas de `date` |
| 2 | Colunas constantes / quase constantes | Nenhuma |
| 3 | Valores sentinela em numéricas | 3 ocorrências de `dxy_var_30d == 0` — checado individualmente, são variação líquida zero em 30 dias, plausível (não sentinela). Nenhum `-1`/`9999` real |
| 4 | Códigos de ausência mascarados | N/A — sem coluna categórica |
| 5 | Outliers implausíveis (critério relacional) | `dxy` no range 94,79–114,11 é plausível pro período (2022-2025 teve DXY nesse patamar). `brl_usd_var_30d`/`dxy_var_30d` em % de variação 30d, extremos (-9,99% / +14,93%) coerentes com estresse cambial real do período (ex. 2022) |
| 6 | Perfil de nulos por coluna | `brl_usd`: 0. `brl_usd_var_30d`: 30 (warmup do rolling 30d, esperado). `dxy`: **32 nulos espalhados, não só no início** — feriado de mercado nos EUA (DXY não cota) em dia que B3 cotou `brl_usd`. `dxy_var_30d`/`brl_adj_dxy_30d`: 62 nulos — soma do warmup de 30d + propagação dos nulos de `dxy` através da janela móvel |
| 7 | Redundância entre colunas | **`brl_usd` desta tabela é idêntico, linha a linha, a `cambio_brl_usd.csv > brl_usd`** (907/907 linhas batem, diferença máxima 0.0) — mesma cotação ingerida em dois arquivos. Tratar como a mesma fonte, não como sinal duplo em feature engineering |
| 8 | Relação de cada bloco com o alvo | Sem alvo neste dataset isoladamente — `brl_adj_dxy_30d` é o insumo do sinal #2 do IRF v2 (peso 20%, r=+0.521 com demanda USDT, por ADR-0003) |

## Tipos e parsing

- `date`: string ISO, 100% parseável.
- Demais colunas: `float64`, sem cast necessário.

## Conclusão

Nulo em `dxy` e derivados não é erro de coleta — é ausência real de cotação em feriado do mercado americano, propagada pela janela de 30 dias. Não converter pra 0 nem interpolar sem justificativa: linhas com `dxy` nulo devem ficar nulas em qualquer feature que dependa dela. Redundância de `brl_usd` com `cambio_brl_usd.csv` documentada — não é erro, mas feature engineering não deve tratar como duas fontes independentes.
