# Tese: Shadow FX Terminal — vantagem competitiva frente a players estabelecidos (Chainalysis/TRM Labs/Elliptic)

**Status:** viva
**Aberta:** 2026-08-10 · **Veredito:** 2026-08-10 · **Reteste:** 2026-09-09

## A tese em uma frase

Shadow FX Terminal ganha porque tem abordagem econômica inserida e análise de comportamento humano, mesmo Chainalysis/TRM/Elliptic tendo modelos robustos, infra, clientes, produção etc.

## As 5 lentes

| Lente | Predição (fase 2) | Análise (fase 3) | Δ |
|---|---|---|---|
| Necessidade | Time de operações / compliance de empresas financeiras. | Confirmado por regulação real: Resoluções BCB 519-521/2025 (vigor fev/2026) obrigam VASPs a ter AML nível bancário e reporte ao COAF. Comprador não é hipotético, é criado por lei. | **Acerto.** |
| Impacto | Reduz 20% de falso positivo. | Ablação real: 17,3% das transações mudam de classificação com/sem IRF (magnitude bateu). Mas o teste inicial só provou *que* muda, não *pra melhor*. Teste de precisão contra rótulo de verdade (`tipo_usuario`): precisão sobe de 35,8%→43,6%, recall de 34,4%→48,3% — mas falso positivo em poupador legítimo TRIPLICA (1,6%→5,6%). | **Acerto de magnitude, erro de mecanismo** — presumiu "efeito grande = efeito bom" sem testar direção; o ganho de precisão é real mas vem com trade-off não previsto que contradiz o pitch central do projeto ("não bloquear o poupador legítimo"). |
| Distribuição | Mandar pra amigos que trabalham na área, pedir visão interna de suas empresas, estudar como abordar via alguém do time interno que usaria o modelo. | É pesquisa de descoberta via rede pessoal, não canal de vendas repetível. Válido como passo 0 (setor de AML vende por confiança/indicação), mas não escala além de 1-3 contatos sem virar canal real. | **Resposta incompleta** — cobre descoberta, não distribuição em escala. |
| Escala | "Como enxergamos os dados, e entendemos o negócio." | Não respondeu o que muda entre cliente 1 e 10 — reafirmou a tese. Achado real ao investigar: o IRF é fiscal-específico do Brasil (Copom, IPCA, dívida/PIB). Escala de graça entre clientes brasileiros, mas cada país novo exige reconstruir o índice do zero — o oposto do modelo global dos incumbentes. | **Erro de otimismo** — a mesma especificidade que é vantagem hoje é o teto de crescimento internacional. |
| ROI | 2-3 meses de payback pro comprador. | Plausível se o rascunho COAF automático reduzir tempo de analista (audit report original citava MTTR de 45min → <10s), mas nunca medido com cliente real. | **Aposta razoável, não verificada** — nem acerto nem erro, é hipótese sem prova. |

## Como isso morre

A tese morre se, ao validar a classificação final contra o rótulo `tipo_usuario`/`eh_fracionamento` do dataset sintético, o IRF não melhorar a precisão em relação ao modelo sem IRF. Se piorar ou empatar, "efeito grande" (17,3% de mudança de classificação) era só reshuffling, não sinal — a tese perderia a lente de Impacto, que é a que mais sustenta a Necessidade.

**Testado em 2026-08-10:** precisão sobe de 35,8% (sem IRF) para 43,6% (com IRF), recall sobe de 34,4% para 48,3%. **Critério de morte não disparou — a tese sobrevive este teste.**

Achado colateral que o critério original não previu: falso positivo em poupador legítimo (`A_poupador_legitimo`) triplica com o IRF (1,6% → 5,6%). Isso não mata a tese pelo critério combinado, mas é uma tensão real que precisa entrar no destino.

## Veredito e destino

**Veredito: VAI.**

A tese sobrevive ao teste de falsificação combinado — o efeito do IRF é real e aponta na direção certa (mais precisão, mais recall). A vantagem de "abordagem econômica + comportamental" é defensável no eixo de Necessidade (regulação real cria o comprador) e Impacto (efeito mensurável, não ruído).

Mas o veredito vem com 3 condições que mudam a direção documentada do projeto, não só o resultado:

1. **O pitch precisa parar de vender "resolve o dilema sem custo".** O README/PROBLEM.md afirmam implicitamente que o IRF ajuda a não bloquear o poupador legítimo — o teste mostrou o oposto: o IRF aumenta a chance de bloquear poupador legítimo, em troca de pegar mais fracionador real. Isso é uma decisão de produto (trade-off precisão-cobertura vs. experiência do usuário legítimo) que precisa ser explícita, não escondida atrás de "detecta melhor".
2. **A vantagem competitiva real não é "modelo melhor"— é auditabilidade + especificidade de nicho (eixos 3 e 4 do menu anterior), não escala global.** O projeto deveria parar de se posicionar implicitamente contra Chainalysis/TRM/Elliptic em escala e se posicionar como solução pra exchange brasileira pequena/média que não paga preço enterprise — isso é consistente com o teto de escala encontrado (IRF é Brasil-específico).
3. **Falta o teste de distribuição real** — a resposta de "amigos no setor" precisa virar pelo menos 1 conversa real documentada antes da tese poder alegar "sei como vender isso".

**Destino:** próximo passo é `/wayfinder` pra decompor essas 3 condições em tickets concretos (reescrever pitch com trade-off explícito, reposicionar contra nicho não-enterprise, rodar 1 conversa de descoberta real) — não é mais um problema de "a tese vale", é um problema de "o quê construir/ajustar agora que a tese está validada com ressalvas".

## Adendo — recálculo com IRF_LAG_DAYS corrigido (2026-08-11)

Os números acima (linhas 22-26) foram calculados numa máquina cuja cópia local do projeto não tinha `.git` e estava incompleta — faltava `IRF_LAG_DAYS = 14`, um lag anti-vazamento de dado que já existia no histórico real do GitHub (`utils.py`), sem o qual o modelo via dado macro (IPCA/Selic/Dívida-PIB) do dia exato da transação, informação que na vida real só é publicada semanas depois.

**Recalculado com o lag correto, contra o mesmo rótulo de verdade:**

| Métrica | Sem IRF | Com IRF (vazando, número antigo) | Com IRF (`IRF_LAG_DAYS=14`, correto) |
|---|---|---|---|
| Precisão | 35,9% | 43,6% | **45,2%** |
| Recall | 34,4% | 48,3% | **43,9%** |
| Falso positivo (poupador legítimo) | 1,5% | 5,6% (3,5x) | **3,5% (2,3x)** |
| Transações que mudam de classificação | — | 17,3% | **16,9%** |

**O veredito não muda — o achado central sobrevive à correção, e o trade-off é até menos severo do que a versão com vazamento sugeria** (custo 2,3x, não 3,5x). O critério de falsificação da linha 22 continua não disparando: precisão e recall melhoram com o lag correto, na mesma direção.

Isso não invalida a tese, mas é um lembrete do próprio "Delta de raciocínio" abaixo: número que parece confirmar a predição pode estar certo por acidente metodológico, não por mecanismo — vale sempre checar se o pipeline que gerou o número tinha as salvaguardas que o projeto real já tinha implementado.

## Os 150

A tese do projeto foca em um analytics de blockchain AML que possui uma vantagem competitiva frente aos players já consolidados que possuem modelo robusto, produtização, escala e etc. A nossa vantagem se resume na adição da visão econômica com o comportamento humano. Isso vem com 3 condições: pitch precisa mudar, reposicionar como nicho não-enterprise, testar distribuição real. O principal achado é o trade-off de que, com IRF, aumentamos a precisão dos flagados, porém aumentamos o falso positivo (poupador legítimo flagado à toa — 1,6% → 5,6%).

> ⚠️ **Número desatualizado pelo Adendo acima** (número real, com o lag corrigido: 1,5%→3,5%, não 1,6%→5,6%). Mantido como o autor escreveu — "Os 150" só é revisado por quem escreveu — mas sinalizado aqui pra quem for citar externamente.

---
## Delta de raciocínio

Dois erros de mecanismo, não de fato, valem registrar porque tendem a se repetir em teses futuras:

1. **"Efeito existe" foi lido como "efeito é bom" sem checar direção.** Ao prever "reduz 20% de falso positivo", a magnitude bateu (17,3% de mudança de classificação), mas a predição pulou direto pra "e essa mudança é uma melhora" sem ter testado contra rótulo de verdade. É o erro mais caro de todos porque é o mais fácil de não perceber — um número que "parece confirmar" a predição pode estar confirmando só a magnitude, não a direção.
2. **"Nosso diferencial" foi confundido com "por que ele escala".** Na lente de Escala, a resposta reafirmou a tese em vez de projetar o que muda entre cliente 1 e 10. O mecanismo: é mais fácil re-defender uma posição já tomada do que projetar um cenário novo — a pergunta de escala exige simular o futuro, não repetir o presente. Vale atenção em teses futuras: quando a resposta a uma lente soa como a resposta de outra lente, é sinal de que a pergunta não foi respondida, só reformulada.
