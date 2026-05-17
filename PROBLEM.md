# PROBLEM.md — Contrato AI Scientist: Shadow FX Terminal

> *Este documento registra o raciocínio de negócio e as decisões técnicas fundamentais do projeto, na perspectiva de um AI Scientist orientado a valor.*

---

## 💡 A Origem: Dois Catalisadores, Um Projeto

### Catalisador 1 — O Paper
Tudo começou com a leitura do paper *"Dolarização Informal: Stablecoins como resposta à instabilidade monetária brasileira"* (Paulo J. Britto, OTC Research, 2026).

O **objetivo inicial** era puramente analítico: **validar e expandir a análise estatística** do paper com dados reais. A tese central é que o brasileiro compra USDT não para especular em cripto, mas como mecanismo de *hedge* contra a desvalorização estrutural do Real — o mesmo comportamento que leva famílias a guardar dólar em casa durante crises cambiais, só que na forma digital.

### Catalisador 2 — O Evento de Mercado
O segundo vetor de inspiração veio de um evento do mercado financeiro sobre **novas fronteiras de segurança financeira no ecossistema digital pós-fraudes**. O evento levantou um problema que os bancos e corretoras brasileiras ainda não resolveram: como criar um sistema de compliance que seja simultaneamente:

- **Sensível o suficiente** para capturar fraudes sofisticadas (smurfing, lavagem via bets, evasão de divisas)
- **Específico o suficiente** para não bloquear o cidadão legítimo que responde racionalmente a uma crise macroeconômica

O insight chave extraído: *"O comportamento financeiro só faz sentido se você conhece o contexto macroeconômico do momento."* Essa frase se tornou o princípio de design do IRF (Índice de Risco Fiscal).

---

## ❓ As Perguntas Fundamentais

O projeto foi estruturado em torno de **três perguntas progressivas**, cada uma respondida por uma fase do pipeline:

---

### Pergunta 1 (Econométrica): O brasileiro usa stablecoin como dólar de colchão?

**Por que essa pergunta importa:**
Se a hipótese for verdadeira, a compra de USDT em períodos de câmbio alto não é crime financeiro — é comportamento racional de preservação de capital. Um sistema de AML que não entende isso vai gerar uma enxurrada de falsos positivos, punindo o cidadão comum.

**Como respondemos:**

A resposta não veio de um dado único, mas de uma **cadeia de 5 evidências convergentes**:

| # | Evidência | Resultado | O que prova |
|:--|:---|:---:|:---|
| 1 | Spearman (BRL/USD × Volume USDT global) | r = +0.496 ✅ | Co-movimento existe entre câmbio e demanda por stablecoin |
| 2 | Correlação Parcial controlando DXY | −2.5% de redução | **Não é efeito do dólar global** — o sinal é específico do BRL |
| 3 | Google Trends `geo='BR'` × BRL/USD | r = +0.501 ✅ | O interesse em USDT é especificamente **brasileiro** |
| 4 | Lead-Lag: BRL[t−1] → Interesse BR[t] | r = +0.508 ✅ | O câmbio **precede** o interesse — há direcionalidade causal |
| 5 | Dívida Bruta/PIB × Volume USDT | r = +0.707 ✅ | A raiz é **dominância fiscal estrutural**, não volatilidade de curto prazo |

**Resposta:** Sim, com suporte metodológico robusto. O fenômeno é real, é brasileiro, tem direcionalidade causal e é rastreável a fundamentos macroeconômicos estruturais — não apenas a choques de câmbio.

---

### Pergunta 2 (Regulatória): Por que as novas regras do BCB criam um problema de compliance?

**Por que essa pergunta importa:**
Com as Resoluções BCB 519-521/2026 equiparando stablecoins a câmbio, toda corretora passou a ter obrigação legal de reportar operações suspeitas ao COAF. O problema: a maioria ainda usa regras fixas para detectar suspeitas.

**O diagnóstico do problema:**

```
CENÁRIO REAL — dia 16/10/2024 (BRL = R$ 6,28, IRF = 87/100):

[CIDADÃO A] — Poupador Assustado
  Compra R$ 8.500 de USDT às 14h via PIX.
  Motivo real: câmbio disparou, quer proteger o 13º salário.

[CRIMINOSO B] — Fracionador Profissional
  Faz 9 transferências de R$ 8.900 para wallets diferentes entre 2h e 4h da manhã.
  Motivo real: smurfing para fugir do limite de R$ 10k da Resolução BCB 519.

[SISTEMA TRADICIONAL DE REGRAS]
  → Cidadão A: FLAG (valor próximo ao limiar) → Analista perde tempo → frustração
  → Criminoso B: PASSA (cada transação individual está "abaixo do limite")
```

**O que os sistemas tradicionais não conseguem ver:** o contexto macroeconômico que torna o comportamento do Cidadão A previsível e legítimo, e o padrão comportamental do Criminoso B que só aparece quando você analisa o conjunto das transações + horário + distribuição de wallets.

**Resposta:** As regras fixas falham porque são cegas ao contexto. A compra de R$ 8.500 de USDT em um dia de câmbio estável é estatisticamente diferente da mesma compra em um dia de stress fiscal elevado. Nenhum threshold fixo captura essa distinção.

---

### Pergunta 3 (Técnica): Como construir um sistema que faça essa distinção de forma escalável?

**Por que essa pergunta importa:**
Uma corretora de médio porte processa centenas de milhares de transações por mês. Mandar tudo para um analista humano é inviável. Mandar tudo para um LLM é caro e lento. A solução precisa ser ao mesmo tempo inteligente e eficiente.

**Como respondemos — Arquitetura em 3 Camadas (Cascaded Pipeline):**

```
CAMADA 1 — Filtros Determinísticos (BCB 519-521)
  → Custo: ~0ms | Cobre: ~87% dos casos
  → "As regras existem e precisam ser aplicadas."
  → Casos VERDES passam direto. Casos com flags vão para C2.

CAMADA 2 — Isolation Forest + IRF (Machine Learning + Contexto Macro)
  → Custo: ~1ms | Cobre: ~13% dos casos
  → "O comportamento é anômalo ou descorrelacionado do cenário macroeconômico?"
  → O modelo diferencia o **Hedge** (compra que segue o câmbio) de **Anomalias Graves** (volumes massivos em momentos de calmaria cambial).
  → Casos VERMELHOS são reportados. Zona cinza vai para C3.

CAMADA 3 — LLM-as-Judge (Agente RAG + Atas do Copom)
  → Custo: ~2s | Cobre: ~0.2% dos casos mais ambíguos
  → "Leia as últimas atas do Copom e julgue se esse perfil de risco é esperado."
  → Gera rascunho de Relatório de Inteligência Financeira (RIF) para o COAF.
```

**A inovação central — o IRF como Feature Contextual:**
Injetar o Índice de Risco Fiscal como variável do modelo de ML transforma um classificador comportamental num sistema que entende *quando* o comportamento é suspeito — não apenas *como* ele parece.

**Resposta:** Um pipeline em cascata onde cada camada resolve o que é trivial e passa o complexo para a camada seguinte. A eficiência vem da hierarquia; a inteligência vem do IRF.

---

## 💰 Valor de Negócio & ROI

| Stakeholder | Problema Resolvido | Valor Gerado |
|:---|:---|:---|
| **Corretoras de Cripto** | Falsos positivos bloqueando clientes legítimos | Redução da fadiga de analistas + evitar multas do BCB |
| **Bancos e Fintechs** | Compliance cego ao contexto macroeconômico | Sistema de AML que distingue crise de crime |
| **Reguladores (BCB/COAF)** | Excesso de reportes baixa qualidade que ocultam os reais | Reportes mais precisos com rascunho automatizado via LLM |
| **Mercado de Dados** | Validação independente e data-driven do paper de Britto (2026) | Evidência econométrica com cadeia de 5 provas convergentes |

---

## 🔬 Nota Metodológica — Limitação de Atribuição Geográfica

### O que o paper reconhece
O paper de Britto (2026) admite explicitamente que os dados on-chain (volume de USDT em blockchain) são **globais** — não permitem identificar se quem comprou USDT foi um brasileiro, um argentino ou um turco. Para resolver isso, o paper cruza com dados de busca web geolocalizados como proxy de demanda doméstica.

### Como este projeto replica e expande essa metodologia
Utilizamos o Google Trends filtrado exclusivamente para o Brasil (`geo='BR'`) — 183 semanas de dados semanais — combinado com análise de Lead-Lag e correlação parcial controlando o DXY (dólar global). O resultado é a **cadeia de 5 evidências** descrita na Pergunta 1.

### Onde estão os scripts
- `src/coletar_google_trends_br.py` — Coleta dados do Google Trends (`geo='BR'`)
- `src/validacao_atribuicao_geografica.py` — Executa os 5 testes de viés geográfico
- `src/validacao_estatistica.py` — Correlação parcial, Lead-Lag e simulação de estresse
- `src/analise_correlacao.py` — Relatório completo da cadeia de evidências

### Limitações residuais (honestidade científica)
- Google Trends é índice relativo (0–100), não volume absoluto de compras.
- Volume USDT do yfinance é global — proxy de fluxo, não de origem geográfica.
- Dados on-chain georreferenciados (Chainalysis, Glassnode Pro) removeriam ambiguidades, mas são pagos (~USD 999/mês).
- A cadeia de evidências constitui **suporte robusto, não prova definitiva** sem dados on-chain localizados. Essa limitação é documentada explicitamente seguindo o padrão de transparência científica do paper original.
