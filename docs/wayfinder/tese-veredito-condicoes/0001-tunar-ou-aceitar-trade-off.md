---
tipo: grilling
status: resolvido
criado: 2026-08-10
---

# Ticket 0001: Tunar o modelo pra reduzir o trade-off, ou aceitar e documentar como está?

## Bloqueio

A tese (`docs/tese/shadow-fx-vantagem-competitiva/TESE.md`) confirmou que o IRF melhora precisão (35,8%→43,6%) e recall (34,4%→48,3%), mas triplica falso positivo em poupador legítimo (1,6%→5,6%). Antes de reescrever qualquer pitch, existe uma decisão técnica anterior não tomada:

**Opção A — Tunar antes de documentar.** Tentar reduzir o falso positivo ajustando o peso do IRF no `score_final` (hoje `c2*0.6 + c1_flag*40*0.4`, com `irf_contexto` dentro do c2) ou os thresholds dos buckets VERDE/AMARELO/VERMELHO, e só então travar o pitch com um trade-off menor.

**Opção B — Aceitar o trade-off como está.** O trade-off é honesto e documentável (número real, não estimativa) — tunar sem critério pode só trocar overfitting num sentido por overfitting no outro, e o dataset é sintético (não há garantia de que otimizar pra ele generaliza pra dado real).

Só o usuário decide isso — é escolha de risco/honestidade de produto, não fato técnico.

## Resultado

**Opção B — Aceitar o trade-off e documentá-lo.** Decisão: 2026-08-10. Justificativa do usuário: dataset é sintético, tunar sem rótulo real de produção corre risco de otimizar pra ruído. O número real (1,6%→5,6% falso positivo, 35,8%→43,6% precisão) fica travado como está e vira input direto do Ticket 0002 (reescrever pitch).
