# SPEC FINAL — Condições do Veredito da Tese (Shadow FX Terminal)

> Compilado a partir dos 5 tickets Wayfinder em `docs/wayfinder/tese-veredito-condicoes/`. Todos resolvidos em 2026-08-10.

## Contexto (de onde veio)

`docs/tese/shadow-fx-vantagem-competitiva/TESE.md` fechou com veredito **VAI, com 3 condições**: (1) reescrever o pitch com o trade-off explícito, (2) reposicionar como nicho, (3) testar distribuição real. Este Wayfinder decompôs as 3 condições — que na prática viraram 5 blocos, porque a condição 1 dependia de uma decisão técnica anterior não tomada, e a condição 2 dependia de pesquisa que revelou o motivo original errado.

## Decisões tomadas (Tickets 0001-0004)

1. **Trade-off: aceitar e documentar, não tunar** (Ticket 0001). Dataset sintético — tunar sem rótulo real arrisca otimizar pra ruído.
2. **Pitch reescrito com honestidade** (Ticket 0002). `PROBLEM.md` e `README.md` atualizados: número real de falso positivo (1,6%→5,6%), precisão real (35,8%→43,6%), tabela de resultados corrigida (estava desatualizada de antes do fix de calibração desta sessão).
3. **Motivo do nicho corrigido por fato, não descartado** (Tickets 0003+0004). Hipótese original ("exchange pequena não tem orçamento") foi derrubada por fato real: VASP autorizada no Brasil precisa de R$ 10,8mi de capital mínimo por lei — não é startup sem grana. Motivo revisado e mantido: complexidade regulatória brasileira (BCB/COAF, reforma tributária) que incumbente global genérico não prioriza acompanhar de perto. Método explícito do usuário: resolver nicho bem definido primeiro, generalizar depois — não o caminho inverso.
4. **Roteiro de descoberta pronto** (Ticket 0005) — 5 perguntas, ordem deliberada (as 2 primeiras podem matar a conversa cedo), critério de sucesso definido. Execução (a conversa real) é ação humana, fica pendente fora do escopo do agente.

## Fora de escopo (não resolvido aqui)

- **Executar a conversa de descoberta** — roteiro pronto, conversa em si depende do usuário.
- **Reteste da tese em +30 dias** (2026-09-09, campo já registrado em `TESE.md`) — avaliar então se a conversa aconteceu e se algo mudou.

## Atualização (2026-08-11)

O item "reescrever o pitch com a justificativa de nicho corrigida", listado acima como fora de escopo, **foi implementado** — README.md e PROBLEM.md agora têm a narrativa corrigida, reforçada com pesquisa adicional (7 mudanças regulatórias em 18 meses, ausência de investimento dos incumbentes no Brasil, R$388bi de volume — ver Ticket 0003, Adendo). Também consolidada uma 3ª instância do padrão de duplicação de prompt/rascunho COAF, achada em `app.py` num Blind Spot Pass que não tinha sido feito nesse arquivo antes. Único item de fato pendente do bloco inteiro: a conversa real do Ticket 0005.

## Próximo passo (fora do Wayfinder)

Por acordo prévio nesta sessão, o destino depois deste bloco é `/grill-with-docs` — não pra este bloco específico (que fechou), mas pra retomar o objetivo maior da sessão: reconstruir a metodologia do projeto do zero (gerar `AGENTS.md` com Linguagem Ubíqua, aplicar Blind Spot Pass, e ancorar as decisões já tomadas — incluindo esta — em ADRs onde fizer sentido).
