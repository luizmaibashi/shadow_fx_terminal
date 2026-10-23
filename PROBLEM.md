# PROBLEM.md — o raciocínio de negócio por trás do Shadow FX Terminal

Este documento registra por que o projeto existe, as perguntas que ele tentou responder e as decisões técnicas que vieram dessas respostas.

---

## A origem: dois catalisadores, um projeto

### Catalisador 1 — o paper

Tudo começou com a leitura de *"Dolarização Informal: Stablecoins como resposta à instabilidade monetária brasileira"* (Paulo J. Britto, OTC Research, 2026).

O objetivo inicial era puramente analítico: validar e expandir a análise estatística do paper com dado real. A tese central é que o brasileiro compra USDT não pra especular em cripto, mas como hedge contra a desvalorização estrutural do Real — o mesmo comportamento que leva família a guardar dólar em casa numa crise cambial, só que na forma digital.

### Catalisador 2 — o evento de mercado

O segundo empurrão veio de um evento sobre as novas fronteiras de segurança financeira no digital pós-fraudes. A pergunta que ficou foi: como criar um sistema de compliance sensível o suficiente pra capturar fraude sofisticada (smurfing, lavagem via bets, evasão de divisas) e específico o suficiente pra não bloquear o cidadão comum que está só reagindo racionalmente a uma crise macroeconômica?

O insight que ficou: o comportamento financeiro só faz sentido se você conhece o contexto macroeconômico do momento. Essa frase virou o princípio de design do IRF.

---

## As perguntas fundamentais

O projeto foi estruturado em torno de três perguntas progressivas, cada uma respondida por uma fase do pipeline.

### Pergunta 1 (econométrica): o brasileiro usa stablecoin como dólar de colchão?

Se a hipótese for verdadeira, comprar USDT num período de câmbio alto não é crime financeiro, é comportamento racional de preservação de capital. Um sistema de AML que não entende isso vai gerar enxurrada de falso positivo, punindo o cidadão comum.

A resposta não veio de um dado único, veio de uma cadeia de 5 evidências convergentes:

| # | Evidência | Resultado | O que prova |
|:--|---|:---:|---|
| 1 | Spearman (BRL/USD × volume USDT global) | r = +0,496, significativo | co-movimento entre câmbio e demanda por stablecoin |
| 2 | Correlação parcial controlando DXY | queda de −2,5% | não é efeito do dólar global — o sinal é específico do BRL |
| 3 | Google Trends `geo='BR'` × BRL/USD | r = +0,501, significativo | o interesse em USDT é especificamente brasileiro |
| 4 | Lead-lag: BRL[t−1] → interesse BR[t] | r = +0,508, significativo | o câmbio precede o interesse — há direcionalidade causal |
| 5 | Dívida bruta/PIB × volume USDT | r = +0,707, significativo | a raiz é dominância fiscal estrutural, não volatilidade de curto prazo |

Resposta: sim, com suporte metodológico razoável. O fenômeno é real, é brasileiro, tem direcionalidade causal e é rastreável a fundamento macroeconômico estrutural — não é só reação a choque de câmbio.

### Pergunta 2 (regulatória): por que a nova regra do BCB cria um problema de compliance?

Com as Resoluções BCB 519-521/2026 equiparando stablecoin a câmbio, toda corretora passou a ter obrigação legal de reportar operação suspeita ao COAF. O problema é que a maioria ainda usa regra fixa pra detectar suspeita.

Um cenário real ilustra o problema — dia 16/10/2024, BRL = R$ 6,28, IRF = 87/100:

- **Cidadão A, o poupador assustado.** Compra R$ 8.500 de USDT às 14h via Pix. Motivo real: câmbio disparou, quer proteger o 13º salário.
- **Criminoso B, o fracionador profissional.** Faz 9 transferências de R$ 8.900 pra wallets diferentes entre 2h e 4h da manhã. Motivo real: smurfing pra fugir do limite de R$ 10k da Resolução BCB 519.

Com regra tradicional: Cidadão A é flagado (valor perto do limiar), o analista perde tempo, o cidadão fica frustrado. Criminoso B passa, porque cada transação isolada está "abaixo do limite".

O que a regra fixa não enxerga é o contexto macroeconômico que torna o comportamento do Cidadão A previsível e legítimo, e o padrão do Criminoso B que só aparece quando você olha o conjunto — horário, distribuição de wallets, valor agregado.

Resposta: regra fixa falha porque é cega ao contexto. Comprar R$ 8.500 de USDT num dia de câmbio estável é estatisticamente diferente da mesma compra num dia de stress fiscal elevado. Threshold fixo não capta essa distinção.

### Pergunta 3 (técnica): como construir isso de forma escalável?

Uma corretora de médio porte processa centenas de milhares de transações por mês. Mandar tudo pra um analista humano é inviável. Mandar tudo pra um LLM é caro e lento. A resposta precisa ser inteligente e barata ao mesmo tempo.

A arquitetura em cascata resolve isso:

```
Camada 1 — filtros determinísticos (BCB 519-521)
  custo ~0ms, cobre ~87% dos casos
  as regras existem e precisam ser aplicadas
  caso verde passa direto, caso com flag vai pra C2

Camada 2 — Isolation Forest + IRF
  custo ~1ms, cobre ~13% dos casos
  o comportamento é anômalo ou descorrelacionado do cenário macro?
  diferencia hedge (segue o câmbio) de anomalia grave (volume massivo em calmaria)
  caso vermelho é reportado, zona cinza vai pra C3

Camada 3 — LLM como juiz (agente RAG + atas do Copom)
  custo ~2s, cobre ~0,2% dos casos mais ambíguos
  lê a ata recente e julga se aquele perfil de risco é esperado
  gera rascunho de RIF pro COAF
```

Os percentuais de cobertura acima são estimativa de desenho, feita antes de medir. Medido nas 4.509 transações sintéticas de `deploy/hf_space/data/processed/resultado_compliance.csv`: a Camada 1 sinaliza 3.345 casos (74,2%), e a zona cinza da Camada 2 (score entre 40 e 70), que é o que seguiria para o LLM, tem 1.164 casos (25,8% [24,6; 27,1]), não 0,2%. Com o juiz ligado, a Camada 3 receberia cerca de 130 vezes o volume previsto.

A ideia de desenho era o IRF como feature contextual: com o índice dentro do modelo, ele julgaria não só como o comportamento parece, mas quando ele é suspeito. A próxima seção mostra que o dado atual não consegue testar essa ideia.

Resposta de desenho: um pipeline em cascata onde cada camada resolve o trivial e passa o complexo adiante. Resposta medida: no dado atual, o primeiro degrau já resolve tudo, e os de cima não têm trabalho.

---

## A escada medida (revisão de outubro/2026)

Cada degrau de custo maior só se justifica se o anterior falhar em algo. Medi cada um contra o rótulo do dataset sintético. Reproduz com `python src/medir_escada.py`, e os números ficam travados em `tests/test_medir_escada.py`. Intervalos são Wilson 95%.

| Degrau | Sinaliza | Precisão | Recall (fracionador) | Legítimo sinalizado |
|---|---:|---|---|---|
| Camada 1 completa (R1-R6) | 3.345 | 39,3% [37,7; 41,0] | 100% [99,7; 100] | 63,6% [61,9; 65,2] |
| **Só regras de comportamento (R3, R4, R5)** | 1.327 | **99,0% [98,3; 99,4]** | **99,9% [99,6; 100]** | **0,4% [0,2; 0,7]** |
| Isolation Forest "suspeito" (score > 70) | 369 | 39,0% [34,2; 44,1] | 11,0% [9,4; 12,8] | 7,0% [6,2; 8,0] |
| Alerta final AMARELO ou VERMELHO | 1.460 | 44,8% [42,3; 47,4] | 49,7% [47,0; 52,4] | 25,2% [23,8; 26,8] |

O que a tabela diz:

1. **A regra sozinha resolve este dado.** Pega 1.314 de 1.315 transações de fracionador e erra em 13 de 3.194 legítimas. R1 e R2 (valor e volume) são regras de reporte obrigatório e acertam em cheio o institucional legítimo; misturadas com as de comportamento, elas inflam a Camada 1 para 74%.
2. **O modelo não acrescenta nada à regra aqui.** Onde só o modelo acusa (score > 70 sem regra de comportamento), há 0 fraudes em 225 casos [0; 1,7%]. E ele dá score abaixo de 40 a 654 transações de fracionador que a regra pegou.
3. **O motivo é que o teste é circular.** O gerador (`src/gerador_transacoes_mock.py`) cria a fraude com valor entre R$ 8.500 e R$ 9.900 na madrugada, exatamente o que R4 e R5 procuram. Não existe no dado um fracionador que fuja da regra, então nenhum degrau acima tem o que fazer.
4. **O `n` que importa é de pessoas.** São 10 fracionadores, 100 poupadores e 15 institucionais. Por usuário, a regra pega 10 de 10 fracionadores (IC [72; 100]) e não toca nenhum dos 100 poupadores ([0; 3,7]). Intervalo por transação passa mais certeza do que 10 pessoas sustentam.
5. **O juiz LLM nunca foi avaliado, e seu veredito não muda nada.** `c3_veredito` não entra em `score_final`, na API nem no dashboard. No snapshot, os 1.164 casos cinza estão em `FALLBACK`.

Leitura: o resultado não diz que o ML ou o LLM são inúteis no mundo real. Diz que este dado não tem o caso que justificaria subir um degrau. Saber dizer isso com número é o ponto deste projeto hoje. Diagnóstico completo e plano: `docs/revisao/2026-10-REVISAO.md`.

---

## O trade-off real, medido — o preço da inovação central

A seção anterior descreve o que o IRF deveria fazer: distinguir Cidadão A de Criminoso B sem custo pra nenhum dos dois. Testado contra o rótulo de verdade do dataset sintético (`docs/tese/shadow-fx-vantagem-competitiva/TESE.md`, veredito 2026-08-10, recalculado em 2 rodadas de correção de bug em 2026-08-11), a realidade tem um trade-off que a narrativa acima não captura:

| Métrica | Sem IRF | Com IRF |
|---|---|---|
| Precisão (dos flagados, % que era fraude real) | 35,9% | 44,8% |
| Recall (dos fraudadores reais, % detectado) | 34,4% | 49,9% |
| Falso positivo (poupador legítimo flagado à toa) | 1,5% | 5,0% (2,3x a 3,5x conforme a rodada de calibração) |

Base: as 4.509 transações sintéticas do gerador. Os números são pontuais, sem intervalo de confiança, e a ablação que os gerou não está versionada no repositório.

**Revisão de outubro/2026: esta tabela não sustenta a tese, nem contra nem a favor.** O gerador sorteia a data de cada transação sem olhar o cenário macro, então o IRF tem a mesma distribuição nas três classes (média 25,6 no poupador, 26,3 no institucional, 25,9 no fracionador; KS poupador × fracionador D = 0,043, p = 0,19). Se o IRF não difere entre quem frauda e quem poupa, ele não tem como informar o modelo sobre quem é quem. O ganho de 35,9% para 44,8% vem da forma como o Isolation Forest separa pontos quando ganha uma dimensão a mais, não do contexto. A oscilação do falso positivo do poupador entre 2,3x e 3,5x a cada correção de calibração é o sintoma: efeito real não se move tanto com ajuste de calibração. E o comportamento que a tese descreve (o poupador compra mais quando o câmbio sobe) nunca foi simulado.

O que muda: o trade-off da tabela não é "o preço do IRF", é ruído de um teste que não podia dar certo. A tese do IRF volta a ser hipótese, com teste e critério de abandono escritos antes de rodar (`docs/revisao/2026-10-REVISAO.md`, §4): gerador novo em que o poupador reage ao câmbio e o fracionador não, um controle sem esse acoplamento em que o IRF precisa dar ganho zero, e comparação por usuário com o mesmo teto de dano ao poupador. Se falhar, o IRF sai do discurso como diferencial e fica como contexto exibido ao analista.

A decisão anterior de não tunar o modelo no dado sintético (`docs/wayfinder/tese-veredito-condicoes/0001-tunar-ou-aceitar-trade-off.md`) continua certa, agora por um motivo mais forte: não há sinal do IRF para tunar.

---

## Vantagem competitiva — por que isso não é só mais um score de anomalia

O mercado de blockchain analytics/AML já é dominado por Chainalysis, TRM Labs, Elliptic — modelo robusto, infraestrutura, clientes, centenas de milhões em captação. Nenhum dos três compete de frente em "modelo melhor": eles têm mais dado, mais engenharia, mais tempo de mercado. A vantagem deste projeto está em outro eixo — contexto macro-fiscal como feature, mais especificidade regulatória brasileira — não em detectar melhor no sentido genérico.

"Detectar melhor" não é o argumento certo: no dado sintético a regra simples já detecta tudo, e o ganho atribuído ao IRF não se sustenta (ver acima). Um discurso de "nosso modelo é mais preciso" cairia em 5 minutos na frente de qualquer avaliador técnico.

"Nicho porque eles não têm orçamento pra atender" também não é o argumento certo — foi a primeira hipótese testada, e caiu contra um fato real: VASP autorizada no Brasil precisa de capital mínimo de R$ 10,8 milhões por lei (fonte: NDM Advogados). Não é startup sem grana disputando com quem paga US$ 50-200K/ano de Chainalysis.

O argumento que sobreviveu ao teste é a complexidade regulatória brasileira dinâmica, que um player global genérico não tem incentivo de negócio pra acompanhar de perto:

- Cerca de 7 mudanças regulatórias relevantes em 18 meses — Lei 14.478/2022, 4 consultas públicas (2023-2024), Resoluções BCB 519/520/521 (nov/2025), Resolução 561, IN BCB 701/2026, mudança de IOF sobre stablecoin (fev/2026). Fonte: Agência Brasil, Mattos Filho, Forbes.
- Nenhuma evidência pública de Chainalysis, TRM Labs ou Elliptic tratando o Brasil como mercado prioritário — sem expansão anunciada, sem feature específica pra resolução do BCB encontrada em busca dedicada.
- Volume real que sustenta a demanda: R$ 388 bilhões declarados em criptoativo por brasileiro em 9 meses de 2025, mais de 70% em stablecoin. Fonte: Blue Consult.

A ressalva que fica, com honestidade: essa tese é bem fundamentada em fato público, não é opinião solta — mas continua sendo raciocínio, não validação de mercado. O teste que faltaria pra virar validação — alguém de uma exchange brasileira confirmando que ainda não resolveu isso sozinho, ou que valorizaria essa especificidade — ainda não foi feito. Ver `docs/tese/shadow-fx-vantagem-competitiva/TESE.md` (veredito completo).

---

## Valor de negócio e ROI

| Stakeholder | Problema resolvido | Valor gerado |
|---|---|---|
| Corretoras de cripto | Falso positivo bloqueando cliente legítimo | Contexto reduz falso positivo frente a regra fixa incondicional, mas não zera — reduz relativo ao modelo sem IRF (ver trade-off acima). Reduz fadiga do analista via priorização, não elimina revisão humana |
| Bancos e fintechs | Compliance cego ao contexto macroeconômico | Hipótese: pesar crise vs. crime. Ainda não testada (o dado sintético não carrega sinal do IRF); teste e critério de abandono em `docs/revisao/2026-10-REVISAO.md` |
| Reguladores (BCB/COAF) | Excesso de reporte de baixa qualidade escondendo os reais | Reporte mais preciso, com rascunho automatizado via LLM |
| Mercado de dados | Validação independente do paper de Britto (2026) | Evidência econométrica com cadeia de 5 provas convergentes |

---

## Nota metodológica — limitação de atribuição geográfica

O paper de Britto (2026) admite que o dado on-chain (volume de USDT em blockchain) é global — não dá pra identificar se quem comprou foi brasileiro, argentino ou turco. Pra resolver isso, o paper cruza com dado de busca web geolocalizado como proxy de demanda doméstica.

Este projeto replica e expande essa metodologia usando Google Trends filtrado pra `geo='BR'` — 183 semanas de dado semanal — combinado com lead-lag e correlação parcial controlando o DXY. O resultado é a cadeia de 5 evidências da Pergunta 1.

**Onde estão os scripts:**
- `src/coletar_google_trends_br.py` — coleta o Google Trends com `geo='BR'`
- `src/validacao_atribuicao_geografica.py` — roda os 5 testes de viés geográfico
- `src/validacao_estatistica.py` — correlação parcial, lead-lag e simulação de estresse
- `src/analise_correlacao.py` — relatório completo da cadeia de evidências

**Limitações residuais:** Google Trends é índice relativo (0-100), não volume absoluto de compra. O volume USDT do yfinance é global, é proxy de fluxo, não de origem geográfica. Dado on-chain georreferenciado (Chainalysis, Glassnode Pro) removeria essa ambiguidade, mas custa cerca de USD 999/mês. A cadeia de evidências é suporte razoável, não prova definitiva, sem dado on-chain localizado — essa limitação é documentada explicitamente, seguindo o padrão de transparência do paper original.
