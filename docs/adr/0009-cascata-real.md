# ADR-0009: Cascata real (reporte separado de suspeita, C3 só onde o modelo acusa sem regra)

**Data:** 2026-10-23
**Status:** Accepted
**Proposto por:** Luiz Maibashi
**Contexto:** `src/pipeline_compliance.py` (`camada1_filtros_bcb`, `inferir_score`, `executar_pipeline`). Origem: `docs/revisao/2026-10-REVISAO.md` §2.1-2.4

## Contexto

A cascata do `PROBLEM.md` ("C1 libera o verde, C2 vê o resto, C3 julga a zona cinza") não é a que o código executa:

- `c1_flag` mistura R1/R2 (reporte obrigatório por valor e volume) com R3-R6 (suspeita comportamental). Todos os 2.030 casos de institucional legítimo caem em R1/R2, e a Camada 1 sinaliza 74% das transações.
- A zona cinza é `c2_score` entre 40 e 70 em qualquer linha, com ou sem regra. 82 dos 1.164 casos cinza são de poupador sem nenhuma regra.
- `c3_veredito` não entra em `score_final`, na API nem no app.
- `score_final = 0,6·C2 + 16·C1` nunca passa de 76, e os buckets VERDE/AMARELO/VERMELHO não correspondem a nenhuma decisão escrita.

## Decisão

1. **Separar dois canais na Camada 1:**
   - `c1_reporte` (R1, R2): obrigação de comunicar por valor ou volume. **Não é suspeita** e não acende alerta sozinho.
   - `c1_suspeita` (R3, R4, R5, R6): regra de comportamento.
   - `c1_flag` e `c1_razoes` continuam existindo, com o mesmo significado de hoje (OR de tudo), por compatibilidade com o app, a API e o site.
2. **C2 roda em todas as transações.** O Isolation Forest custa praticamente zero por linha. Restringir C2 ao que C1 flagou criaria uma cegueira estrutural: uma fraude fora da regra nunca seria vista pelo modelo, e é exatamente isso que o gerador v2 (ADR-0011) vai testar. O degrau caro, que a cascata economiza, é o LLM.
3. **Modelo binário pelo limiar do ADR-0008:** `c2_positivo = c2_score_anomalia ≥ limiar_operacao`. Se o ADR-0008 não achar limiar viável, `c2_positivo = False` em tudo, e o degrau fica desligado.
4. **Tabela de decisão (`decisao_cascata`):**

| `c1_suspeita` | `c2_positivo` | Decisão | `alerta_final` |
|---|---|---|---|
| sim | sim | concordam: suspeito | VERMELHO |
| não | não | concordam: liberado | VERDE |
| sim | não | regra acusa com motivo explícito | AMARELO (fila humana, **sem C3**) |
| não | sim | só o modelo acusa, sem motivo explícito: zona cinza | AMARELO (vai a C3) |

5. **C3 só roda na zona cinza, que é `c2_positivo & ~c1_suspeita`.** Quando a regra acusa, ela já traz o motivo legível (R3-R6), e o analista não precisa do LLM para saber por que o caso está na fila. O LLM só agrega onde o único sinal é um score sem explicação. Enquanto o ADR-0010 (papel do juiz) não for aceito, `c3_veredito` **não muda** `alerta_final`: o caso cinza vai para a fila humana, e o LLM pode preencher o rascunho, mas não decide.

   *Revisado em 2026-10-23, depois da primeira medição.* A versão anterior mandava ao C3 toda discordância, nos dois sentidos. No snapshot (metade de avaliação), o limiar escolhido pelo ADR-0008 foi 98,7. Com isso, 676 dos 688 casos cinza eram "regra sim, modelo não", e a cascata mandava mais casos ao LLM (688) do que a faixa antiga de 40-70 (620). Ou seja: quando o modelo está quase desligado, a discordância nos dois sentidos vira "toda regra acionada vai ao LLM"
6. **`score_final` passa a ser só prioridade de fila** dentro de cada cor. Os buckets por `score_final` deixam de definir a cor.

## Consequências

**Positivas**
- O institucional legítimo deixa de virar alerta só por valor, porque o reporte vai para outro canal. O FP em legítimos deve cair muito em relação aos 25,2% atuais.
- O custo do LLM passa a ser proporcional aos casos sem motivo explícito, não a uma faixa arbitrária de score. Pelo snapshot da primeira medição, a estimativa é de 688 para cerca de 12 chamadas na metade de avaliação.
- A pergunta "cada degrau se paga?" fica mensurável: fracionadores novos por 100 casos cinza.

**Negativas**
- No gerador v1, a regra pega quase tudo, e o C3 deve receber poucos casos e não acrescentar nada. Isso confirma o diagnóstico de circularidade, e o teste real fica para o v2.
- A discordância "regra sim, modelo não" não passa por nenhum degrau extra. Se a regra tiver falso positivo sistemático (no snapshot, institucional de madrugada via R5), quem filtra é o analista humano, não o LLM.
- A cor muda de significado. O `AGENTS.md` (glossário VERDE/AMARELO/VERMELHO), o `app.py`, a API, `deploy/hf_space/` e o site precisam ser alinhados. **Na Fase 2 só o pipeline e a medição mudam.** O snapshot público continua congelado e fica registrado como débito até ser regenerado.
- Um poupador com R1/R2 e modelo positivo ainda cai na zona cinza. Isso é aceito: é um caso em que só o modelo acusa.

## Alternativas descartadas

| Opção | Vantagem | Por que foi rejeitada |
|---|---|---|
| C2 só no que C1 flagou (o desenho original) | Mais barato no papel | Cegueira estrutural para fraude fora da regra, e o custo do C2 é ~0 |
| Estreitar a faixa 40-70 no olho (50-70, 60-70) | Mudança de uma linha | Troca um número arbitrário por outro (revisão §2.4) |
| Manter R1/R2 dentro de `c1_flag` como suspeita | Sem mudança de schema | R1/R2 é obrigação de reporte e gera 2.030 alarmes falsos |
| C3 em toda discordância (regra XOR modelo) | Simétrico | Medido: com o modelo quase desligado, manda ao LLM toda regra acionada (688 contra 620 da faixa antiga) |
| Fazer `c3_veredito` decidir já | Fecha a cascata | O juiz nunca foi avaliado contra gabarito, isso é a Fase 4 e o ADR-0010 |

## Validação

- Teste unitário de `decisao_cascata` cobrindo as 4 linhas da tabela, e o caso `limiar=None`.
- Teste de que R1/R2 sozinhos não geram `c1_suspeita`.
- `src/medir_escada.py` ganha o degrau "cascata (ADR-0009)": precisão, recall, FP por transação e por usuário, tamanho da zona cinza e fracionadores novos por 100 casos cinza.
- Teste de que "regra sim, modelo não" dá AMARELO com `zona_cinza=False`, e de que nenhuma linha com `c1_suspeita=True` chega ao C3.
