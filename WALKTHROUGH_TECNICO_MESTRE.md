# 🎓 Masterclass Técnica Profunda: Shadow FX Terminal
**Data:** 17 de Maio de 2026

---

## 🏛️ Introdução: O Paradigma do Cientista de Dados & AI Engineer

Para entender o **Shadow FX Terminal**, é preciso compreender a interseção de duas disciplinas cruciais da inteligência artificial moderna: a **Ciência de Dados (Data Science)** e a **Engenharia de IA (AI Engineering)**. 

No mercado corporativo atual, o maior gargalo não é a criação de modelos preditivos, mas sim a sua **produtização sob rigor estatístico, de conformidade regulatória e de segurança**. Este projeto foi desenhado para romper o abismo entre o laboratório experimental (notebooks) e o ambiente de produção em tempo real (APIs e dashboards), servindo como a consolidação prática e avançada do meu processo de estudo e aprendizado contínuo na **Pós Tech AI Scientist**.

| Dimensão | O Cientista de Dados Tradicional | O AI Engineer de Produção | A Abordagem Shadow FX Terminal |
| :--- | :--- | :--- | :--- |
| **Foco Principal** | Modelagem experimental, validação estatística e hipóteses em Jupyter Notebooks. | Arquitetura de software, latência, segurança, integrações e entrega do sistema. | **Rigor Científico + Solidez de Engenharia:** Análise macroeconômica validada estatisticamente alimentando um pipeline em cascata robusto. |
| **Artefato de Entrega** | Um arquivo `.ipynb` com gráficos estáticos e uma acurácia teórica alta. | Uma API conteinerizada (`Dockerfile`), testes unitários e infraestrutura pronta. | **Sistema Ponta a Ponta:** Três notebooks CRISP-DM de pesquisa pareados com módulos `.py` modulares, FastAPI, Streamlit Dashboard e Docker seguro. |
| **Gestão de Risco** | Assume que os dados de teste sempre representarão o futuro do mercado. | Cria fallbacks caso a API do LLM caia ou sofra timeout no pipeline de transações. | **Defesa em Profundidade:** Pipeline em 3 camadas com fallback heurístico para manter a operação viva mesmo se a IA falhar. |
| **Interpretabilidade** | Gráficos SHAP complexos que apenas outros cientistas de dados conseguem decifrar. | Exposição crua de scores numéricos em um banco de dados de log. | **Explainable AI (XAI) Human-Centric:** O LLM traduz a anomalia estatística da IA em uma justificativa clara em português e gera o rascunho de reporte regulatório do COAF. |

---

## 🗺️ Guia de Navegação: Como Auditar e Entender este Repositório

Para guiar recrutadores, arquitetos de soluções e líderes de tecnologia, o repositório é dividido estritamente em duas frentes complementares:

### 1. A Trilha do Cientista de Dados (Exploração e Rigor Estatístico)
Se o seu objetivo é auditar o **rigor matemático e a modelagem**, navegue pelos notebooks CRISP-DM:
*   [01_analise_correlacao.ipynb](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20(1)/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/notebooks/01_analise_correlacao.ipynb): Estudo de cointegração e estacionaridade das séries financeiras (DXY, BRL, Google Trends) utilizando testes de raiz unitária **Augmented Dickey-Fuller (ADF)**. Prova estatística da tese macroeconômica.
*   [02_indice_risco_fiscal.ipynb](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20(1)/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/notebooks/02_indice_risco_fiscal.ipynb): Engenharia do **IRF (Índice de Risco Fiscal)**. Uso de **Principal Component Analysis (PCA)** para extrair componentes ortogonais dos indicadores fiscais brasileiros, gerando pesos matematicamente justificados e eliminando o viés humano.
*   [03_motor_compliance.ipynb](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20(1)/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/notebooks/03_motor_compliance.ipynb): Arena de benchmarks de detecção de anomalias (benchmark entre *Isolation Forest*, *LOF* e *One-Class SVM*).

### 2. A Trilha do AI Engineer (Engenharia de Sistemas e IA Generativa)
Se o seu objetivo é auditar a **arquitetura de software e MLOps**, explore a estrutura de produção em `src/`:
*   [pipeline_compliance.py](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20(1)/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/src/pipeline_compliance.py): O coração do sistema. Implementação do pipeline de decisão em 3 camadas (Heurísticas regulatórias BCB -> Machine Learning não-supervisionado -> LLM-as-a-Judge).
*   [agente_rag.py](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20%281%29/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/src/agente_rag.py): Agente inteligente que realiza busca semântica em banco de dados temporal (Atas do COPOM) para contextualizar a decisão com macroeconomia.
*   [api.py](file:///c:/Users/Tchan%20%281%29/Documents/Base_de_Conhecimento/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/src/api.py): API FastAPI de alto throughput expondo o motor de análise em tempo real com validações robustas do Pydantic.
*   [app.py](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20%281%29/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/app.py): Interface reativa Streamlit em Dark Mode, expondo o Compliance Scanner com logs de auditoria e geração automática de relatórios prontos para o COAF.
*   [Dockerfile](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20%281%29/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/Dockerfile) & [docker-compose.yml](file:///c:/Users/Tchan/Documents/Base_de_Conhecimento%20%281%29/PROJETOS/02_PORTFOLIO/shadow_fx_terminal/docker-compose.yml): Infraestrutura dockerizada segura e escalável, aplicando práticas de hardening (non-root users).

---

> [!IMPORTANT]
> **A Tese de Negócio Resolvida:**
> Em tempos de instabilidade fiscal, as stablecoins (USDT) se comportam de forma legítima como um hedge cambial contra o risco fiscal do país (perfil do "Poupador"). Em tempos normais de estabilidade, transações volumosas e descorrelacionadas fora de horário sugerem ocultação de patrimônio ou lavagem de dinheiro (perfil do "Lavador"). O Shadow FX Terminal separa esses dois perfis cientificamente injetando o contexto macroeconômico (IRF) diretamente na tomada de decisão da IA.

---


## 📂 Pilar 1: Arquitetura de Software (Por que `.py` e não apenas Notebooks?)

Muitos iniciantes perguntam: *"Se o código funciona no Notebook, por que criar pastas como `src/` e arquivos `utils.py`?"*

### A Resposta: O Cemitério de Código (Context Rot)
Notebooks são excelentes para **exploração**, mas péssimos para **produção**.
1.  **Reutilização (DRY - Don't Repeat Yourself):** Se você define uma função de limpeza de dados no Notebook 1, e precisa dela no Notebook 2, você acaba copiando e colando. Se descobrir um bug, terá que corrigir em dois lugares.
2.  **Paridade Treino-Serventia (Training-Serving Parity):** Em ML, o maior erro é processar os dados de um jeito na hora de treinar e de OUTRO jeito na hora que a API recebe uma transação real. 
    - Ao isolar a lógica em `src/utils.py`, garantimos que o modelo e a API usem **exatamente o mesmo código**.

### A Estrutura de Pastas:
*   **`src/` (Source):** Onde mora o código "vivo". São módulos Python que podem ser importados por qualquer lugar.
*   **`utils.py` (A Central de Inteligência):** Aqui isolamos funções puras (sem efeitos colaterais). Se mudarmos a forma como o IRF é calculado aqui, ele muda automaticamente no Dashboard, na API e nos Notebooks.
*   **`notebooks/`:** Usados apenas como "rascunhos de luxo" para visualização e prototipagem rápida.

---

## 🧪 Pilar 2: Engenharia de Dados e a "Estratégia de Dados Reais"

No mundo real, dados on-chain (como supply de USDT) são caros (APIs de $1.000/mês). 

### A Estratégia Híbrida (Mock vs. Real):
1.  **Fase de Mock (v1):** Usamos dados sintéticos para desenhar a arquitetura. **Mas atenção:** não eram dados aleatórios. Usamos **Domain Knowledge Injection**. Calibramos o mock para seguir a tese de Paulo J. Britto (2026): correlação baixa em 2022 (choque FTX) e correlação alta em 2024 (crise fiscal).
2.  **Fase Real (v2):** Substituímos os mocks por dados do **Yahoo Finance (yfinance)**, **BCB** e **Google Trends**. 
    - **Termo Técnico: Proxy de Demanda.** Como não temos o volume exato de brasileiros comprando USDT (isso é sigilo das corretoras), usamos o Google Trends Brasil como um *proxy*. Se as buscas sobem após o dólar subir, temos uma evidência estatística de demanda.

---

## ⚙️ Pilar 3: Deep Dive no Código (Micro e Macro)

Vamos analisar os componentes vitais e o "porquê" de cada decisão técnica.

### 🧠 3.1. `utils.py`: O Cálculo do IRF v2
O Índice de Risco Fiscal é o diferencial do projeto. Ele não olha apenas para o preço do dólar.

```python
# Em src/utils.py
def calcular_irf_v2(divida_pib_var, brl_adj_dxy, ...):
    # Sinal 1: Dívida/PIB (Dominância Fiscal)
    # Se a dívida sobe, o investidor teme o calote ou inflação e foge para o USDT.
    sinal_divida = min(max(divida_pib_var / 0.12, 0), 1)

#### O Rigor Estatístico (PCA & ADF)
No nível sênior, não inventamos pesos. 
-   **PCA (Principal Component Analysis):** Usamos para provar que os 6 sinais do IRF são ortogonais e para derivar os pesos matematicamente, evitando o viés humano.
-   **Teste ADF (Stationarity):** Provamos que nossas séries financeiras são estacionárias (via log-retornos) antes de calcular correlações, eliminando o risco de "Correlação Espúria".
```python
# Sinal 2: BRL Ajustado pelo DXY
# Aqui removemos o efeito do dólar global para isolar o "Risco Brasil Puro".
```
**Por que normalizar para 0-100?** Para que o score seja interpretável por humanos. Um analista de compliance entende "Risco 85", mas não entende "Variação logarítmica de 0.045".

### 🛡️ 3.2. `pipeline_compliance.py`: A Cascata de Filtros
Aqui aplicamos o padrão de **Stanford CS230**.

#### Camada 1: Heurísticas (Filtros Baratos)
```python
def camada1_filtros_bcb(df):
    # R1: Transação >= R$ 10.000
    # Por que 10k? Porque é o limite regulatório das Resoluções 519-521.
    # Se bater 10k, o sistema já acende a luz amarela antes mesmo de rodar IA.
```

#### Camada 2: Isolation Forest (Detecção de Anomalias)
**O que é:** Imagine que você desenha um círculo em volta de todas as transações normais. Aquelas que ficam muito longe do círculo são "isoladas".

```python
# Injeção de Contexto Sênior
FEATURES_ML = ["valor_brl", "n_transacoes_dia", "irf_contexto", "entropia_wallets"]
#🤔 POR QUÊ: 
# 1. 'irf_contexto' ensina a IA que o normal muda na crise.
# 2. 'entropia_wallets' detecta Smurfing (dispersão de valores).
```
---

### 🏛️ 3.3. A Arena de Modelos (Benchmark)
Um sênior não escolhe um modelo "porque sim". Nós construímos uma **Arena de Modelos** (Notebook 03):
1.  **Isolation Forest:** Campeã por escalabilidade e eficácia em dados globais.
2.  **LOF (Local Outlier Factor):** Ótima para outliers locais, mas instável em larga escala.
3.  **One-Class SVM:** Robusta, porém lenta para pipelines de alta frequência (Pix/Crypto).

**Resultado:** A *Isolation Forest* foi escolhida após benchmark de performance e interpretabilidade (XAI).

---

## 🤖 Pilar 4: IA Agêntica e RAG (A Fronteira)

### `src/agente_rag.py`
Aqui o projeto entra no nível **Software 3.0**. Usamos o LLM não para "chatear", mas para **decidir**.

#### O Processo RAG (Temporal):
1.  **Recuperação:** O código olha a data da transação (ex: 15/09/2024).
2.  **Busca:** Ele vai no arquivo `atas_copom_index.csv` e busca a Ata do Copom mais próxima.
3.  **Injeção:** Ele coloca o texto da Ata no prompt: *"Dado que o Copom disse isso [ATA], analise essa transação [DADOS]"*.

#### MLOps e Robustez:
```python
except Exception as e:
    # Por que o Fallback? 
    # Porque APIs podem falhar ou ficar lentas. Um sistema de compliance 
    # não pode travar a corretora se o Gemini estiver fora do ar.
    return _fallback_heuristico(transacao)
```

---

## 🐳 Pilar 5: Deploy e Segurança (Enterprise Ready)

### Docker Hardening:
No nosso `Dockerfile`, aplicamos práticas de segurança de nível bancário:
```dockerfile
RUN useradd -m appuser
USER appuser
```
**Por que?** Se você rodar como `root` e alguém explorar uma vulnerabilidade no seu app (ex: Prompt Injection), ele terá controle total do servidor. Rodando como `appuser`, o invasor fica "preso" em um ambiente sem permissões.

---

## 🤝 Aprendizado Contínuo, Pós Tech AI Scientist & Peer Review

Este projeto é um organismo vivo e reflete diretamente minha jornada de **estudo e aprimoramento contínuo**. Como aluno da **Pós Tech AI Scientist**, acredito que a soberania técnica não reside em saber tudo, mas na capacidade de pesquisar com rigor, experimentar incansavelmente e abraçar a mentalidade de melhoria constante.

Nenhum código é perfeito e nenhuma arquitetura de dados é imutável. A verdadeira engenharia de software e a ciência de dados avançam por meio da colaboração e do debate saudável. 

### 📢 Estou Aberto a Críticas, Sugestões e Melhorias!
Se você é um cientista de dados, engenheiro de IA, arquiteto de software ou entusiasta do mercado financeiro, a sua perspectiva é extremamente valiosa para mim:
*   **Encontrou um gargalo?** Tem alguma sugestão para otimizar a latência da detecção em cascata no `pipeline_compliance.py`?
*   **Melhoria estatística?** Acha que podemos testar outros proxies macroeconômicos além do Google Trends para o cálculo do IRF?
*   **Refatoração?** Viu alguma oportunidade de tornar o RAG agêntico em `agente_rag.py` ainda mais resiliente?

> [!TIP]
> **Como colaborar:**
> Sinta-se totalmente convidado a abrir uma **Issue**, sugerir uma refatoração ou submeter um **Pull Request**. Feedbacks técnicos e revisões de código de outros profissionais são os maiores aceleradores de crescimento técnico que existem. Vamos evoluir juntos!

---

## 🏁 Conclusão: A Soberania do AI Engineer

Neste projeto, a barreira do código experimental foi superada. O Shadow FX Terminal demonstra como:
1.  **Arquitetar** um ecossistema proditizável, modular e robusto.
2.  **Calibrar** teses econômicas com validação estatística e proxies do mundo real.
3.  **Implementar** defesa cibernética em profundidade (Cascata regulatória + ML + RAG).
4.  **Garantir** a continuidade do negócio com sistemas de fallback tolerantes a falhas.

**Esta profundidade atende ao seu novo padrão de base de conhecimento? Se sim, adote o "Protocolo Maibashi" para seus próximos projetos.**

