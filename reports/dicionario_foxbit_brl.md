# Dicionário de colunas — foxbit_brl

Fonte: `data/raw/foxbit_brl.csv`. EDA em `reports/eda_foxbit_brl.md`.

## Colunas (pós-limpeza)

| Coluna | Tipo | Significado | Interpretação de negócio |
|---|---|---|---|
| `foxbit_usdt_volume` | float64 | Volume diário de USDT negociado na Foxbit, em USDT | Volume real, brasileiro por jurisdição (não proxy global) |
| `foxbit_usdt_close` | float64 | Preço de fechamento USDT/BRL na Foxbit | Câmbio implícito — valida contra `cambio_brl_usd.csv` (mesma faixa, 4,61-6,33 vs 4,59-6,30) |
| `foxbit_usdt_n_trades` | int64 | Número de negociações de USDT/BRL no dia | Proxy de atividade/liquidez, não só volume — dia com muitos trades pequenos é diferente de poucos trades grandes |
| `foxbit_usdc_volume` | float64 | Volume diário de USDC negociado na Foxbit, em USDC | Idem `foxbit_usdt_volume`, outra stablecoin |
| `foxbit_usdc_close` | float64 | Preço de fechamento USDC/BRL na Foxbit | Idem `foxbit_usdt_close` |
| `foxbit_usdc_n_trades` | int64 | Número de negociações de USDC/BRL no dia | Idem `foxbit_usdt_n_trades` |
| `foxbit_vol_total` | float64 | `foxbit_usdt_volume` + `foxbit_usdc_volume` | Soma determinística (EDA, item 7) — visão agregada de volume stablecoin BR na Foxbit |

## Conexão com objetivo de negócio

Doc de origem: `docs/wayfinder/shadow-fx-dado-brasil-especifico/SPEC_FINAL.md` — sabatina completa já feita lá (Tickets 0001-0004), incluindo grill-with-docs de 2026-08-09 que decidiu escopo e critério de sucesso. Não repete sabatina aqui.

**Hipótese testada**: volume real negociado na Foxbit (Brasil-específico, por jurisdição, não proxy) correlaciona com `brl_usd` tão bem ou melhor que o volume global (`usdt_volume`, yfinance) já usado no projeto. Critério de sucesso definido na sabatina: `|r(foxbit_vol_total, brl_usd)| > |r(usdt_volume_global, brl_usd)|`.

**Decisão de integração** (Ticket 0004 do wayfinder): se a hipótese confirmar, o sinal Foxbit **soma** como sinal adicional no pipeline — não substitui o volume global. Comparação dos dois é o próprio argumento de negócio (prova quantitativa da limitação hoje só documentada qualitativamente no dicionário de `stablecoins_yfinance_real`).

**Resultado real da comparação** (`src/comparar_correlacao_br.py`, rodado em 2026-08-09, 907 linhas na interseção das 3 séries):

- `brl_usd` x `foxbit_vol_total` (BR real): r=+0,400, p=0,0000 (Moderada, critério do próprio projeto em `utils.calcular_correlacao_spearman`)
- `brl_usd` x `usdt_volume` (global): r=+0,496, p=0,0000 (Moderada)

**Veredito: Foxbit-BR NÃO superou o sinal global** — critério de sucesso definido na sabatina (`|r(foxbit)| > |r(global)|`) não foi atingido. Mas o resultado não é nulo: r=0,40 é correlação real, significativa, e classificada "Moderada" pelo próprio critério do projeto — só mais fraca que o global (0,496).

**Leitura pro objetivo maior do projeto**: dado que Foxbit é só ~41% do mercado BR (não 100%), uma correlação de 0,40 vs 0,496 do agregado global é um resultado razoável, não uma rejeição da hipótese "dado Brasil-específico importa". Sugere que o volume global já capta bem o comportamento brasileiro (o Brasil pode ser uma fração grande o suficiente do volume USDT/USDC mundial pra já se refletir no agregado), e que uma única exchange, mesmo grande, é amostra parcial demais pra superar isso sozinha. Próximo passo, se a direção for adiante, seria agregar múltiplas exchanges BR (Mercado Bitcoin, Binance BR, etc.) antes de comparar de novo — não descartar a direção com 1 fonte só.

## Features criadas

Nenhuma nesta rodada — escopo definido na sabatina foi só coleta + comparação, sem mexer no IRF v2/ADR-0003 (`docs/wayfinder/shadow-fx-dado-brasil-especifico/0004-integracao-no-pipeline.md`). Resultado negativo (não superou) reforça que não há justificativa ainda pra criar feature nova a partir deste dataset sozinho no índice formal.
