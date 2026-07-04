# Architecture Decision Records — Shadow FX Terminal

## Index

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [0001](0001-isolation-forest-vs-lof-svm.md) | Isolation Forest como Motor de Detecção | Accepted | 2026-05-17 |
| [0002](0002-gemini-flash-llm-judge.md) | Gemini 2.5 Flash como LLM-as-Judge | Accepted | 2026-05-17 |
| [0003](0003-irf-v2-seis-sinais.md) | IRF v2 com 6 Sinais Ortogonais | Accepted | 2026-05-05 |
| [0004](0004-fastapi-streamlit-architecture.md) | FastAPI + Streamlit como Stack de Deploy | Accepted | 2026-05-10 |

---

## Princípios de Decisão

1. **ROI primeiro**: toda decisão tem custo/benefício quantificado.
2. **Alternativas documentadas**: nenhuma escolha é "óbvia" — mostramos o que foi descartado e por quê.
3. **Risco explícito**: vulnerabilidades e dívidas técnicas são registradas, não escondidas.
4. **Validação testável**: toda decisão tem métrica de sucesso e plano de monitoramento.
