# ADR-0002: Gemini 2.5 Flash como LLM-as-Judge (Camada 3)

**Data**: 2026-05-17
**Status**: Accepted
**Proposto por**: Luiz Maibashi
**Contexto**: Shadow FX Terminal — Camada 3 do pipeline de compliance

---

## 1. CONTEXTO (O QUÊ?)

Transações classificadas como "zona cinza" (score ML entre 40-70) precisam de julgamento qualitativo para determinar se são suspeitas de lavagem de dinheiro ou evasão de divisas. A decisão precisa considerar o contexto macroeconômico (atas do Copom, IRF).

**Restrições técnicas:**
- Cobertura: ~0.2% das transações (os casos mais ambíguos) — volume baixo
- Latência tolerável: até 5s (não é tempo real)
- Precisa gerar rascunho de relatório COAF (RIF) em linguagem natural
- Orçamento: ~$0.15/tera de inferência (custo deve ser mínimo dado o baixo volume)
- Privacidade: dados de transação NÃO podem sair do Brasil (LGPD)

---

## 2. DECISÃO (POR QUÊ?)

**O que escolhemos:**
Gemini 2.5 Flash (Google AI) com RAG temporal (atas do Copom injetadas como contexto).

**Razão principal (ROI statement):**
"Gemini 2.5 Flash oferece o menor custo por chamada ($0.03/1M tokens) entre os LLMs com qualidade suficiente para análise de compliance, tem janela de contexto de 1M tokens (cabe o histórico completo do Copom), e o SDK google-genai é nativamente Python — zero custo de integração."

**Por que não outros provedores:**
- OpenAI GPT-4o: 10x mais caro ($0.30/1M tokens) sem ganho de qualidade para este domínio específico
- Claude 3.5 Sonnet: excelente para análise jurídica, mas 5x mais caro e sem garantia de disponibilidade na América do Sul
- Modelo local (Llama 3): exigiria GPU on-prem, custo de infra > $200/mês para 0.2% do volume

---

## 3. CONSEQUÊNCIAS

**Positivas (Wins):**
- Custo operacional mínimo: ~$0.10/mês para o volume estimado (30-50 casos cinza/mês)
- RAG temporal com atas do Copom funciona sem banco vetorial (busca linear por data é suficiente)
- Fallback heurístico já implementado para degradação graciosa
- Resposta estruturada (VEREDITO + JUSTIFICATIVA + RASCUNHO COAF) facilita parse

**Negativas (Custo/Risco):**
- Dados de transação trafegam para servidores Google (risco LGPD mitigado: dados são pseudonimizados, sem PII explícita)
- Dependência de API externa — indisponibilidade de serviço cai no fallback
- Gemini 2.5 Flash pode ter viés de "falso positivo" em compliance (tendência a ser conservador)
- LLM é chamado standalone (agente_rag.py), não integrado no pipeline principal

**Timeline:**
- Implementação: 1 dia
- Integração no pipeline: pendente (ADR-0003 registra esta dívida técnica)

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| **GPT-4o mini** | Boa qualidade/price ratio | ❌ 3x mais caro que Gemini Flash; sem diferença significativa em teste A/B com 20 prompts |
| **Llama 3 70B (local)** | Dados não saem do Brasil | ❌ Requer GPU A10G (~$1.500/mês) para 0.2% do volume — sobre engenharia |
| **Apenas regras heurísticas** | 100% deterministico, sem custo | ❌ Casos cinza são ambíguos por definição — regras não capturam nuance qualitativa |

---

## 5. IMPACTO ROI & VALIDAÇÃO

**Métrica de sucesso:**
- Taxa de acerto vs analista humano: >85% em amostra de 50 casos validados
- Custo mensal: < $1.00
- Latência p95: < 4s por chamada

**Validação:**
- Teste cego com 20 casos rotulados por analista de compliance
- Concordância mínima de 80% entre LLM e analista humano

---

## 6. REFERÊNCIES & LINKS

- `src/agente_rag.py` — Implementação do agente
- `src/pipeline_compliance.py` — Pipeline (Camada 3 preparada, não integrada)
- Google AI: https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash
- Resolução BCB 521/2026 — Obrigatoriedade de reporte ao COAF
