# Predição da Fase 3 (registrada antes da medição)

**Data:** 2026-10-23 · **Quem:** Luiz Maibashi · **Medição:** `src/medir_irf.py` (ADR-0011), ainda não rodada em tamanho real quando isto foi escrito.

| Pergunta | Predição do Luiz (literal) | Leitura registrada |
|---|---|---|
| Recall de fracionador no v2, com IRF − sem IRF | "cerca de 10%" | +10 p.p. |
| FP do poupador nos dias de IRF alto, com − sem | "sobe cerca de 5%" | +5 p.p. |
| Condições que passam | "B" | B passa; A e C falham |

Implicação da predição: o IRF ganharia recall (B), mas o placebo também mostraria ganho (A falha, ou seja, parte do efeito seria do método e não do macro), e o poupador seria mais incomodado nos dias de estresse (C falha). Pelo critério de abandono, isso tiraria o IRF do pitch como diferencial.

## Resultado

Pendente. O delta (onde bateu, onde não e por qual mecanismo) entra aqui depois da medição.
