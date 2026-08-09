# ADR-0005: Coletores de Dados Descentralizados — Sem Orquestrador Central

**Data**: 2026-08-09
**Status**: Accepted
**Proposto por**: Luiz Maibashi
**Contexto**: Shadow FX Terminal — Pipeline de coleta de dados (`src/coletar_*.py`)

---

## 1. CONTEXTO (O QUÊ?)

Ao planejar `src/coletar_foxbit.py` (novo coletor, dado Brasil-específico da Foxbit — ver `docs/wayfinder/shadow-fx-dado-brasil-especifico/SPEC_FINAL.md`), surgiu a pergunta: com 5+ coletores agora (`coletar_dados.py` — que já agrupa câmbio/globais/stablecoins/macro —, `coletar_google_trends_br.py`, `scraper_copom.py`, e o novo `coletar_foxbit.py`), faz sentido ter um orquestrador central (`coletar_tudo.py` ou similar) que rode todos com um comando?

---

## 2. DECISÃO (POR QUÊ?)

**O que escolhemos**: manter os coletores como scripts standalone, cada um com seu próprio `if __name__ == "__main__":`, sem orquestrador central. `coletar_foxbit.py` segue o mesmo padrão.

**Razão principal**: os coletores têm perfis de confiabilidade heterogêneos. `coletar_dados.py` (yfinance + `python-bcb`) é rápido e estável. `coletar_google_trends_br.py` usa `pytrends`, API não-oficial, com sleeps deliberados de 30-60s e retry com backoff pra evitar 429 — uma corrida pode levar minutos e falhar por rate limit. Um orquestrador que rodasse os dois em sequência faria a atualização do dado mais crítico (câmbio) depender do sucesso/velocidade do dado mais frágil (Trends), sem necessidade.

"Se não fizermos isso: nada muda — o padrão atual (rodar cada coletor manualmente conforme necessário) continua funcionando, sem dor registrada."
"Se fizéssemos um orquestrador: ganharíamos um comando único, mas herdaríamos acoplamento entre fontes com perfis de falha incompatíveis, sem ganho medido."

---

## 3. CONSEQUÊNCIAS

**Positivas (Wins):**
- Falha ou lentidão de uma fonte (ex. Trends com 429) não bloqueia nem atrasa as demais.
- Cada coletor continua idempotente e re-executável isoladamente, como hoje.
- Zero código novo de coordenação/estado pra manter.

**Negativas (Custo/Risco):**
- Atualizar o dataset completo exige rodar N scripts manualmente, não 1 comando.
- Risco de esquecer de rodar um coletor ao atualizar a base (mitigado: cada dataset tem gate de EDA/dicionário no CRISP-DM da base de conhecimento, que avisa se faltar cobertura — mas não avisa se o CSV está desatualizado, só se está ausente).

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| **Orquestrador central (`coletar_tudo.py` chamando todos os `main()`)** | 1 comando pra atualizar tudo | Acopla fonte rápida/estável a fonte lenta/frágil sem necessidade; nenhuma dor documentada em `AGENTS.md` (5 débitos técnicos listados, nenhum é "falta orquestrador") pede isso — construir sem dor real é overengineering |
| **Orquestrador com paralelismo + retry compartilhado** | Mais rápido, mais robusto | Complexidade desproporcional ao problema — nenhum dos coletores atuais roda com frequência alta o suficiente pra justificar |

---

## 5. IMPACTO ROI & VALIDAÇÃO

**Métrica de sucesso**: nenhuma mudança de comportamento esperada — é decisão de *não fazer*. Sucesso = essa pergunta não voltar a ser levantada sem um gatilho novo (dor real documentada).

**Gatilho pra revisitar**: se a atualização manual de múltiplos coletores virar dor registrada (ex. dataset desatualizado em produção por esquecimento), reabrir esta decisão — trade-off muda se houver evidência de custo real, não hipotético.

---

## 6. REFERÊNCIAS & LINKS

- `docs/wayfinder/shadow-fx-dado-brasil-especifico/SPEC_FINAL.md` — contexto que originou a pergunta (novo coletor Foxbit)
- `AGENTS.md` — lista de débitos técnicos conhecidos (não inclui este item)
- `src/coletar_dados.py`, `src/coletar_google_trends_br.py` — padrão atual de coletor standalone
