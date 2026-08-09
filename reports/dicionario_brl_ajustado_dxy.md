# Dicionário de colunas — brl_ajustado_dxy

Fonte: `data/raw/brl_ajustado_dxy.csv`. EDA em `reports/eda_brl_ajustado_dxy.md`.

## Colunas (pós-limpeza)

| Coluna | Tipo | Significado | Interpretação de negócio |
|---|---|---|---|
| `date` | string ISO | Data do pregão | Chave temporal, junta com os outros datasets macro |
| `brl_usd` | float64 | Câmbio BRL/USD bruto | Idêntico a `cambio_brl_usd.csv > brl_usd` (ver EDA, item 7) — presente aqui só como insumo do cálculo de ajuste, não é sinal novo |
| `brl_usd_var_30d` | float64 | Variação % de `brl_usd` em 30 dias | Velocidade de desvalorização/valorização do Real, sem isolar causa |
| `dxy` | float64 | US Dollar Index — força do dólar contra cesta de moedas globais (não só BRL) | Mede o "dólar forte no mundo todo", independente do Brasil |
| `dxy_var_30d` | float64 | Variação % do DXY em 30 dias | Velocidade do movimento global do dólar |
| `brl_adj_dxy_30d` | float64 | `brl_usd_var_30d` menos a parte explicada por `dxy_var_30d` — câmbio "limpo" do efeito dólar-forte-global | O número que efetivamente isola risco Brasil — usado no IRF v2 |

## Conexão com objetivo de negócio

Doc de origem: `docs/adr/0003-irf-v2-seis-sinais.md`, sinal #2 (peso 20%, r=+0,521 com demanda USDT). Não precisou de sabatina nova — o ADR já documenta objetivo e uso desta coluna especificamente (diferente de `cambio_brl_usd`, que precisou de sabatina em 2026-08-09 porque o ADR só cobria a versão ajustada, não a bruta).

**Hipótese que este dataset testa**: separar "Brasil ficou mais arriscado" de "dólar subiu no mundo inteiro" — sem esse ajuste, um evento de estresse global (ex. alta de juros americana) dispararia falso positivo de risco fiscal brasileiro. `brl_adj_dxy_30d` é o preditor que entra no IRF v2 pra isso.

**Colunas candidatas a feature**: `brl_adj_dxy_30d` já é a feature final (30% do IRF v2 é dominado por Dívida/PIB, mas este é o 2º maior peso). `brl_usd` e `dxy` brutos não devem virar feature separada aqui — já são insumo consumido dentro de `brl_adj_dxy_30d`, entrar duas vezes infla peso do mesmo sinal sem querer.

## Features criadas

Nenhuma nova neste dataset — `brl_adj_dxy_30d` já vem calculado no CSV bruto (não é feature engineering nosso, é ingestão).
