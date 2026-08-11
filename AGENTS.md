# AGENTS.md — Shadow FX Terminal

> **Projeto**: Pipeline de compliance AML para stablecoins com contexto macroeconômico (IRF).
> **Stack**: Python · Pandas · Scikit-Learn · FastAPI · Streamlit · Gemini 2.5 Flash
> Atualizado em 2026-08-11 via `/grill-with-docs` (Blind Spot Pass + sabatina), depois de `/tese` e `/wayfinder` na mesma linha de trabalho. Versão original preservada em espírito; seções novas marcadas.

---

## Mapa do projeto

- `src/` — Código modular de produção (utils, pipeline, API, agente RAG)
- `notebooks/` — 3 notebooks CRISP-DM (correlação, IRF, arena de modelos)
- `app.py` — Dashboard Streamlit (frontend)
- `docs/adr/` — Architecture Decision Records (6 registrados)
- `docs/audit/` — Auditorias (PAVC, auditoria v2)
- `docs/tese/` — Sabatinas de valor/vantagem competitiva (`/tese`)
- `docs/wayfinder/` — Decomposição de escopo nebuloso em tickets (`/wayfinder`)
- `tests/` — Testes unitários (pytest, 3 arquivos)
- `models/` — Artefatos treinados (isolation_forest_v1.joblib, scaler_v1.joblib, score_calibracao_v1.joblib)
- `data/` — Dados brutos e processados (não versionados)

---

## Stack e dependências

- **Backend**: FastAPI (`src/api.py`) — CORS restrito, API key middleware
- **Frontend**: Streamlit (`app.py`) — dark mode, responsivo
- **ML**: Isolation Forest (scikit-learn) — detecção de anomalias
- **LLM**: Gemini 2.5 Flash — Camada 3 (LLM-as-Judge), opcional, implementada em `agente_rag.py` + `executar_camada3_llm()`
- **Container**: Docker + Docker Compose (non-root user)

---

## Linguagem Ubíqua (termos do domínio)

| Termo | Significado NESTE projeto (não genérico) |
|-------|-------------|
| **IRF** | Índice de Risco Fiscal (0-100). v1 (3 sinais, legado) e v2 (6 sinais, produção) coexistem — `irf_contexto` usa sempre v2. Não é métrica de risco de crédito nem de mercado — resume "quão hostil está o cenário macro brasileiro hoje", injetado como feature de ML. |
| **Smurfing** | Fracionamento de transações para fugir de limites regulatórios. |
| **Poupador Assustado** | Comprador legítimo de USDT como hedge contra desvalorização do Real. É quem o projeto existe pra **não** incomodar — e é o perfil que mais sofre o trade-off medido (falso positivo 1,6%→5,6% com IRF, ver `TESE.md`). |
| **Fracionador** | Perfil suspeito: estrutura múltiplas transações abaixo de R$10k pra evitar reporte. É quem o projeto existe pra pegar. |
| **Compliance** | Não é "seguir regra" — é decidir, por transação, se precisa de atenção humana, em 3 camadas de custo crescente. |
| **Risco** | Probabilidade de evasão de divisas ou lavagem — nunca "risco de mercado"/"risco de crédito". |
| **Score contextual** | Score de anomalia que muda de significado dependendo do cenário macro do dia (via IRF), não um score fixo por padrão de transação isolado. |
| **Camada 1** | Filtros determinísticos das Resoluções BCB 519-521/2026 (R1-R5). |
| **Camada 2** | Isolation Forest com IRF como feature contextual. |
| **Camada 3** | LLM-as-Judge com RAG temporal (atas do Copom) — implementada, ativa via `LLM_JUDGE_ENABLED=true` + `GEMINI_API_KEY`. |
| **VERDE / AMARELO / VERMELHO** | Classificação final por `score_final` (buckets 0-40/40-70/70-100). Não confundir com `c2_classificacao` (normal/cinza/suspeito), saída intermediária só da Camada 2. |
| **wallets_unicas** | Contagem de wallets distintas **por dia** (regra R3). Não confundir com `entropia_wallets` (dispersão no histórico inteiro do usuário — escopo diferente). |
| **COAF** | Conselho de Controle de Atividades Financeiras. |
| **RIF/RAS** | Relatório de Inteligência Financeira / Relatório de Atividade Suspeita. |

---

## Regras de engenharia

- **FEATURES_ML** centralizado em `utils.py` — nunca duplicar.
- **IRF_LAG_DAYS=14** — lag obrigatório para evitar data leakage macro (macrovariáveis como IPCA/Selic/Dívida-PIB são publicadas com semanas de atraso; usar IRF do dia exato da transação vazaria informação futura).
- **LLM_JUDGE_ENABLED=false** por padrão — ativar via `.env` com `GEMINI_API_KEY`.
- **Non-root** no Docker — `USER appuser`.
- Testes: `pytest tests/ -v` — 3 arquivos (`test_utils.py`, `test_pipeline_compliance.py`, `test_agente_rag.py`).
- Logs em `pipeline.log` (não versionado).
- **Normalização de score do Isolation Forest**: calibrada empiricamente (p1/p99) no treino, salva em `models/score_calibracao_v1.joblib` — nunca hardcodear range fixo (`carregar_calibracao_score()`/`normalizar_score_anomalia()` em `pipeline_compliance.py` são a fonte única, usada tanto no pipeline batch quanto na API).

---

## Restrições técnicas confirmadas (Sabatina 2026-08-10/11)

- **Maior restrição hoje: dado sintético.** Nenhuma validação usa transação real — `gerador_transacoes_mock.py` gera com seed fixa, rótulos conhecidos por construção. Métricas de precisão/recall em `TESE.md` são contra esse rótulo sintético, não produção.
- **Sem banco de dados** — CSV + joblib em memória no startup da API (ADR-0006, decisão consciente, não bug).
- **Sem persistência de histórico por usuário** — a API não verifica a regra R2 (volume 30 dias) por transação isolada; só o pipeline batch consegue.

## Escopo negativo (o que decidimos conscientemente não fazer)

- **Não virar produto ainda.** O projeto é prova de competência metodológica, não aposta de receita (ver `TESE.md`, eixo 4).
- **Não tunar o modelo pra reduzir o trade-off de falso positivo** sem dado real (Ticket 0001 do Wayfinder).

## Métrica de sucesso e cenário de falha (Falsificabilidade)

Herdado de `TESE.md`: **a tese/projeto "falha" se, medido contra o rótulo de verdade do dataset sintético, o IRF não melhorar a precisão em relação a rodar sem ele.** Testado com `IRF_LAG_DAYS=14` aplicado corretamente (2026-08-11): precisão 35,9%→45,2%, recall 34,4%→43,9%, falso positivo em poupador legítimo 1,5%→3,5% (2,3x, não 3,5x como no teste inicial com vazamento). Critério de morte não disparou — veredito "VAI" confirmado com o número correto.

---

## ADRs registrados

| ADR | Decisão |
|-----|---------|
| 0001 | Isolation Forest vs LOF vs One-Class SVM |
| 0002 | Gemini 2.5 Flash como LLM-as-Judge |
| 0003 | IRF v2 com 6 sinais ortogonais |
| 0004 | FastAPI + Streamlit como stack de deploy |
| 0005 | Coletores descentralizados, sem orquestrador central |
| 0006 | Persistência em CSV/joblib em memória (não migrar pra banco agora) |

---

## Débitos técnicos conhecidos

1. Dados em memória (DataFrame) — não escala para milhões de transações. *(aceito conscientemente via ADR-0006)*
2. Sem CI/CD robusto (linting/mypy) — `pytest` roda, mas sem gate automatizado de qualidade.
3. Sem banco de dados — dados voláteis entre restarts. *(mesmo débito do item 1, ADR-0006)*
4. ~~Timestamps malformados sem try/except no pipeline~~ — **parcialmente corrigido (2026-08-11)**: coluna `hora` dessincronizada do timestamp real em transações fracionadas (`gerador_transacoes_mock.py`) foi corrigida. Validação defensiva (try/except) em parsing de timestamp malformado de fonte externa continua em aberto.
5. `preparar_prompt_llm` duplicado no pipeline (deve migrar para agente RAG) — **não é o mesmo item** do bug de duplicação entre `api.py`/`pipeline_compliance.py` corrigido em 2026-08-11 (esse foi consolidado numa função única); este item 5 é sobre organização arquitetural (onde a função deveria morar), ainda em aberto.
6. **[novo, 2026-08-11]** Thresholds de normalização do IRF v2 (`calcular_irf_v2` em `utils.py`) são constantes hardcoded calibradas uma vez sobre 2022-2025 — mesma categoria de fragilidade que o bug de calibração do Isolation Forest (já corrigido). Fix: recalcular percentis a cada atualização de dado e versionar como artefato.

### Corrigidos em 2026-08-11 (Blind Spot Pass + reconciliação com histórico real)

- Regra R2 (`camada1_filtros_bcb`) usava janela de 30 *transações*, não 30 dias calendário — corrigido com `.rolling("30D")`.
- `api.py`: schema `TransacaoInput` não declarava `hora` nem `wallets_unicas`, mas o endpoint `/compliance/score` os usava — causava `AttributeError` garantido. Corrigido.
- `api.py`: normalização de score e prompt do LLM-as-judge duplicados e divergentes do `pipeline_compliance.py` — consolidados em fonte única.
- `api.py`: texto de razão do C1 (XAI) só checava 2 das 5 regras reais — agora cobre R1/R3/R4/R5; R2 documentado como não-verificável sem histórico do usuário.
- Bug de calibração do score do Isolation Forest (range hardcoded `-0.5/0.5` não batia com a distribuição real) — corrigido com calibração empírica (p1/p99) salva como artefato.

---

## Artefatos de raciocínio (não código, mas parte do produto)

- `docs/tese/shadow-fx-vantagem-competitiva/TESE.md` — sabatina de valor: o projeto ganha vantagem competitiva real frente a Chainalysis/TRM/Elliptic? Veredito: VAI, com 3 condições — **números em processo de recálculo com `IRF_LAG_DAYS` aplicado corretamente**.
- `docs/wayfinder/tese-veredito-condicoes/` — decomposição das 3 condições em 5 tickets, todos resolvidos, `SPEC_FINAL.md` compilado.
- Este arquivo (`AGENTS.md`) — mesclado via `/grill-with-docs` em cima do original.

## Referências externas citadas nas decisões

- Resoluções BCB 519, 520, 521/2025 (vigor fev/2026) — cria a obrigação legal de AML pra VASPs.
- Capital mínimo pra VASP: R$ 10,8 milhões (fonte: NDM Advogados).
- Preço de mercado dos incumbentes: Chainalysis US$50-200K/ano, TRM Labs €60-150K/ano, Elliptic €80-180K/ano (fonte: Costbench, Finconduit).
