# ADR-0008: Critério de decisão por teto de dano ao poupador

**Data:** 2026-10-23
**Status:** Accepted
**Proposto por:** Luiz Maibashi
**Contexto:** Ponto de operação da Camada 2 e da cascata (ADR-0009). Origem: `docs/revisao/2026-10-REVISAO.md` §1 e §2.4

## Contexto

Os limiares da Camada 2 (40 e 70 no `c2_score_anomalia`) e do `score_final` foram escolhidos no olho. Não existe ponto que maximize captura de fracionador e proteção do Poupador Assustado ao mesmo tempo. Escolher um limiar é escolher quanto dano ao cliente legítimo se aceita por fraude pega, e essa troca precisa estar escrita.

Baseline medido no snapshot (`src/medir_escada.py`, n=4.509 transações, 110 usuários):

- `alerta_final` ≠ VERDE: recall 49,7% [47,0; 52,4], FP em legítimos 25,2% [23,8; 26,8].
- Regra R3∪R4∪R5: 10/10 fracionadores (IC [72; 100]), 0/100 poupadores tocados (IC [0; 3,7]).
- O dado tem 29% de transações de fraude e ~8 transações por dia, então nenhuma capacidade de fila por dia é realista nele.

## Decisão

O ponto de operação é escolhido por uma regra de Neyman-Pearson com restrição de fila:

> Maximizar o recall de fracionador, **por usuário**, sujeito a:
> 1. **Teto de dano X = 5%**: no máximo 5% dos poupadores com pelo menos 1 alerta.
> 2. **Capacidade K**: no máximo K alertas por 100 transações. **Inativa no gerador v1** (`K=None`). Liga com o gerador v2 (ADR-0011, prevalência realista) e é calibrada com números reais na Fase 5.

Implementação: `escolher_limiar_operacao(df, score_col, x_max=0.05, k_max=None)` varre os limiares candidatos (valores únicos do score) e, entre os que respeitam as restrições, fica com os de maior recall por usuário. Em caso de empate, devolve o **maior** limiar: com o mesmo recall, ele gera menos alertas e incomoda menos poupadores. Se nenhum limiar respeita X, devolve `None`, e o degrau fica desligado. Isso é resultado, não erro.

**Anti-vazamento:** o limiar é escolhido em metade dos usuários (split por usuário, estratificado por `tipo_usuario`, seed fixa) e reportado na outra metade, com IC de Wilson. Escolher e medir no mesmo dado infla o resultado.

**Sensibilidade de custo:** além do ponto escolhido, o relatório mostra o limiar que minimiza o custo esperado com razões FN:FP de 1:1, 10:1 e 50:1. Isso fica no relatório e não decide nada até a Fase 5 trazer custos reais.

**Por que 5% por usuário:** com n=100 poupadores, 0/100 ainda tem IC até 3,7%. Um teto de 2% não seria distinguível de 0% nem de 5%, então seria só retórica. Contar por usuário em vez de por transação corresponde ao dano real, que é o cliente bloqueado, e não ao número de linhas.

**ROI:**
- Se não fizermos isso, cada limiar é defendido no olho, e a pergunta de entrevista "por que 70?" não tem resposta.
- Se fizermos, todo degrau é comparado na mesma régua ("quantos fracionadores eu pego sem incomodar mais de 5% dos poupadores?"), e um degrau que não se paga é desligado por critério.

## Consequências

**Positivas**
- O ponto de operação passa a ser reproduzível e explicável a um diretor de compliance.
- Desligar o degrau vira um resultado legítimo.

**Negativas**
- Com 10 fracionadores, o split 50/50 deixa 5 de cada lado. O IC do recall de avaliação vai de cerca de 50% a 100%. O número só fica útil no v2, com mais usuários.
- X = 5% é julgamento, não custo medido. Fica marcado como hipótese até a Fase 5.
- K inativo significa que o ponto escolhido pode gerar mais alertas do que uma equipe real consegue revisar. Isso fica escrito no relatório.

## Alternativas descartadas

| Opção | Vantagem | Por que foi rejeitada |
|---|---|---|
| Manter 40/70 fixos | Zero trabalho | Arbitrário, sem dano declarado |
| Minimizar custo esperado (FN·c₁ + FP·c₂) | Ótimo se os custos forem conhecidos | Os custos são desconhecidos. Fica só como sensibilidade |
| Teto de 2% por usuário | Mais protetor | Indistinguível de 0% e de 5% com n=100 |
| Teto por transação | Mais n | Mede linha, não cliente incomodado |
| Ligar K = 15/100 já | Restrição completa | O número seria inventado sobre uma prevalência irreal |

## Validação

- `escolher_limiar_operacao` tem teste unitário com dado de brinquedo onde o limiar ótimo é conhecido, incluindo o caso sem limiar viável (`None`).
- `src/medir_escada.py` reporta o limiar escolhido, o recall e o FP por usuário no lado de avaliação, com IC.
- Revisão: ao ligar o gerador v2 (ADR-0011), reabrir K.
