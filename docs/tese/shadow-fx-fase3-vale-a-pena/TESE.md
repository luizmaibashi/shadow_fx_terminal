# Tese: vale gastar mais 1-2 semanas no Shadow FX (Fases 3 e 4)?
**Status:** rascunho (sabatina adiada)
**Aberta:** 2026-10-23 · **Veredito:** 2026-10-23 · **Reteste:** 2026-11-22

## A pergunta

Vale gastar mais 1-2 semanas no Shadow FX (Fase 3: gerador v2 + teste do IRF; Fase 4: eval do juiz LLM), ou o portfólio corrigido (Fases 1-2 + vazamentos, `4603941`) já basta para a vaga-alvo?

## A tese em uma frase

**Não enunciada.** A Fase 1 (socrática) parou no primeiro desbloqueio: o Luiz recebeu o critério vazio (três tipos de pergunta de entrevistador; valor marginal de uma fase = pergunta nova respondida × chance de ser feita na vaga × peso − custo de oportunidade) e decidiu seguir o projeto e responder depois.

## As 5 lentes

Não preenchidas. As predições da Fase 2 do `/tese` só podem ser escritas pelo Luiz; ficam para a retomada.

| Lente | Predição (fase 2) | Análise (fase 3) | Δ |
|---|---|---|---|
| Necessidade | — | — | — |
| Impacto | — | — | — |
| Distribuição | — | — | — |
| Escala | — | — | — |
| ROI | — | — | — |

## Como isso morre

Escrito antes do veredito, a partir de critérios já registrados em `docs/revisao/2026-10-REVISAO.md`:

1. **IRF (§4.3):** falhar em qualquer condição A (placebo com IC contendo zero), B (ganho de recall com limite inferior do IC > 0 no mesmo teto de dano) ou C (FP do poupador em dia de IRF alto não piora mais que +1 p.p.) tira o IRF do pitch como diferencial.
2. **Juiz LLM (§6, Fase 4):** IC do ganho sobre o baseline cruzando zero → juiz vira só redator de RIF.
3. **Tempo (§6):** o corte "se a TC4 apertar, para aqui" continua valendo. Fase 3 orçada em 3-4 dias úteis; se a TC4 (16/11) ou a etapa final da Innoscience pedirem esse tempo, o projeto para no estado publicado (`4603941`), que já é coerente.

## Veredito e destino

**Veredito: VAI, por decisão do Luiz, sem tese enunciada (2026-10-23).**

Ressalva registrada: o checklist da skill (mais de 2 semanas + carreira) pedia a sabatina antes da Fase 3. O Luiz preferiu seguir e responder depois. O risco é gastar 3-6 dias sem saber que pergunta de entrevistador eles respondem; o mitigador é o critério de tempo acima.

**Destino:** Fase 3 começa conferindo os offsets de `src/macro_disponibilidade.py` no calendário IBGE/BCB e escrevendo o ADR-0011 (gerador v2 + placebo); Codex implementa por spec, Claude audita, Luiz aprova push. **Retomar a sabatina** (Fase 1 do `/tese`, a partir da pergunta "qual pergunta do entrevistador a Fase 3 ou 4 responde que hoje fica sem resposta?") antes de iniciar a Fase 4.

## Os 150

Pendente (escrito pelo Luiz).

---
## Delta de raciocínio

Pendente.
