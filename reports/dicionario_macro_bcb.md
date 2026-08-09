# Dicionário de colunas — macro_bcb

Fonte: `data/raw/macro_bcb.csv`. EDA em `reports/eda_macro_bcb.md`.

## Colunas (pós-limpeza)

| Coluna | Tipo | Significado | Interpretação de negócio |
|---|---|---|---|
| `date` | string ISO | Data de referência | Chave temporal |
| `ipca_mensal` | float64 | Inflação mensal (%) | Ritmo de alta de preços no curto prazo |
| `selic_meta` | float64 | Taxa básica de juros (%) | Custo do dinheiro — Selic alta reduz atratividade de ativos de risco (inclusive cripto) |
| `ibc_br` | float64 | Índice de Atividade Econômica do BC | Proxy de PIB mensal — atividade fraca é sinal #6 do IRF v2 (peso 10%) |
| `divida_bruta_pib` | float64 | Dívida bruta do governo geral / PIB (%) | Sinal #1 do IRF v2 (peso 30%, r=+0,707) — o preditor mais forte de demanda por USDT no projeto |
| `expectativa_ipca_12m` | float64 | Expectativa de mercado (Focus/BCB) pra inflação nos próximos 12 meses | Sinal de inflação **esperada**, não realizada |
| `ipca_acum_12m` | float64 | Inflação acumulada em 12 meses (%) | Ritmo de alta de preços no médio prazo — mesma informação de `desvio_meta_ipca` (ver EDA, item 7) |
| `desvio_meta_ipca` | float64 | `ipca_acum_12m` menos a meta do Copom (3%) | Sinal #3 do IRF v2 (peso 15%) — dominância fiscal / inflação desancorada |

## Conexão com objetivo de negócio

Doc de origem: `docs/adr/0003-irf-v2-seis-sinais.md`. Sabatina rodada em 2026-08-09 pra resolver um ponto que o ADR deixava em aberto (achado no EDA, item 8): `selic_meta` e `expectativa_ipca_12m` não aparecem na tabela de 6 sinais do ADR — checar se são coleta órfã ou uso legítimo fora do índice.

**Resultado da checagem no código** (não precisou perguntar ao usuário, resolvido por grep):
- `divida_bruta_pib` → sinal #1 (30%), `desvio_meta_ipca`/`ipca_acum_12m` → sinal #3 (15%), `ibc_br` → sinal #6 (10%). Confirma ADR.
- `selic_meta` **é usada** — entra na seleção de colunas de `carregar_dataset_mestre()` (`src/utils.py:350`) e em `analise_correlacao.py`, mas fora dos 6 sinais formais do IRF v2. Papel: análise exploratória de correlação, não index final. ADR-0003 não está errado, só não documentou esse uso secundário.
- **`expectativa_ipca_12m` não é usada em lugar nenhum além da coleta** (`src/coletar_dados.py`) — não aparece em `utils.py`, `analise_correlacao.py`, nem em nenhum notebook. É dado coletado e não consumido.

**Hipótese que este dataset testa**: risco fiscal estrutural (dívida, inflação, atividade) como preditor de demanda por USDT — parte central do IRF v2, que é a camada de contexto do modelo de anomalia (Camada 2).

**Colunas candidatas a feature**: `divida_bruta_pib`, `desvio_meta_ipca` (ou `ipca_acum_12m` — não os dois), `ibc_br` já são feature via IRF v2. `selic_meta` é candidata a feature adicional fora do índice, se a correlação exploratória sustentar. `expectativa_ipca_12m` é candidata **não confirmada** — ver "Features criadas" abaixo.

## Features criadas

Nenhuma criada por nós — os sinais do IRF v2 já vêm calculados em `src/utils.py`, não fazem parte deste dicionário (são código, não coluna de CSV). `expectativa_ipca_12m` é um caso de dado coletado sem feature correspondente — decisão de descontinuar a coleta ou criar a feature fica pra sabatina de arquitetura do projeto, fora do escopo deste dicionário.
