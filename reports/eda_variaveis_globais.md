# EDA — variaveis_globais

Fonte: `data/raw/variaveis_globais.csv` (876 linhas, 6 colunas). 2022-01-03 a 2025-06-27. Contexto de mercado global (DXY, VIX, S&P 500) — usado como coluna opcional em `carregar_dataset_mestre()` (`src/utils.py`).

| # | Item | Achado |
|---|---|---|
| 1 | Duplicatas (chave e linha inteira) | 0 duplicatas de linha inteira, 0 duplicatas de `date` |
| 2 | Colunas constantes / quase constantes | Nenhuma |
| 3 | Valores sentinela em numéricas | Nenhum `0`/`-1`/`9999` |
| 4 | Códigos de ausência mascarados | N/A — sem coluna categórica |
| 5 | Outliers implausíveis (critério relacional) | `vix_var_30d` chega a +192% (2024-08-05) e -61% (mai/2025) — verificado contra evento real: agosto/2024 foi o "unwind do carry trade do iene" (VIX saltou de ~15 pra 38 em dias), evento de mercado documentado, não erro. Mantido |
| 6 | Perfil de nulos por coluna | `vix`/`sp500`: 2 nulos cada. `dxy_var_30d`: 30 (warmup). `vix_var_30d`: 33 (warmup + 2 nulos de origem). `dxy`: **0 nulos** — diferente de `brl_ajustado_dxy.csv`, que tem 32 nulos na mesma coluna (ver item 7) |
| 7 | Redundância entre colunas | **`dxy` desta tabela é idêntico a `brl_ajustado_dxy.csv > dxy`** nas 875 datas em comum (diferença máxima 0,0). Este arquivo tem 876 linhas contra 907 do outro — **as 31 datas que faltam aqui são exatamente as datas onde `dxy` era nulo no outro arquivo** (feriado de mercado americano): este dataset já veio com essas linhas removidas, o outro manteve como nulo. Mesma fonte, duas formas de lidar com a ausência |
| 8 | Relação de cada bloco com o alvo | Sem alvo formal — contexto macro global, usado como feature opcional em `carregar_dataset_mestre()`. Não faz parte dos 6 sinais do IRF v2 (ADR-0003) |

## Tipos e parsing

- `date`: string ISO, 100% parseável.
- Demais colunas: `float64`.

## Conclusão

Terceira redundância de câmbio/DXY encontrada nesta bateria de EDA (depois de `brl_usd` duplicado entre `cambio_brl_usd`/`brl_ajustado_dxy`, e `desvio_meta_ipca`≡`ipca_acum_12m` em `macro_bcb`): `dxy` está em 2 arquivos, com tratamento de ausência diferente entre eles. Não é erro, mas quem for consumir `dxy` deveria escolher uma fonte só — hoje há risco de inconsistência silenciosa se um pipeline ler de um arquivo e outro pipeline ler do outro.
