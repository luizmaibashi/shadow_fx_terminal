# ADR-0004: FastAPI + Streamlit como Stack de Deploy

**Data**: 2026-05-10
**Status**: Accepted
**Proposto por**: Luiz Maibashi
**Contexto**: Shadow FX Terminal — Frontend e Backend

---

## 1. CONTEXTO (O QUÊ?)

Precisávamos de uma stack para expor o motor de compliance como:
1. **API REST** para integração com sistemas de corretoras (backtest, batch scoring)
2. **Dashboard interativo** para analistas de compliance (visualização, drill-down, geração de relatórios COAF)

**Restrições técnicas:**
- Custo de infra: $0 (container único, sem banco de dados externo)
- Backend e frontend precisam ser independentes (arquitetura desacoplada)
- Dados carregados em memória (DataFrame) — sem banco relacional
- Deploy via Docker Compose (container único)
- Documentação da API deve ser auto-gerada (OpenAPI)

---

## 2. DECISÃO (POR QUÊ?)

**O que escolhemos:**
- **Backend**: FastAPI (uvicorn) — REST API com docs OpenAPI automáticos
- **Frontend**: Streamlit — dashboard reativo com CSS customizado (dark mode)
- **Comunicação**: CORS entre localhost:8000 (API) e localhost:8501 (Streamlit)

**Razão principal (ROI statement):**
"FastAPI é a framework Python mais rápida para APIs (emula performance de Go/Node) com validação Pydantic nativa e docs automáticos — zero custo de documentação. Streamlit permite criar dashboard interativo com ~300 linhas de Python puro, sem precisar de React ou JavaScript, reduzindo o tempo de deploy em 5x vs um frontend tradicional."

---

## 3. CONSEQUÊNCIAS

**Positivas (Wins):**
- FastAPI: docs em `/docs` (Swagger UI) e `/openapi.json` — sem custo de documentação
- Streamlit: dashboard em dark mode profissional com KPIs, gráficos e gerador de relatórios COAF
- CORS configurado com origem restrita (`localhost:8501`) — segurança por padrão
- Container único via Docker Compose — deploy simplificado
- API key validation via middleware (segurança adicional)
- Resposta em JSON validada por Pydantic — contratos explícitos

**Negativas (Custo/Risco):**
- Dados em memória: API reinicia se o container cair (mitigado: dados salvos em CSV)
- Streamlit não é tão customizável quanto React/Vue (limitado para UI complexa)
- CORS permite apenas uma origem — precisa refatorar para deploy multi-domínio
- Sem autenticação de usuário (Streamlit não tem RBAC nativo)
- API key hardcoded como fallback (`shadow-fx-secret-2026` no código fonte — dívida técnica registrada)

**Timeline:**
- Implementação: 2 dias
- Benefit realization: imediato

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| **Flask + React** | Stack mais robusta para produção | ❌ 5x mais tempo de desenvolvimento; React requer bundler, estado, cache — overkill para MVP de compliance |
| **Gradio** | Mais rápido que Streamlit | ❌ Menos customizável visualmente; difícil fazer dark mode profissional; sem API REST independente |
| **Dash (Plotly)** | Excelente para dashboards analíticos | ❌ Mais pesado que Streamlit; curva de aprendizado maior; sem documentação automática |
| **Monolito (Streamlit puro)** | Simples | ❌ Viola separação de responsabilidades; impossível integrar com sistemas externos sem API |

---

## 5. IMPACTO ROI & VALIDAÇÃO

**Métrica de sucesso:**
- Tempo de deploy inicial: < 30 minutos
- Dashboard funcional: 300 linhas Python (vs ~2.000 linhas React equivalentes)
- Documentação da API: automática (zero esforço de escrita)

**Validação:**
- Teste de carga: 100 requisições concorrentes ao endpoint `/compliance/score` — p95 < 50ms
- Dashboard testado em Chrome, Firefox e Edge (cross-browser)

---

## 6. REFERÊNCIES & LINKS

- `src/api.py` — Implementação FastAPI
- `app.py` — Dashboard Streamlit
- `Dockerfile` — Containerização
- `docker-compose.yml` — Orquestração
- FastAPI docs: https://fastapi.tiangolo.com/
