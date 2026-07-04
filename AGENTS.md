# AGENTS.md — Shadow FX Terminal

> **Projeto**: Pipeline de compliance AML para stablecoins com contexto macroeconômico (IRF).
> **Stack**: Python · Pandas · Scikit-Learn · FastAPI · Streamlit · Gemini 2.5 Flash

---

## Mapa do projeto

- `src/` — Código modular de produção (utils, pipeline, API, agente RAG)
- `notebooks/` — 3 notebooks CRISP-DM (correlação, IRF, arena de modelos)
- `app.py` — Dashboard Streamlit (frontend)
- `docs/adr/` — Architecture Decision Records (4 registrados)
- `docs/audit/` — Auditorias (PAVC, auditoria v2)
- `tests/` — Testes unitários (pytest)
- `models/` — Artefatos treinados (isolation_forest_v1.joblib)
- `data/` — Dados brutos e processados (não versionados)

---

## Stack e dependências

- **Backend**: FastAPI (`src/api.py`) — CORS restrito, API key middleware
- **Frontend**: Streamlit (`app.py`) — dark mode, responsivo
- **ML**: Isolation Forest (scikit-learn) — detecção de anomalias
- **LLM**: Gemini 2.5 Flash — Camada 3 (LLM-as-Judge), opcional
- **Container**: Docker + Docker Compose (non-root user)

---

## Linguagem Ubíqua (termos do domínio)

| Termo | Significado |
|-------|-------------|
| **IRF** | Índice de Risco Fiscal (0-100), v2 com 6 sinais macroeconômicos |
| **Smurfing** | Fracionamento de transações para fugir de limites regulatórios |
| **Poupador Assustado** | Comprador legítimo de USDT como hedge contra desvalorização do Real |
| **Camada 1** | Filtros determinísticos das Resoluções BCB 519-521/2026 |
| **Camada 2** | Isolation Forest com IRF como feature contextual |
| **Camada 3** | LLM-as-Judge com RAG temporal (atas do Copom) |
| **COAF** | Conselho de Controle de Atividades Financeiras |
| **RIF/RAS** | Relatório de Inteligência Financeira / Relatório de Atividade Suspeita |

---

## Regras de engenharia

- **FEATURES_ML** centralizado em `utils.py` — nunca duplicar
- **IRF_LAG_DAYS=14** — lag obrigatório para evitar data leakage macro
- **LLM_JUDGE_ENABLED=false** por padrão — ativar via `.env` com `GEMINI_API_KEY`
- **Non-root** no Docker — `USER appuser`
- Testes: `pytest tests/ -v` — 54+ testes
- Logs em `pipeline.log` (não versionado)

---

## ADRs registrados

| ADR | Decisão |
|-----|---------|
| 0001 | Isolation Forest vs LOF vs One-Class SVM |
| 0002 | Gemini 2.5 Flash como LLM-as-Judge |
| 0003 | IRF v2 com 6 sinais ortogonais |
| 0004 | FastAPI + Streamlit como stack de deploy |

---

## Débitos técnicos conhecidos

1. Dados em memória (DataFrame) — não escala para milhões de transações
2. Sem CI/CD — testes precisam ser manuais
3. Sem banco de dados — dados voláteis entre restarts
4. Timestamps malformados sem try/except no pipeline
5. `preparar_prompt_llm` duplicado no pipeline (deve migrar para agente RAG)
