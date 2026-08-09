# EDA — stablecoins_yfinance_real

Fonte: `data/raw/stablecoins_yfinance_real.csv` (1276 linhas, 9 colunas). 2022-01-01 a 2025-06-29. Volume e preço globais de USDT/USDC (yfinance) — variável comportamental central do projeto, pareada com `cambio_brl_usd` pra testar a hipótese "Poupador Assustado".

| # | Item | Achado |
|---|---|---|
| 1 | Duplicatas (chave e linha inteira) | 0 duplicatas de linha inteira, 0 duplicatas de `date` |
| 2 | Colunas constantes / quase constantes | Nenhuma |
| 3 | Valores sentinela em numéricas | Nenhum `0`/`-1`/`9999` |
| 4 | Códigos de ausência mascarados | N/A — sem coluna categórica |
| 5 | Outliers implausíveis (critério relacional) | **ACHADO CRÍTICO, CORRIGIDO 2026-08-09: `usdc_volume` em 2022-01-26 (83,25 trilhões) e 2022-01-29 (77,94 trilhões) — >80x a mediana da série (~4,9 bilhões), em 2 dias, não 1 (checagem inicial por `nlargest` só achou o 2º; scan sistemático por limiar de mediana achou os dois).** Não é evento de mercado real — erro de coleta/unidade da API yfinance. Propagava pra `stablecoin_vol_total` (soma) e pra `usdc_volume_mm30`/`stablecoin_vol_total_mm30` (médias móveis) por ~30 dias, distorcendo qualquer feature de tendência calculada nessa janela. **Corrigido**: as duas células viraram nulo na fonte (`src/coletar_dados.py`, documentado no código pra sobreviver a re-coleta), colunas derivadas recalculadas — `usdc_volume_mm30` máximo caiu de ~3,2 trilhões pra ~12,4 bilhões, escala compatível com o resto da série |
| 6 | Perfil de nulos por coluna | 0 nulos em todas as 9 colunas |
| 7 | Redundância entre colunas | `stablecoin_vol_total` = `usdt_volume` + `usdc_volume`, exatamente (diferença máxima 0 em todas as linhas) — soma determinística, não é sinal independente |
| 8 | Relação de cada bloco com o alvo | Sem alvo formal neste dataset — ele É a variável comportamental (proxy de demanda por hedge) que o projeto tenta explicar com câmbio/macro. `usdt_close`/`usdc_close` ficam sempre perto de 1,00 (peg do dólar) — esperado, não é sinal, é validação de que a stablecoin não despregou |

## Tipos e parsing

- `date`: string ISO, 100% parseável.
- `usdt_volume`, `usdc_volume`, `stablecoin_vol_total`: `int64`. Demais: `float64`.

## Conclusão

**Corrigido em 2026-08-09** (item 5). Antes de corrigir, checou-se se o outlier afetava algum número já reportado: `src/analise_correlacao.py` e `src/recalcular_irf.py` (calibração do IRF v2, R²=0,72 do ADR-0003) usam só `usdt_volume` — nunca tocam `usdc_volume`/`stablecoin_vol_total`. O outlier não mudava nenhuma métrica publicada; a correção foi só higiene de dado, pra quando essas colunas forem usadas em feature nova.
