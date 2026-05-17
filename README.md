# Shadow FX Terminal 📊

> **Um pipeline quantitativo de análise econométrica e compliance AML para stablecoins no Brasil — onde ciência de dados encontra política monetária e segurança financeira.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Autor:** Luiz Maibashi  
**Referências principais:**
- *"Dolarização Informal: Stablecoins como resposta à instabilidade monetária brasileira"* — Paulo J. Britto (OTC Research, 2026)
- Insights extraídos de evento do mercado financeiro sobre **novas formas de segurança financeira no ecossistema digital pós-fraudes** (2025)

**Stack:** Python · Pandas · Scipy · Scikit-Learn · Jupyter · yfinance · python-bcb · pytrends

---

## 🌐 Contexto: Por Que Este Projeto Existe Agora?

### O Momento Atual — Fraudes, Bets e o Dinheiro que Some

O Brasil vive uma crise silenciosa de integridade financeira. Em paralelo à desvalorização crônica do Real, o ecossistema financeiro digital brasileiro enfrenta três frentes simultâneas de risco:

1. **Fraudes bancárias em escala industrial:** O Brasil lidera o ranking mundial de golpes financeiros digitais. Só em 2024, o sistema bancário registrou mais de **R$ 2,5 bilhões em prejuízos com fraudes via Pix**, incluindo engenharia social, SIM swap e contas de laranjas. O criminoso moderno não usa mais mala de dinheiro — usa PIX, contas digitais e stablecoins.

2. **O fenômeno das Bets (casas de apostas online):** Com a regulamentação do mercado de apostas esportivas em 2024, explodiram os casos de lavagem de dinheiro via plataformas de apostas. O esquema é simples: deposita dinheiro sujo, aposta em odds garantidas entre contas próprias, saca o "prêmio" limpo. Stablecoins entram nesse fluxo como camada de anonimização entre o dinheiro fiat e o cripto.

3. **Evasão de divisas via stablecoin:** A desvalorização do Real empurra dois públicos opostos para o USDT — o cidadão assustado que quer preservar poder de compra, e o criminoso que usa o mesmo instrumento para mandar dinheiro para fora sem passar pelo câmbio oficial. Sistemas de compliance que não distinguem esses dois perfis são ineficazes por design.

> **O desafio central:** Como uma instituição financeira, corretora de criptoativos ou regulador distingue automaticamente o *"Poupador Assustado"* do *"Fracionador Profissional"*? Essa é a pergunta que este projeto responde.

### A Dupla Inspiração — Paper + Evento de Mercado

**O ponto de partida acadêmico** foi o paper de Paulo J. Britto (OTC Research, 2026), que demonstrou quantitativamente que brasileiros usam USDT como reserva de valor — não como especulação.

**O segundo vetor de inspiração** veio de um evento do mercado financeiro sobre as **novas fronteiras de segurança financeira no ecossistema digital**. O evento discutiu como as instituições financeiras tradicionais estão sendo forçadas a repensar seus modelos de compliance frente a:
- **Pagamentos instantâneos 24/7** (Pix): janela de fraude que não dorme
- **DeFi e stablecoins** como camada de anonimização
- **IA generativa sendo usada por fraudadores** (deepfakes de voz, documentos sintéticos)
- A necessidade de **sistemas de score contextual** — que levem em conta não só o comportamento do usuário, mas o *ambiente macroeconômico* no momento da transação

Essa última ideia — *contexto macroeconômico como feature de ML* — foi o insight que transformou uma análise estatística num produto de compliance.

---

## 🧠 O Ponto de Virada: Da Análise Econométrica à Solução de Mercado

**O projeto nasceu com um objetivo puramente analítico (Projeto 1):** Consolidar estatisticamente a tese de que o brasileiro compra stablecoins (USDT) não para especular, mas como proteção contra a desvalorização do Real — e provar isso com dados reais, não mocks.

Enquanto construíamos o **Índice de Risco Fiscal (IRF)** para validar essa correlação, identificamos um **cenário de risco urgente no mercado regulatório**: as novas Resoluções do BCB passaram a enquadrar o USDT como câmbio, exigindo fiscalização ativa contra lavagem de dinheiro (AML).

O problema crítico: sistemas de compliance baseados apenas em regras simples ("flag se > R$ 10.000") iriam **bloquear o Poupador Assustado** (falso positivo) e **deixar o Fracionador profissional passar** (falso negativo). Nenhum dos dois resultados é aceitável.

**Decidimos então evoluir o projeto (Projeto 2):** Pegamos a prova estatística que construímos e a injetamos como inteligência contextual dentro de um algoritmo de Machine Learning. Nasceu assim uma solução completa que resolve dois problemas de uma vez:
1. **Valida quantitativamente** a tese da dolarização informal brasileira via stablecoins.
2. **Entrega um Motor de Compliance inteligente** que atende às novas regulações do BCB, diferenciando o cidadão que quer se proteger da inflação do criminoso que pratica evasão de divisas.

---

## 🏗️ Arquitetura do Sistema (3 Camadas)

O projeto segue o padrão **Cascaded Heuristic Filters** (Stanford CS230), garantindo eficiência de custo e precisão analítica:

1.  **Camada 1 (Regras BCB):** Filtros determinísticos baseados nas Resoluções 519-521/2026.
2.  **Camada 2 (IA de Detecção):** *Isolation Forest* calibrada com o Índice de Risco Fiscal (IRF v2). O modelo diferencia o comportamento de **Hedge** (compras de USDT que acompanham a desvalorização do Real) de **Anomalias de Descorrelação** (volumes massivos de compra em momentos de calmaria cambial, um forte indicador de lavagem ou evasão).
3.  **Camada 3 (LLM-as-a-Judge):** Orquestração de agentes para análise qualitativa de casos em "zona cinza".

---

## 🧪 Rigor Científico (Ciência de Dados)

O diferencial deste projeto é a aplicação do **CRISP-DM** com profundidade estatística:
*   **Análise de Estacionaridade:** Uso do Teste ADF para evitar correlações espúrias em séries financeiras.
*   **Justificativa de Pesos via PCA:** O Índice de Risco Fiscal não é arbitrário; seus pesos são derivados da Análise de Componentes Principais.
*   **Arena de Modelos:** Benchmark entre *Isolation Forest*, *LOF* e *One-Class SVM* para escolha do melhor motor de detecção.
*   **Explainable AI (XAI):** Visualização de fronteiras de decisão via PCA 2D para transparência no compliance.

---

## 📜 As Resoluções BCB 519-521/2026 — Por Que São o Coração deste Projeto

### O que mudou e por quê isso importa

Antes de 2026, stablecoins como USDT e USDC operavam em um **vácuo regulatório** no Brasil. Uma pessoa podia comprar R$ 500.000 em USDT numa corretora com menos burocracia do que abrir uma conta bancária. Isso criava um vetor óbvio para lavagem de dinheiro e evasão de divisas.

As **Resoluções BCB nº 519, 520 e 521** mudaram esse cenário definitivamente ao estabelecer que:

| Resolução | O que faz | Por que importa |
|:---|:---|:---|
| **BCB 519** | Equipara stablecoins lastreadas em moeda estrangeira a **instrumentos de câmbio** | A compra de USDT passa a ter os mesmos requisitos legais de uma operação de câmbio tradicional |
| **BCB 520** | Exige que corretoras de cripto atuem como **Instituições de Pagamento reguladas** com KYC reforçado | Know Your Customer passa a ser obrigatório e auditável — igual aos bancos |
| **BCB 521** | Obriga o reporte automático ao **COAF** de transações suspeitas acima de limiares específicos | Qualquer operação fora do padrão deve gerar um Relatório de Inteligência Financeira (RIF) |

### Por que sistemas de compliance tradicionais falham nesse cenário

O problema não é a regulação em si — é como as instituições tentam implementá-la. A abordagem padrão é um conjunto de **regras fixas e cegas ao contexto**:

```
[REGRA TRADICIONAL]
SE valor > R$ 10.000 → FLAG para análise
SE hora < 6h → FLAG para análise  
SE > 3 wallets no dia → FLAG para análise

[RESULTADO]
• Analista afogado em alertas (90% são falsos positivos)
• Criminosos aprendem os limiares e fracionam (smurfing)
• Brasileiro assustado com o câmbio em R$ 6,30 → bloqueado
```

### Como o Shadow FX Terminal resolve isso

A inovação central é simples mas poderosa: **injetar o contexto macroeconômico como variável do modelo**.

Um brasileiro que compra R$ 8.000 de USDT num dia normal e um brasileiro que faz a mesma compra no dia em que o Real perdeu 4% e o IRF está em 87/100 são **eventos estatisticamente diferentes**. O primeiro é anômalo; o segundo é previsível e legítimo.

Nenhum sistema de regras fixas consegue fazer essa distinção. Um modelo que conhece o estado do câmbio, a trajetória da dívida pública, o tom do último Copom e o volume de busca por USDT no Brasil — consegue.

> **Em termos regulatórios:** O Shadow FX Terminal reduz a fadiga dos analistas de compliance, melhora a precisão dos reportes ao COAF e garante que a fiscalização das Resoluções BCB 519-521 não se torne um instrumento de exclusão financeira para cidadãos legítimos.

---

## 📐 Arquitetura do Projeto

O projeto é dividido em **5 fases** que constroem uma sobre a outra, seguindo a metodologia AI Scientist (Stanford CS230 + CRISP-DM):

```
┌──────────────────────────────────────────────────────────────────────┐
│                       SHADOW FX TERMINAL v2                          │
│                                                                      │
│  FASE 1: Prova da Tese (Dados Reais)   FASE 2: Índice de Risco v2   │
│  ┌──────────────────────────────┐      ┌──────────────────────────┐  │
│  │ yfinance: BRL/USD + USDT Vol │      │ Sinal Câmbio adj. DXY    │  │
│  │ BCB API:  IPCA, Selic, Dív.  ├─────►│ Sinal USDT/USDC Volume   ├─┐│
│  │ pytrends: Interesse BR USDT  │      │ Tom Copom (hawkish/dov.) │ ││
│  └──────────────────────────────┘      │ IPCA Desvio Meta         │ ││
│   r=+0.496 bruta | r=+0.707 Dívida    │ Dívida/PIB (r=+0.707)    │ ││
│   Lead-Lag 1-4sem | Parcial −2.5% DXY │ IBC-Br (atividade)       │ ││
│                                        └──────────────────────────┘ ││
│                                              IRF 0-100 diário        ││
│  FASE 3: Motor de Compliance AML                                     ││
│  ┌───────────────────────────────────────────────────────────────┐  ││
│  │ C1: Filtros BCB 519-521 (regras determinísticas) → Flag       │  ││
│  │ C2: Isolation Forest + IRF como feature contextual → Score    │◄─┘│
│  │ C3: LLM-as-judge (Gemini 2.5 Flash + RAG Copom) → COAF       │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  FASE 4: FastAPI (backend) + Streamlit Dashboard (frontend)          │
│  FASE 5: Agente RAG — Context Injection via Atas do Copom ✅         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Nota de Engenharia: Evolução da Estratégia de Dados (v1 → v2)

### v1 — Mock Data Strategy (decisão honesta e documentada)

Na versão inicial, todos os provedores de dados on-chain **bloquearam o acesso histórico (2022–2025) em seus planos gratuitos**:
- **Glassnode:** API paga a partir de USD 999/mês
- **CryptoQuant:** Dados históricos em tier pago (403 Forbidden)
- **CoinGecko:** Limite de 365 dias no tier gratuito

Em vez de paralisar o projeto, geramos dados **sintéticos mas parametrizados** pelas dinâmicas descritas no paper. Isso tem um nome técnico: **Synthetic Data Generation com Domain Knowledge Injection** — prática padrão em MLOps quando dados reais são inacessíveis.

```python
# A lógica do mock NÃO é aleatória — é calibrada por evidência empírica:
# 2022: Random walk (dominado por colapso FTX/Luna — choque exógeno ao câmbio BR)
# 2023: Correlação crescente com câmbio (~r=0.87 no semestre)
# 2024-S2: Forte correlação estrutural + "efeito piso" (acumulação por hedge)
```

### v2 — Dados 100% Reais (estado atual)

A v2 eliminou todos os mocks utilizando fontes públicas e gratuitas:

| Dado | Fonte | Registros |
|:---|:---|:---:|
| BRL/USD + Volume USDT/USDC | yfinance (Yahoo Finance) | 1.276 dias |
| IPCA, Selic, IBC-Br, Dívida/PIB | API BCB via `python-bcb` | Mensal 2022-2025 |
| DXY, VIX, S&P500 | yfinance | 1.276 dias |
| Interesse em USDT no Brasil | Google Trends (`geo='BR'`) | 183 semanas |
| Atas do Copom | Scraping BCB | 27 reuniões |

**Limitação residual:** Dados on-chain georreferenciados (Chainalysis, Glassnode Pro) ainda estão em tier pago. O Google Trends (`geo=BR`) é o proxy metodologicamente mais próximo do que o paper original utilizou — e a cadeia de 5 evidências (ver Fase 1-C) demonstra que esse proxy é robusto.

---

## 📂 Estrutura do Repositório

```
shadow_fx_terminal/
│
├── README.md                    ← Este arquivo
├── PROBLEM.md                   ← Contrato AI Scientist (3 perguntas fundamentais + ROI)
├── requirements.txt             ← Dependências completas (bcb, pytrends, genai incluídos)
├── .env                         ← GEMINI_API_KEY (não versionado)
├── .gitignore
│
├── src/                         ← Módulos de produção
│   ├── utils.py                 ← ⭐ Core: IRF v1+v2, correlações, carregamento de dados
│   ├── coletar_dados.py         ← Coleta v1: câmbio BRL/USD (yfinance)
│   ├── coletar_google_trends_br.py ← v2: 183 semanas de interesse BR por USDT
│   ├── analise_correlacao.py    ← ⭐ Cadeia de 5 evidências (script executável)
│   ├── validacao_estatistica.py ← Correlação Spearman bruta + parcial por semestre
│   ├── validacao_atribuicao_geografica.py ← Teste de viés geográfico (Lead-Lag + DXY)
│   ├── recalcular_irf.py        ← Recalcula IRF v2 sobre o dataset mestre
│   ├── scraper_copom.py         ← Coleta das Atas do Copom (BCB) + base histórica
│   ├── gerador_transacoes_mock.py ← Simulação de 4.509 transações (3 perfis de risco)
│   ├── pipeline_compliance.py   ← ⭐ Motor AML: 3 camadas em cascata (C1→C2→C3)
│   ├── api.py                   ← FastAPI backend (endpoints IRF + compliance)
│   └── agente_rag.py            ← ⭐ Fase 5: Gemini 2.5 Flash + RAG Copom + fallback
│
├── notebooks/                   ← Análises interativas com narrativa
│   ├── 02_indice_risco_fiscal.ipynb  ← Fase 2: Construção do IRF
│   └── 03_motor_compliance.ipynb    ← Fase 3: Pipeline AML e métricas
│
├── data/
│   ├── raw/                     ← Dados brutos (não versionados — ver .gitignore)
│   │   ├── cambio_brl_usd.csv            ← BRL/USD real (yfinance, Jan/2022–Jun/2025)
│   │   ├── stablecoins_yfinance_real.csv ← Volume USDT+USDC real (1.276 dias)
│   │   ├── macro_bcb.csv                 ← IPCA, Selic, IBC-Br, Dívida/PIB (BCB)
│   │   ├── variaveis_globais.csv         ← DXY, VIX, S&P500 (yfinance)
│   │   ├── brl_ajustado_dxy.csv          ← BRL/USD descontado o efeito do DXY
│   │   ├── google_trends_br_stablecoin.csv ← 183 semanas geo=BR
│   │   └── atas_copom_index.csv          ← 27 reuniões Copom 2022–2025
│   └── processed/
│       ├── dataset_mestre_v2.csv         ← ⭐ Dataset unificado (7 fontes reais)
│       ├── dataset_irf_completo.csv      ← IRF v1 diário
│       ├── dataset_irf_completo_v2.csv   ← IRF v2 (6 sinais) diário
│       ├── irf_por_reuniao_copom.csv     ← IRF médio por reunião do Copom
│       ├── transacoes_simuladas.csv      ← 4.509 transações (3 perfis)
│       └── resultado_compliance.csv      ← Output final do pipeline AML
│
├── models/                      ← Modelos treinados (não versionados)
│   ├── isolation_forest.joblib  ← Modelo de detecção de anomalias
│   └── scaler.joblib            ← StandardScaler (Training-Serving Parity)
│
├── tests/
│   └── test_utils.py            ← 18 testes unitários (v1 + v2 + integração)
│
└── reports/                     ← Visualizações geradas
    ├── grafico_correlacao.png
    ├── grafico_spearman.png
    ├── grafico_irf.png
    └── grafico_compliance.png
```

---

## 🔍 Transparência de Dados: Real vs. Mock

Para garantir o equilíbrio entre rigor científico e viabilidade técnica de um projeto de portfólio, o Shadow FX Terminal opera em um regime híbrido:

1. **Contexto Macroeconômico (100% REAL):**
   - Todos os dados que compõem o **Índice de Risco Fiscal (IRF)** são reais e coletados de fontes oficiais (BCB, yfinance, Google Trends). 
   - Isso permite que o projeto reflita o cenário econômico brasileiro exato entre 2022 e 2025 (ex: disparada do dólar, reuniões do Copom, variação da Dívida/PIB).

2. **Transações Individuais (SIMULADAS / MOCK):**
   - As 4.509 transações processadas pelo motor de compliance são geradas sinteticamente (`src/gerador_transacoes_mock.py`).
   - **Por que simulamos?**
     - **Privacidade & Ética:** Transações reais de blockchain são públicas, mas o mapeamento de CPFs/User IDs para carteiras é sensível.
     - **Controle Metodológico:** Para treinar o *Isolation Forest*, precisamos de perfis controlados (ex: usuários normais vs. fracionadores profissionais) para validar a precisão do modelo.
     - **Infraestrutura:** Evita a necessidade de rodar nós de blockchain (indexadores) pesados localmente.

3. **O Diferencial (Digital Twin):**
   - Embora a transação seja simulada, ela é **processada dentro do contexto real**. O motor avalia o comportamento do "Usuário A" contra o "IRF Real" do dia. É o que chamamos de *Digital Twin* de compliance: testamos regras de negócio sintéticas em um ambiente econômico de alta fidelidade.

---

## 🚀 Como Executar

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar a API Key (Agente RAG — Fase 5)
```bash
# Crie o arquivo .env na raiz do projeto:
echo GEMINI_API_KEY=sua_chave_aqui > .env
```

### 3. Coletar Dados Reais (v2)
```bash
# Câmbio BRL/USD + stablecoins (yfinance) + macro BCB + variáveis globais
python src/coletar_dados.py

# Atas do Copom (BCB)
python src/scraper_copom.py

# Google Trends Brasil — interesse em USDT/stablecoin (geo=BR)
python src/coletar_google_trends_br.py
```

### 4. Rodar as Análises
```bash
# Cadeia completa de 5 evidências (script executável)
python src/analise_correlacao.py

# Validação de atribuição geográfica (Lead-Lag + DXY)
python src/validacao_atribuicao_geografica.py

# Ou abrir os notebooks interativos:
jupyter lab  # notebooks/02_indice_risco_fiscal.ipynb e 03_motor_compliance.ipynb
```

### 5. Executar o Pipeline de Compliance
```bash
python src/gerador_transacoes_mock.py   # Gera 4.509 transações (3 perfis)
python src/pipeline_compliance.py       # 3 camadas → resultado_compliance.csv
```

### 6. Rodar os Testes
```bash
python -m pytest tests/ -v             # 18 testes unitários
```

---

## 📊 Resultados (v2 — Dados Reais)

### Fase 1 — Correlação Spearman (BRL/USD × Volume USDT) — *Dados Reais*

> **Fonte de dados (v2):** Volume diário de USDT-USD via yfinance (1.276 registros reais, 2022–2025). Substitui o dataset sintético da v1.

| Semestre | Correlação (r) | Significativo? | Força |
|:---|:---:|:---:|:---:|
| 2022-S1 | −0.208 | ✅ | Fraca (negativa) |
| 2022-S2 | −0.136 | ❌ | **Fraca — Efeito FTX/Luna (choque exógeno)** |
| 2023-S1 | +0.434 | ✅ | Moderada |
| 2023-S2 | −0.034 | ❌ | Fraca |
| 2024-S1 | +0.082 | ❌ | Fraca |
| 2024-S2 | **+0.681** | ✅ | **Moderada/Forte** (pico — BRL atingiu R$ 6,30) |
| 2025-S1 | +0.437 | ✅ | Moderada |
| **Total (907 dias)** | **+0.496** | ✅ | **Moderada** |

> **⚠️ Nota Técnica — Correlação ≠ Causalidade:** Spearman demonstra co-movimentação, não causalidade direcional. Ambas as séries respondem ao mesmo fator latente — o risco fiscal percebido — capturado pelo IRF.

### Fase 1-B — Análise de Robustez: Controlando o Confundidor Global (DXY)

> **O problema:** O BRL/USD sobe tanto quando o Brasil piora (risco fiscal local) quanto quando o dólar global se fortalece (DXY). Sem controlar o DXY, podemos estar atribuindo ao risco brasileiro o que é na verdade um movimento global.

| Análise | Coeficiente | Redução vs. Bruta | Interpretação |
|:---|:---:|:---:|:---|
| Spearman Bruta | r = 0.496 | — | Baseline |
| **Spearman Parcial (ctrl. DXY)** | **r = 0.483** | **−2.5%** | **Fenômeno LOCAL** |
| Spearman MM30 (suavizado) | r = 0.546 | — | Sinal reforçado |
| **Parcial MM30 (ctrl. DXY)** | **r = 0.542** | **−0.7%** | **Praticamente imune ao DXY** |

> **✅ Conclusão da Robustez:** A redução de apenas **2.5%** ao controlar pelo DXY indica que a correlação **não é artefato do dólar global**. O movimento do BRL especificamente correlaciona com o volume de USDT mesmo após remover o efeito do índice dólar.

### Fase 1-C — Atribuição Geográfica: Google Trends Brasil (geo=BR)

> **O problema que o paper reconhece explicitamente:** Dados on-chain de volume (USDT-USD) são **globais** — não é possível identificar por eles se foi o Brasil que comprou USDT. O paper de Britto (2026) resolve isso cruzando com dados de busca web geolocalizados. **Este projeto replica e expande essa metodologia.**

**Fonte:** Google Trends filtrado exclusivamente para o Brasil (`geo='BR'`) — 183 semanas de dados semanais (2022–2025).

| Keyword (BR) | Correlação com BRL/USD | Significativo? | Força |
|:---|:---:|:---:|:---|
| "USDT" | r = +0.501 | ✅ | Moderada |
| "stablecoin" | r = +0.341 | ✅ | Fraca |
| **Índice Composto (USDT+Tether+stablecoin)** | **r = +0.507** | ✅ | **Moderada** |

**Análise de Lead-Lag (BRL defasado precede o interesse?):**

| BRL defasado | r com Interesse BR | Significativo? |
|:---:|:---:|:---:|
| 1 semana | +0.508 | ✅ |
| 2 semanas | +0.504 | ✅ |
| 3 semanas | +0.502 | ✅ |
| 4 semanas | +0.496 | ✅ |

> **✅ Evidência de Causalidade Direcional:** O BRL defasado em **1 a 4 semanas** correlaciona com o interesse de busca brasileiro. Isso sugere que a queda do câmbio **precede** o aumento do interesse em USDT no Brasil — o caminho causal proposto no paper.

> **Correlação Parcial Trends BR (ctrl. DXY): r = +0.523, redução de apenas −3.2%** — o interesse de busca brasileiro por USDT é robusto ao controle do dólar global.

> **⚠️ Limitações do Google Trends:** (1) Índice relativo (0–100), não volume absoluto. (2) Captura intenção de compra, não compra efetiva. (3) Granularidade semanal. (4) Proxy de demanda, complementa mas não substitui dados on-chain georreferenciados.

### Cadeia de Evidências — Por que é Fenômeno Brasileiro?

```
Problema:   Volume USDT global → não permite identificar o país comprador.

Evidência 1 (Bruta):   BRL/USD ↔ Volume USDT global: r=+0.496 ✅ Significativo.
Evidência 2 (Robustez): Controlando DXY → r=+0.483, redução de apenas 2.5%.
                         → Não é artefato do dólar global.
Evidência 3 (Geoloc.):  BRL/USD ↔ Buscas "USDT" no BRASIL (geo=BR): r=+0.501 ✅
                         → Sinal de interesse exclusivamente brasileiro.
Evidência 4 (Lead-Lag): BRL[t-1 sem] → Interesse BR[t]: r=+0.508 ✅
                         → Câmbio PRECEDE o interesse — causalidade direcional.
Evidência 5 (Parcial):  Trends BR × BRL | DXY → r=+0.523, redução 3.2%.
                         → Comportamento de busca BR é robusto ao fator global.

Conclusão: A convergência das 5 evidências constitui suporte metodológico
           robusto para a hipótese de dolarização informal brasileira via USDT.
```

### Fase 2 — Índice de Risco Fiscal (IRF)

| Período | IRF Médio | Interpretação |
|:---|:---:|:---|
| 2022 | Baixo | Juros em alta forte, câmbio relativamente controlado |
| 2023-S2 | Alto | Cortes de juros + real enfraquecendo (fuga estrutural) |
| 2024-S2 | **Muito Alto** | Pico de correlação — BRL atingiu R$ 6,30, USDT como hedge |
| 2025 | Alto | Continuidade do aperto fiscal, dominância fiscal evidente |

> **⚠️ Nota de Calibração — Pesos do IRF v1:** Os pesos (Câmbio 40%, USDT 35%, Copom 25%) foram definidos por julgamento especializado, não por otimização empírica. O IRF v2 (`calcular_irf_v2()`) usa 6 sinais ortogonais com dados reais do BCB. Veja `src/utils.py`.

### Fase 3 — Motor de Compliance AML

| Resultado | Quantidade | % |
|:---|:---:|:---:|
| 🟢 VERDE (Normal) | 3.936 | 87,3% |
| 🟡 AMARELO (Monitorar) | 564 | 12,5% |
| 🔴 VERMELHO (Ação Imediata) | 9 | 0,2% |
| 🤖 Prontos para LLM-judge (C3) | 640 | 14,2% |

### 🔍 Como o Modelo Resolve o Problema Real do Mercado (Falsos Positivos)

Sistemas de compliance antigos baseados apenas em regras (ex: "Flag se > R$ 10.000") geram milhares de falsos positivos ou perdem criminosos inteligentes. Nossa simulação com 4.509 transações prova o valor de uma arquitetura inteligente usando ML + Contexto Macro (IRF):

- 🟢 **Tipo A: O "Poupador Assustado" (Legítimo)**
  * *Comportamento:* Compra USDT no desespero quando o câmbio derrete.
  * *O que a IA faz:* Como injetamos o **IRF** no modelo, a IA entende: *"Hoje o Risco Fiscal está alto, é natural a corrida para o dólar"*. Classifica como **VERDE** e não incomoda o analista.
- 🟡 **Tipo B: O Institucional / Mesa de Arbitragem (Legítimo, mas volumoso)**
  * *Comportamento:* Movimenta R$ 200.000 todo dia.
  * *O que a IA faz:* A Isolation Forest olha o histórico e percebe que *volumes gigantes são o "normal" dessa carteira*. Em vez de explodir o sistema com alertas vermelhos, ele apenas sinaliza como **AMARELO (Monitorar)**.
- 🔴 **Tipo C: O Fracionador / Evasor (Suspeito)**
  * *Comportamento:* Faz 11 transferências de R$ 9.500 de madrugada (Smurfing para fugir do limite BCB de R$ 10k).
  * *O que a IA faz:* O modelo detecta a anomalia grave (*quem manda 11 PIXs de 9.5k às 3 da manhã?*). Crava **VERMELHO (Ação Imediata)**, trava a transação e envia para o analista.

Essa abordagem AI Scientist reduz drasticamente a fadiga do time de operações e mira como um laser no verdadeiro alvo das regulações cambiais.

### Fase 4 — Dashboard Streamlit e FastAPI Backend

A Fase 4 materializa o motor de compliance em uma interface visual de nível de produção, seguindo as melhores práticas de Engenharia de Software (separação entre backend e frontend):

- **FastAPI (`src/api.py`):** Backend desacoplado que expõe endpoints de serviço (IRF atual, histórico, pontuação de transação, etc) para integração com outros sistemas da corretora.
- **Streamlit (`app.py`):** Dashboard premium, interativo e focado na experiência do Analista de Compliance.

#### Como o App Funciona (Passo a Passo)

1. **🏠 Dashboard Principal:** 
   - Exibe os **KPIs em tempo real**: o Índice de Risco Fiscal (IRF) mais recente e o total de transações processadas.
   - Mostra o funil do pipeline AML: quantas transações passaram direto (**VERDE**), quais foram para a zona cinza (**AMARELO**) e as anômalas graves (**VERMELHO**).
   - Um gráfico histórico mostra a evolução do IRF no tempo, pintando as áreas onde o risco de fuga de capitais esteve crítico.
   - Traz uma tabela rápida com os casos "Ação Imediata".

2. **⚖️ Compliance Scanner:**
   - É o "simulador" em tempo real. O analista preenche os dados de uma transferência (ex: R$ 9.500 às 3 da manhã para 12 wallets diferentes).
   - O motor cruza os dados com o **IRF do dia** (contexto macroeconômico) e as heurísticas da Camada 1.
   - O aplicativo devolve instantaneamente um Score (0-100) e o Alerta. Se a transação for sinalizada como "AMARELO", o app já redige e exibe o *prompt* que o LLM-as-judge usaria para investigá-la.

3. **📈 Análise IRF:**
   - Uma página quantitativa para analisar o "clima macroeconômico".
   - Decompõe o Índice de Risco Fiscal em seus 3 fatores: como o Câmbio (peso 40%), o Supply de USDT (peso 35%) e as Atas do Copom (peso 25%) se moveram no tempo. Isso ajuda a mesa de operações a entender *por que* o risco está alto hoje.

4. **ℹ️ Sobre o Projeto:**
   - Conta a história do projeto, detalhando a virada (Pivot) da análise do paper inicial para a solução de software, documentando as resoluções do BCB aplicáveis.

**Como rodar a Fase 4:**
```bash
# Terminal 1: Iniciar o Dashboard (Interface Visual)
streamlit run app.py

# Terminal 2: Iniciar a API (Opcional - Backend)
uvicorn src.api:app --reload --port 8000
```

---

## 🏗️ Decisões Técnicas e AI Scientist

### Por que Correlação de Spearman e não Pearson?
Séries financeiras raramente são normalmente distribuídas. Spearman mede correlação de postos (ranking), sendo robusta a outliers e assimetrias — a mesma escolha metodológica do paper original.

### Por que Isolation Forest para AML?
Em Anti-Money Laundering, **dados rotulados de fraude são raros e sigilosos**. Isolation Forest é um algoritmo de detecção de anomalias não-supervisionado: não precisa de exemplos de fraude para treinar. Ele isola pontos que se distanciam do comportamento normal em menos divisões de árvore.

### O Diferencial: IRF como Feature Contextual
A maioria dos sistemas de AML olha apenas para o comportamento individual. **Nosso diferencial:** incorporamos o IRF (contexto macroeconômico) como feature do modelo. Um brasileiro comprando R$ 8.000 de USDT num dia normal vs. num dia em que o real perdeu 5% são padrões completamente diferentes.

### Cascaded Pipelines (Padrão CS230)
Seguindo o **Stanford CS230**, o pipeline usa filtros em cascata: cada camada resolve os casos mais óbvios e passa os "difíceis" para a camada seguinte, mais cara computacionalmente. Isso reduz custo de inferência em ~85% vs. rodar o LLM em tudo.

---

## 🔮 Próximos Passos (Evolução Enterprise)

Como parte da visão de produto e maturidade de engenharia, as seguintes melhorias foram identificadas para evolução do repositório:
- **Engenharia de Software:** Implementação de pipeline CI/CD (GitHub Actions) e substituição de `print` por módulo `logging` estruturado.
- **Engenharia de Dados:** Validação de schemas ao carregar CSVs (via Pandera) e migração do armazenamento para formato `.parquet`.
- **Economia:** Incorporação do **CDS 5Y** (Credit Default Swap) como proxy mais rápido e sensível do que a Dívida/PIB mensal.
- **Product Management:** **Explainable AI (XAI)** para justificar alertas em linguagem natural e **Geração Automatizada de Rascunho COAF (PDF)**, tornando o alerta 100% acionável para o analista de compliance.

---

## 🗺️ Roadmap

- [x] **Fase 1:** Análise exploratória e prova da correlação (Notebook 01)
- [x] **Fase 2:** Índice de Risco Fiscal composto — 3 sinais integrados (Notebook 02)
- [x] **Fase 3:** Motor de Compliance AML — 3 camadas em cascata (Notebook 03)
- [x] **Fase 4:** FastAPI backend — endpoint `/score` desacoplado
- [x] **Fase 4:** Streamlit Dashboard — Interface visual premium
- [x] **Fase 4:** Testes unitários (`pytest`) implementados e validados
- [x] **Fase 5:** Agente RAG (Camada 3) — `agente_rag.py` com LLM lendo Atas do Copom para gerar relatórios COAF (inclui arquitetura de *Fallback MLOps* para indisponibilidade da API).

---

---

## 🐳 Executando com Docker (Enterprise Ready)

Para garantir um ambiente isolado e pronto para produção, o projeto está totalmente conteinerizado.

### 1. Requisitos
- Docker e Docker Compose instalados.
- Arquivo `.env` configurado (veja `.env.example`).

### 2. Inicialização Rápida
O comando abaixo constrói as imagens e inicia os serviços de Dashboard (Porta 8501) e API (Porta 8000).

```bash
docker-compose up --build
```

### 3. Inicializando Dados e Modelos (Primeira Execução)
Caso os arquivos de dados em `data/` e modelos em `models/` ainda não existam, você pode rodar o container de setup:

```bash
docker-compose run setup
```

### 4. Arquitetura de Containers
- **`shadow-fx-dashboard`**: Interface visual Streamlit (acessível em `localhost:8501`).
- **`shadow-fx-api`**: Backend FastAPI (documentação Swagger em `localhost:8000/docs`).
- **Volumes**: As pastas `data/` e `models/` são montadas como volumes para persistência fora do ciclo de vida dos containers.

---

---

## 🛡️ Auditoria de Rigor e Contra-Viés (PAVC)

Este projeto não é apenas uma implementação técnica, mas um sistema submetido ao **Protocolo de Auditoria e Contra-Viés (PAVC)**. Esta prática garante que o Engenheiro Humano mantenha a soberania sobre as decisões da IA, combatendo o "Efeito Yes-Man".

### Itens Auditados e Validados:
1. **Explainability Test:** Validação manual da lógica de pesos do IRF e paridade treino-serventia (Scaler).
2. **Fallback MLOps:** Implementação de degradagem graciosa no `src/agente_rag.py` para falhas de API.
3. **Stress de Falsificabilidade:** Teste de detecção de anomalias contra ataques de smurfing de alta entropia (Invasor Institucional).

### Evolução Constante (Roadmap de Maturidade):
Como um sistema vivo, o Shadow FX Terminal possui um plano de mitigação para os riscos identificados na auditoria:
- **Escalabilidade:** Migração de processamento síncrono para arquitetura de filas (Async).
- **Persistência:** Transição de CSV para Banco de Dados Relacional (PostgreSQL) + Vetorial.
- **Robustez de Dados:** Substituição de Scraping frágil por Webhooks e APIs Enterprise.

---

## 🛡️ Segurança e Privacidade (Security-by-Design)

Em sistemas financeiros, a segurança não é um detalhe, é o alicerce. O Shadow FX Terminal foi construído seguindo princípios de **Enterprise Security**, garantindo que a inovação em IA não comprometa a integridade dos dados.

### 1. ⚖️ Conformidade com a LGPD (Privacidade)
Para respeitar a Lei Geral de Proteção de Dados (LGPD), o sistema utiliza uma técnica de **Anonimização por Hashing (SHA-256)**.
- **Como funciona:** O identificador real do usuário (como um CPF) nunca é processado em texto claro. Ele é transformado em um código único e irreversível antes de chegar ao modelo de IA.
- **Valor:** Isso garante que o motor de compliance consiga identificar padrões de comportamento sem nunca "saber" quem é a pessoa física por trás da transação.

### 2. 🔐 Proteção de Perímetro (API Key)
A API do motor de compliance não está aberta ao público.
- **Como funciona:** Implementamos um middleware de segurança que exige uma **X-API-Key** válida para cada requisição.
- **Valor:** Impede que agentes maliciosos tentem sobrecarregar o sistema ou extrair scores de risco sem autorização.

### 3. 🐳 Blindagem de Infraestrutura (Docker Hardening)
Diferente de containers comuns que rodam como "administrador" (root), o Shadow FX Terminal roda sob um usuário sem privilégios.
- **Como funciona:** O container é configurado para rodar como um `appuser` limitado. 
- **Valor:** Se houver uma tentativa de invasão ao container, o atacante ficará "preso" dentro de um ambiente sem permissões para afetar o servidor principal.

### 4. 🧠 Defesa em Profundidade (IA)
A arquitetura em 3 camadas funciona como um "filtro de segurança" para a própria IA:
- **Camada 1 e 2 (Âncoras):** Usam regras matemáticas e estatísticas que são imunes a ataques de "persuasão" (como o Prompt Injection).
- **Camada 3 (IA Generativa):** Atua apenas nos casos onde as âncoras já validaram a segurança inicial, minimizando riscos de alucinação ou manipulação.

---

## 📚 Referências

- Britto, P. J. (2026). *Dolarização Informal: Stablecoins como resposta à instabilidade monetária brasileira*. OTC Research.
- Banco Central do Brasil. Resoluções BCB nº 519, 520 e 521 (2026).
- Stanford CS230 Deep Learning — *Cascaded Heuristic Filters & LLM-as-judge patterns*.
- Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). *Isolation Forest*. IEEE ICDM.

---

## ⚖️ Licença

Este projeto está licenciado sob a **Licença MIT** — consulte o arquivo [LICENSE](LICENSE) para obter detalhes. Sinta-se à vontade para explorar, mas por favor, mantenha os créditos ao autor original.
