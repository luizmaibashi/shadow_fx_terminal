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

A inovação central é o IRF como feature contextual: injetar o índice como variável do modelo transforma um classificador comportamental num sistema que entende quando o comportamento é suspeito, não só como ele parece.

Resposta: um pipeline em cascata onde cada camada resolve o trivial e passa o complexo adiante. A eficiência vem da hierarquia, a inteligência vem do IRF.

---

## O trade-off real, medido — o preço da inovação central

A seção anterior descreve o que o IRF deveria fazer: distinguir Cidadão A de Criminoso B sem custo pra nenhum dos dois. Testado contra o rótulo de verdade do dataset sintético (`docs/tese/shadow-fx-vantagem-competitiva/TESE.md`, veredito 2026-08-10, recalculado em 2 rodadas de correção de bug em 2026-08-11), a realidade tem um trade-off que a narrativa acima não captura:

| Métrica | Sem IRF | Com IRF |
|---|---|---|
| Precisão (dos flagados, % que era fraude real) | 35,9% | 44,8% |
| Recall (dos fraudadores reais, % detectado) | 34,4% | 49,9% |
| Falso positivo (poupador legítimo flagado à toa) | 1,5% | 5,0% (2,3x a 3,5x conforme a rodada de calibração) |

O que isso significa, sem retórica: o IRF pega mais fracionador de verdade, mas em troca incomoda mais o Cidadão A — o poupador assustado que o projeto existe pra proteger. Isso não invalida o projeto — a tese sobreviveu ao teste de falsificação nas 3 versões testadas, precisão e recall sempre melhoraram, não é ruído — mas é uma tensão real entre os dois objetivos da Pergunta 2, não uma solução que resolve os dois sem custo. O multiplicador exato do falso positivo (2,3x a 3,5x) se moveu a cada bug de calibração corrigido, então é reportado como faixa, não número fixo — é a leitura honesta (ver `TESE.md`, adendo 2).

Decisão registrada: aceitar o trade-off como está e documentá-lo, sem tunar o modelo pra reduzir o falso positivo, porque o dataset é sintético — otimizar em cima dele arrisca ajustar pra um ruído que não existe em produção real. Ver `docs/wayfinder/tese-veredito-condicoes/0001-tunar-ou-aceitar-trade-off.md`.

---

## Vantagem competitiva — por que isso não é só mais um score de anomalia

O mercado de blockchain analytics/AML já é dominado por Chainalysis, TRM Labs, Elliptic — modelo robusto, infraestrutura, clientes, centenas de milhões em captação. Nenhum dos três compete de frente em "modelo melhor": eles têm mais dado, mais engenharia, mais tempo de mercado. A vantagem deste projeto está em outro eixo — contexto macro-fiscal como feature, mais especificidade regulatória brasileira — não em detectar melhor no sentido genérico.

"Detectar melhor" não é o argumento certo, porque o ganho de precisão vem com custo real (mais falso positivo, como visto acima). Um discurso de "nosso modelo é mais preciso" sem essa ressalva cairia em 5 minutos na frente de qualquer avaliador técnico.

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
| Bancos e fintechs | Compliance cego ao contexto macroeconômico | Sistema de AML que pondera crise vs. crime, com precisão medida, não hipotética (44,8% vs. 35,9%) |
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
