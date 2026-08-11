# Tese: Shadow FX Terminal — vantagem competitiva frente a players estabelecidos (Chainalysis/TRM Labs/Elliptic)

**Status:** viva
**Aberta:** 2026-08-10 · **Veredito:** 2026-08-10 · **Reteste:** 2026-09-09

## A tese em uma frase

O Shadow FX Terminal ganha porque tem abordagem econômica e análise de comportamento humano embutidas, mesmo com Chainalysis/TRM/Elliptic tendo modelo mais robusto, infra, cliente e produto em produção.

## As 5 lentes

| Lente | Predição (fase 2) | Análise (fase 3) | Resultado |
|---|---|---|---|
| Necessidade | Time de operações/compliance de empresa financeira. | Confirmado por regulação real: Resoluções BCB 519-521/2025 (vigor fev/2026) obrigam VASP a ter AML nível bancário e reporte ao COAF. O comprador não é hipotético, é criado por lei. | Acerto. |
| Impacto | Reduz 20% de falso positivo. | Ablação real: 17,3% das transações mudam de classificação com/sem IRF (a magnitude bateu). Mas o teste inicial só provou que muda, não que muda pra melhor. Teste de precisão contra o rótulo de verdade (`tipo_usuario`): precisão sobe de 35,8% para 43,6%, recall de 34,4% para 48,3%, mas o falso positivo em poupador legítimo triplica (1,6% para 5,6%). | Acerto de magnitude, erro de mecanismo — presumi "efeito grande = efeito bom" sem checar a direção; o ganho de precisão é real, mas vem com um trade-off que não estava previsto e que contradiz o pitch central do projeto ("não bloquear o poupador legítimo"). |
| Distribuição | Mandar pra amigos que trabalham na área, pedir visão interna das empresas deles, estudar como abordar alguém do time interno que usaria o modelo. | É pesquisa de descoberta via rede pessoal, não canal de venda repetível. Válido como passo zero — o setor de AML vende por confiança e indicação — mas não escala além de 1 a 3 contatos sem virar canal de verdade. | Resposta incompleta — cobre descoberta, não distribuição em escala. |
| Escala | "Como enxergamos os dados, e entendemos o negócio." | Não respondeu o que muda entre o cliente 1 e o cliente 10, só reafirmou a tese. Achado real ao investigar: o IRF é fiscal-específico do Brasil (Copom, IPCA, dívida/PIB). Escala de graça entre cliente brasileiro, mas cada país novo exige reconstruir o índice do zero — o oposto do modelo global dos incumbentes. | Erro de otimismo — a mesma especificidade que é vantagem hoje é o teto de crescimento internacional. |
| ROI | 2-3 meses de payback pro comprador. | Plausível se o rascunho automático de RIF pro COAF reduzir tempo de analista (o audit report original citava MTTR de 45min para menos de 10s), mas nunca medido com cliente real. | Aposta razoável, não verificada — nem acerto nem erro, é hipótese sem prova. |

## Como isso morre

A tese morre se, ao validar a classificação final contra o rótulo `tipo_usuario`/`eh_fracionamento` do dataset sintético, o IRF não melhorar a precisão em relação ao modelo sem IRF. Se piorar ou empatar, o "efeito grande" (17,3% de mudança de classificação) era só reshuffling, não sinal — e a tese perderia a lente de Impacto, que é a que mais sustenta a Necessidade.

**Testado em 2026-08-10:** precisão sobe de 35,8% (sem IRF) para 43,6% (com IRF), recall sobe de 34,4% para 48,3%. O critério de morte não disparou — a tese sobrevive a este teste.

Achado colateral que o critério original não previu: o falso positivo em poupador legítimo (`A_poupador_legitimo`) triplica com o IRF (1,6% → 5,6%). Isso não mata a tese pelo critério combinado, mas é uma tensão real que precisa entrar no destino.

## Veredito e destino

**Veredito: VAI.**

A tese sobrevive ao teste de falsificação combinado — o efeito do IRF é real e aponta na direção certa, mais precisão, mais recall. A vantagem de "abordagem econômica + comportamental" é defensável no eixo de Necessidade (regulação real cria o comprador) e de Impacto (efeito mensurável, não ruído).

Mas o veredito vem com 3 condições que mudam a direção documentada do projeto, não só o resultado:

1. **O pitch precisa parar de vender "resolve o dilema sem custo".** O README e o PROBLEM.md afirmavam implicitamente que o IRF ajuda a não bloquear o poupador legítimo — o teste mostrou o oposto: o IRF aumenta a chance de bloquear o poupador legítimo, em troca de pegar mais fracionador real. Isso é uma decisão de produto (trade-off precisão-cobertura vs. experiência do usuário legítimo) que precisa ficar explícita, não escondida atrás de "detecta melhor".
2. **A vantagem competitiva real não é "modelo melhor", é auditabilidade + especificidade de nicho, não escala global.** O projeto deveria parar de se posicionar implicitamente contra Chainalysis/TRM/Elliptic em escala e se posicionar como solução pra exchange brasileira pequena ou média que não paga preço enterprise — consistente com o teto de escala encontrado (o IRF é Brasil-específico).
3. **Falta o teste de distribuição real.** A resposta de "amigos no setor" precisa virar pelo menos uma conversa real documentada antes de a tese poder alegar "sei como vender isso".

**Destino:** o próximo passo é o `/wayfinder` pra decompor essas 3 condições em ticket concreto — reescrever o pitch com trade-off explícito, reposicionar contra nicho não-enterprise, rodar uma conversa de descoberta real. Não é mais um problema de "a tese vale", é um problema de "o que construir ou ajustar agora que a tese está validada com ressalva".

## Adendo — recálculo com IRF_LAG_DAYS corrigido (2026-08-11)

Os números acima foram calculados numa máquina cuja cópia local do projeto não tinha `.git` e estava incompleta — faltava `IRF_LAG_DAYS = 14`, o lag anti-vazamento de dado que já existia no histórico real do GitHub (`utils.py`), sem o qual o modelo via dado macro (IPCA/Selic/dívida-PIB) do dia exato da transação — informação que na vida real só é publicada semanas depois.

Recalculado com o lag correto, contra o mesmo rótulo de verdade:

| Métrica | Sem IRF | Com IRF (vazando, número antigo) | Com IRF (`IRF_LAG_DAYS=14`, correto) |
|---|---|---|---|
| Precisão | 35,9% | 43,6% | 45,2% |
| Recall | 34,4% | 48,3% | 43,9% |
| Falso positivo (poupador legítimo) | 1,5% | 5,6% (3,5x) | 3,5% (2,3x) |
| Transações que mudam de classificação | — | 17,3% | 16,9% |

O veredito não muda — o achado central sobrevive à correção, e o trade-off é até menos severo do que a versão com vazamento sugeria (custo 2,3x, não 3,5x). O critério de falsificação da linha acima continua não disparando: precisão e recall melhoram com o lag correto, na mesma direção.

Isso não invalida a tese, mas é um lembrete do próprio "delta de raciocínio" abaixo: um número que parece confirmar a predição pode estar certo por acidente metodológico, não por mecanismo — vale sempre checar se o pipeline que gerou o número tinha as mesmas salvaguardas que o projeto real já tinha implementado.

## Adendo 2 — recálculo com calibração do IRF v2 corrigida (2026-08-11)

Ao corrigir o débito técnico "thresholds hardcoded do IRF v2" (mesma categoria de fragilidade do bug de calibração do Isolation Forest, já corrigido — ver `AGENTS.md`), descobri que o threshold de IPCA estava chumbado em 4.5, mas o valor real calibrado empiricamente (p95 sobre 2022-2025) é 11,4 — 2,5x maior. O sinal de IPCA estava saturando com muito mais facilidade do que o dado real justifica, distorcendo o IRF v2 pra cima.

Corrigido e recalculado (`dataset_irf_completo.csv` regenerado, modelo retreinado, ablação rerodada):

| Métrica | Sem IRF | Adendo 1 (lag corrigido, calibração ainda hardcoded) | Adendo 2 (lag + calibração corrigidos) |
|---|---|---|---|
| Precisão | 35,9% | 45,2% | 44,8% |
| Recall | 34,4% | 43,9% | 49,9% |
| Falso positivo (poupador legítimo) | 1,5% | 3,5% (2,3x) | 5,0% (3,3x) |
| Transações que mudam de classificação | — | 16,9% | 18,3% |

O veredito continua não mudando — precisão e recall seguem melhorando com o IRF, o critério de falsificação não dispara. Mas repare que o custo do falso positivo subiu de novo (2,3x → 3,3x), quase de volta ao número da versão com vazamento de dado (3,5x). Não é contradição, é o que acontece quando duas correções independentes empurram o resultado em direções opostas: o lag reduzia o trade-off, a recalibração do IPCA aumentou o recall (mais caso real pego) à custa de mais falso positivo.

Leitura honesta: depois de 3 rodadas de correção, o número exato do trade-off oscilou entre 2,3x e 3,5x, não convergiu pra um valor único e estável. O que não oscilou foi a direção — o IRF sempre melhora precisão e recall, sempre custa mais falso positivo. Pra portfólio, a afirmação defensável é qualitativa ("existe trade-off real, na faixa de 2 a 3,5x"), não o número de 1 casa decimal — reportar "3,5x" como se fosse preciso seria falsa precisão, dado quanto ele já se moveu entre correções de bug.

## Os 150

A tese do projeto foca num analytics de blockchain AML que tem vantagem competitiva frente aos players já consolidados, que têm modelo robusto, produtização e escala. A vantagem se resume na adição da visão econômica com o comportamento humano. Isso vem com 3 condições: o pitch precisa mudar, reposicionar como nicho não-enterprise, testar distribuição real. O achado principal é o trade-off: com o IRF, a precisão dos flagados sobe, mas o falso positivo também sobe — poupador legítimo flagado à toa vai de 1,6% pra 5,6%.

*Número desatualizado pelo adendo acima (número real, com o lag corrigido: 1,5% → 3,5%, não 1,6% → 5,6%). Mantido como eu escrevi originalmente — "Os 150" só é revisado por quem escreveu — mas sinalizado aqui pra quem for citar externamente.*

---
## Delta de raciocínio

Dois erros de mecanismo, não de fato, valem registrar porque tendem a se repetir em tese futura:

1. **"Efeito existe" foi lido como "efeito é bom" sem checar direção.** Ao prever "reduz 20% de falso positivo", a magnitude bateu (17,3% de mudança de classificação), mas a predição pulou direto pra "e essa mudança é uma melhora" sem testar contra o rótulo de verdade. É o erro mais caro de todos porque é o mais fácil de não perceber — um número que "parece confirmar" a predição pode estar confirmando só a magnitude, não a direção.
2. **"Nosso diferencial" foi confundido com "por que ele escala".** Na lente de Escala, a resposta reafirmou a tese em vez de projetar o que muda entre o cliente 1 e o 10. O mecanismo é que é mais fácil redefender uma posição já tomada do que projetar um cenário novo — a pergunta de escala exige simular o futuro, não repetir o presente. Vale atenção em tese futura: quando a resposta a uma lente soa como a resposta de outra lente, é sinal de que a pergunta não foi respondida, só reformulada.
