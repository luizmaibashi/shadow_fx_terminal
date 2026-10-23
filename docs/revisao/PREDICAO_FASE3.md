# Predição da Fase 3 (registrada antes da medição)

**Data:** 2026-10-23 · **Quem:** Luiz Maibashi · **Medição:** `src/medir_irf.py` (ADR-0011), ainda não rodada em tamanho real quando isto foi escrito.

| Pergunta | Predição do Luiz (literal) | Leitura registrada |
|---|---|---|
| Recall de fracionador no v2, com IRF − sem IRF | "cerca de 10%" | +10 p.p. |
| FP do poupador nos dias de IRF alto, com − sem | "sobe cerca de 5%" | +5 p.p. |
| Condições que passam | "B" | B passa; A e C falham |

Implicação da predição: o IRF ganharia recall (B), mas o placebo também mostraria ganho (A falha, ou seja, parte do efeito seria do método e não do macro), e o poupador seria mais incomodado nos dias de estresse (C falha). Pelo critério de abandono, isso tiraria o IRF do pitch como diferencial.

## Resultado (2026-10-23, `medir_irf.py`, seed 42, B=2.000)

Período efetivo 02/01/2024-27/06/2025. Avaliação: 625 usuários (100 fracionadores, 500 poupadores). Dia de estresse: `irf_contexto` ≥ 47,38 (136 dias corridos), o mesmo corte nos dois mundos. Unidade: usuário. IC 95% por bootstrap pareado.

| Métrica (com IRF − sem IRF) | Placebo | v2 |
|---|---|---|
| Recall de fracionador | **+14,0 p.p.** [+5,0; +24,0] | **+24,0 p.p.** [+15,0; +33,0] |
| FP geral do poupador | −0,4 p.p. [−2,8; +1,8] | +0,6 p.p. [−2,0; +3,0] |
| FP do poupador em dia de estresse | +2,9 p.p. [+1,2; +4,8] | +1,8 p.p. [−0,2; +3,8] |

| Condição | Resultado |
|---|---|
| A: o IC do placebo contém zero | **Falha**: o placebo "ganha" 14 p.p. sem nenhum acoplamento macro |
| B: limite inferior do IC do recall no v2 > 0 | Passa (+15,0) |
| C: limite superior do IC do FP de estresse no v2 ≤ +1 p.p. | **Falha** (+3,8) |

**Veredito pelo critério escrito antes (§4.3 da revisão):** o IRF sai do pitch como diferencial e passa a ser "contexto exibido ao analista". A falha em A é a mais importante: o mesmo método que mostra +24 p.p. no v2 mostra +14 p.p. num mundo em que o IRF não carrega nenhum sinal. Logo, a maior parte do ganho medido não vem do macro. O resultado do v2 sozinho seria lido como sucesso; foi o placebo que impediu isso.

**Mecanismo provável do artefato (hipótese, ainda não testada):** o recall é por usuário, ou seja, "pelo menos um alerta". Fracionadores têm dezenas de transações e poupadores ~12. Uma dimensão a mais no Isolation Forest espalha os scores, e quem tem mais transações ganha mais chances de cruzar o limiar. Para testar: repetir com uma coluna de ruído puro no lugar do IRF; se o "ganho" for parecido, o mecanismo se confirma.

**Limites:** uma única seed do gerador e do modelo; dado sintético escrito por quem tem a tese; v2 − placebo ≈ +10 p.p. é uma diferença de diferenças **sem IC e sem predição registrada**, e não serve como evidência.

## Delta da predição

| Item | Predição | Medido | Bateu? |
|---|---|---|---|
| Quais condições passam | só B | só B | Sim |
| Recall v2 (com − sem) | +10 p.p. | +24 p.p. [+15; +33] | Não: fora do IC, subestimou |
| FP de estresse v2 | +5 p.p. | +1,8 p.p. [−0,2; +3,8] | Não: fora do IC, superestimou |

O mecanismo do erro de magnitude fica para o Luiz escrever: por que ele esperava menos ganho de recall e mais dano ao poupador do que o medido.

---

## Teste de ruído: predição (registrada antes de rodar, 2026-10-23)

**Desenho:** no mundo placebo, troca-se `irf_contexto` por uma coluna de ruído puro (N(0,1) sorteado por dia, igual para todas as transações do dia, seed 7). Compara-se o modelo com ruído e o modelo sem a coluna, com o mesmo split, o mesmo teto de dano (x_max=0,05), o bootstrap pareado por usuário (B=2.000) e o dia de estresse definido pelo IRF real (≥ 47,38).

**Critério escrito antes:** o mecanismo "dimensão extra + recall por usuário" se confirma se o IC do ganho de recall com ruído se sobrepuser ao IC do IRF no placebo ([+5; +24] p.p.).

| Pergunta | Predição do Luiz (literal) | Leitura registrada |
|---|---|---|
| Recall (com ruído − sem) | "o mesmo do anterior" | +10 p.p. |
| FP do poupador em dia de estresse | "o mesmo do anterior" | +5 p.p. |
| O mecanismo se confirma? | "o mesmo do anterior" | Sim (+10 cai dentro de [+5; +24]) |

## Teste de ruído: resultado (`src/medir_irf_ruido.py`, seeds 42/7, B=2.000)

| Recall de fracionador (com coluna − sem) | Placebo | v2 |
|---|---|---|
| IRF (medição principal) | +14,0 p.p. [+5; +24] | +24,0 p.p. [+15; +33] |
| **Ruído por dia** | **+2,0 p.p. [−8; +11]** | **+16,0 p.p. [+7; +26]** |

FP do poupador em dia de estresse com ruído: placebo +0,2 p.p. [−0,8; +1,3]; v2 +1,6 p.p. [−0,6; +4,0].

**Pelo critério escrito antes (sobreposição de IC):** os ICs se sobrepõem em [+5; +11], então o critério dá "confirma". **Esse critério era fraco demais.** Dois ICs largos se sobrepõem quase sempre, e os pontos dizem outra coisa: no placebo, o ruído ganha +2 e o IRF ganha +14. Leitura honesta:

1. **A hipótese "qualquer dimensão extra gera ganho" não se sustenta no placebo.** O ganho falso do IRF ali vem de algo específico da forma da série (distribuição e autocorrelação no tempo), não do conteúdo macro e não de uma coluna qualquer. Próximo teste, se valer: o IRF com os dias embaralhados (mantém a distribuição e quebra a ordem) e o IRF embaralhado em blocos.
2. **No v2, até o ruído puro "ganha" +16 p.p.** O v2 só difere do placebo no comportamento do poupador, então o ganho de +24 do IRF no v2 está majoritariamente inflado por um efeito que não depende do macro. Isso **reforça** o veredito da Fase 3: o IRF sai do pitch como diferencial.
3. **Lição de método:** o recall por usuário com limiar escolhido pelo teto de poupadores é sensível a qualquer mudança de geometria do modelo. Toda ablação neste projeto precisa ter um controle de ruído ao lado, não só um placebo de dado.

### Delta da predição (ruído)

| Item | Predição | Medido | Bateu? |
|---|---|---|---|
| Recall (com ruído − sem), placebo | +10 p.p. | +2 p.p. [−8; +11] | Dentro do IC, mas longe do ponto |
| FP de estresse, placebo | +5 p.p. | +0,2 p.p. [−0,8; +1,3] | Não |
| Mecanismo confirma | Sim | Pelo critério, sim; pela substância, não | Critério mal escrito (erro do Claude) |
