---
tipo: tarefa-simples
status: resolvido
criado: 2026-08-10
---

# Ticket 0002: Reescrever README/PROBLEM.md/audit_report com o trade-off explícito

## Bloqueio

Depende do resultado do Ticket 0001 (tunar ou aceitar). Depois de resolvido, é execução direta: atualizar os textos que hoje vendem "distingue poupador de fracionador" sem qualificar o custo, pra refletir o número real (seja o original 1,6%→5,6%, seja o número pós-tuning).

## Resultado

Reescrito em 2026-08-10:
- `PROBLEM.md` — nova seção "⚠️ Trade-off Real Medido" com a tabela completa (precisão/recall/falso positivo) e link pra `TESE.md`; tabela de Valor de Negócio qualificada.
- `README.md` — 3 pontos: (1) linha 86-88 (Ponto de Virada) referencia o trade-off em vez de prometer solução sem custo; (2) seção "Fase 3 — Motor de Compliance" com números corrigidos (a tabela antiga estava desatualizada, de antes do fix de calibração desta sessão — 3.936/564/9 → 3.053/1.364/92) e narrativa do Tipo A com o número real de falso positivo; (3) linha 150 (nota regulatória) parava de "garantir zero exclusão" e passou a citar o número medido.
