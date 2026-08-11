---
tipo: grilling
status: resolvido
criado: 2026-08-10
---

# Ticket 0004: O projeto assume publicamente a narrativa de nicho, ou mantém neutro?

## Bloqueio

Depende do achado do Ticket 0003. Mesmo com o fato confirmado, existe uma escolha de posicionamento que só o usuário faz: reescrever o README/PROBLEM.md pra declarar explicitamente "isso é pra exchange pequena/média, não pra competir com Chainalysis" (aposta editorial forte, mais honesta, mas reduz o "tamanho do sonho" do pitch) — ou manter a linguagem atual mais ambiciosa/neutra e deixar o reposicionamento implícito só na análise técnica (`docs/tese/`), sem reescrever a cara do projeto.

Isso é decisão de como o projeto quer se apresentar pra recrutador/avaliador, não é fato técnico.

## Resultado

**Opção A (ajustada) — Manter nicho, trocar a justificativa.** Decisão: 2026-08-10.

Justificativa do usuário: não é preço (o fato do Ticket 0003 derrubou isso), é que o mercado brasileiro é complexo o suficiente (regulação BCB/COAF específica, reformas tributárias mudando o jogo continuamente) pra incumbentes globais não priorizarem especialização local — é onde eles são genéricos e o Shadow FX pode ser específico. Método explícito: resolver o problema de um nicho bem definido primeiro, só depois pensar em generalizar pro macro — não o caminho inverso (construir genérico e esperar que sirva pro nicho).

**Implicação pro pitch — implementada em 2026-08-11.** README.md (callout logo após "Ponto de Virada") e PROBLEM.md (nova seção "🎯 Vantagem Competitiva") reescritos com a justificativa corrigida ("complexidade regulatória dinâmica", não "orçamento"), reforçada com a pesquisa do Adendo do Ticket 0003 (7 mudanças regulatórias em 18 meses, ausência de evidência de investimento dos incumbentes no Brasil, R$388bi de volume). Ressalva de que segue sendo raciocínio fundamentado, não validação de mercado, mantida explícita nos dois lugares — não escondida atrás da evidência nova.
