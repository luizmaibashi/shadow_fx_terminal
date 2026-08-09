# Dicionário de colunas — stablecoins_yfinance_real

Fonte: `data/raw/stablecoins_yfinance_real.csv`. EDA em `reports/eda_stablecoins_yfinance_real.md` — continha outlier crítico em 2 dias (jan/2022), **corrigido em 2026-08-09** na fonte (`src/coletar_dados.py`) e neste CSV.

## Colunas (pós-limpeza)

| Coluna | Tipo | Significado | Interpretação de negócio |
|---|---|---|---|
| `date` | string ISO | Data de referência | Chave temporal |
| `usdt_volume` | int64 | Volume global negociado de USDT (Tether), em USD | Proxy de demanda global por USDT — não é volume brasileiro isolado |
| `usdt_close` | float64 | Preço de fechamento do USDT em USD | Deveria ficar ~1,00 (peg); desvio indica estresse da stablecoin, não do Real |
| `usdt_volume_mm30` | float64 | Média móvel 30d de `usdt_volume` | Suaviza ruído diário |
| `usdc_volume` | int64 | Volume global negociado de USDC, em USD | Mesma leitura de `usdt_volume`, outra stablecoin. Tinha outlier em 2022-01-26 e 2022-01-29 — corrigido (nulo na fonte) |
| `usdc_close` | float64 | Preço de fechamento do USDC em USD | Idem `usdt_close` |
| `usdc_volume_mm30` | float64 | Média móvel 30d de `usdc_volume` | Recalculada pós-correção — escala normal (~12,4 bi máximo, antes chegava a ~3,2 tri) |
| `stablecoin_vol_total` | int64 | `usdt_volume` + `usdc_volume` | Soma determinística — não é sinal independente (EDA, item 7) |
| `stablecoin_vol_total_mm30` | float64 | Média móvel 30d de `stablecoin_vol_total` | Recalculada pós-correção |

## Conexão com objetivo de negócio

Doc de origem: `AGENTS.md` (Linguagem Ubíqua — "Poupador Assustado") + `docs/adr/0002-gemini-flash-llm-judge.md` (contexto do pipeline de compliance).

**Hipótese que este dataset testa**: é a variável dependente informal do projeto — volume de stablecoin é o comportamento que o câmbio (`cambio_brl_usd`) e o risco fiscal (`macro_bcb`) tentam explicar. Sem esse dataset não existe pipeline de compliance: é ele que entra em `carregar_dados_base()` pareado com `brl_usd` pra calcular a correlação central do projeto.

**Ressalva importante que a sabatina levanta**: os volumes aqui são **globais** (todo o mercado USDT/USDC no mundo), não filtrados por transação brasileira. A hipótese "Real desvaloriza → brasileiro compra USDT" pressupõe que uma fração observável do volume global reage ao câmbio brasileiro — mas o dataset não isola essa fração. Isso já é uma limitação conhecida e aceita do projeto (não é bug, é escopo — não há fonte pública de volume USDT segmentado por país), mas fica documentado aqui porque molda o que a interpretação de negócio pode e não pode afirmar.

**Colunas candidatas a feature**: `usdt_volume`/`usdc_volume` (ou o total) pareados com `brl_usd` são a combinação central de todo o projeto. `_mm30` servem pra tendência — já corrigidas, seguras pra uso.

## Features criadas

Nenhuma nova neste dicionário — as `_mm30` já vêm calculadas no CSV bruto.
