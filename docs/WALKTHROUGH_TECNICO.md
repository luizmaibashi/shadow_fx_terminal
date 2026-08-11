# Walkthrough técnico — Shadow FX Terminal

Este documento é o mergulho fundo no "porquê" de cada decisão técnica do projeto. Se você quer só entender o que o projeto faz, leia o [README](../README.md) e o [PROBLEM.md](../PROBLEM.md) primeiro — este arquivo é para quem quer auditar a engenharia por trás.

---

## Por que `.py` e não só notebook?

Notebook é ótimo pra explorar, ruim pra produção, por dois motivos concretos:

1. **Reuso.** Se a função de limpeza de dado é definida no Notebook 1 e precisa dela no Notebook 2, ou copia e cola (e daí um bug corrigido num lugar continua vivo no outro), ou extrai pra módulo.
2. **Paridade treino-serventia.** O erro mais comum em ML é processar o dado de um jeito no treino e de outro jeito quando a API recebe uma transação real. Isolando a lógica em `src/utils.py`, o modelo, a API e os notebooks usam exatamente o mesmo código — não uma cópia parecida.

A estrutura reflete isso: `src/` é onde mora o código vivo, `utils.py` concentra as funções puras (sem efeito colateral) que tudo mais importa, e `notebooks/` fica só pra prototipagem e narrativa visual.

---

## A estratégia de dado: mock calibrado, depois dado real

Dado on-chain de verdade (supply de USDT, volume georreferenciado) custa caro — Glassnode cobra a partir de USD 999/mês. A saída, na v1, não foi usar dado aleatório: foi calibrar o mock pela tese de Britto (2026) — correlação baixa em 2022 (choque FTX/Luna) e correlação alta em 2024 (crise fiscal). Isso é injeção de conhecimento de domínio num gerador sintético, uma prática normal quando o dado real está fora de alcance.

Na v2 os mocks de contexto macro saíram e entrou dado real: yfinance, API do BCB, Google Trends. Como não existe volume exato de brasileiro comprando USDT (isso é sigilo de corretora), o Google Trends com `geo='BR'` funciona como proxy de demanda — se a busca sobe depois que o dólar sobe, isso é evidência estatística de interesse, não prova direta de compra.

---

## O cálculo do IRF (`src/utils.py`)

O Índice de Risco Fiscal é o diferencial do projeto — ele não olha só o preço do dólar, olha 6 sinais ortogonais (câmbio ajustado por DXY, volume de USDT, tom do Copom, desvio da meta de IPCA, dívida/PIB, IBC-Br) e resume tudo num número de 0 a 100.

Os pesos não foram escolhidos no chute: o notebook `02_indice_risco_fiscal.ipynb` usa PCA (Análise de Componentes Principais) pra provar que os 6 sinais são razoavelmente ortogonais entre si e derivar peso matematicamente, e o notebook `01_analise_correlacao.ipynb` usa o teste ADF de estacionaridade pra evitar correlação espúria antes de qualquer conclusão sobre as séries financeiras.

Normalizar pra 0-100 é decisão de produto, não só de estatística: um analista de compliance entende "risco 85", não entende "variação logarítmica de 0,045".

---

## A cascata de filtros (`src/pipeline_compliance.py`)

O pipeline segue o padrão de filtros em cascata do Stanford CS230 — cada camada resolve o caso óbvio e só passa adiante o que precisa de mais.

**Camada 1 — regra determinística.** `camada1_filtros_bcb()` aplica os limiares das Resoluções BCB 519-521 (por exemplo, R1 dispara acima de R$ 10.000, porque é o limite regulatório). Se bater o limiar, o sistema já sinaliza antes mesmo de rodar qualquer modelo.

**Camada 2 — Isolation Forest.** A intuição é simples: desenhe um círculo em volta do comportamento normal — o que fica muito longe do centro é isolado com menos divisões de árvore. As features (`FEATURES_ML` em `utils.py`) incluem `irf_contexto` (ensina o modelo que "normal" muda em dia de crise) e `entropia_wallets` (ajuda a pegar smurfing, que é dispersão deliberada de valor entre carteiras).

**Por que Isolation Forest e não LOF ou One-Class SVM?** O notebook `03_motor_compliance.ipynb` roda os três numa arena de benchmark. Isolation Forest venceu em escalabilidade e interpretabilidade — LOF é boa em outlier local mas instável em escala grande, One-Class SVM é robusta mas lenta demais pra um pipeline de alta frequência. O detalhe completo do trade-off está em `docs/adr/0001-isolation-forest-vs-lof-svm.md`.

---

## O agente RAG (`src/agente_rag.py`)

Aqui o LLM não conversa, decide — mais especificamente, ajuda a decidir só nos casos que já passaram pelas duas camadas anteriores e ainda ficaram em zona cinza.

O processo, na prática: o código olha a data da transação, busca no `atas_copom_index.csv` a ata do Copom mais próxima daquela data, e injeta o texto dela no prompt — "dado que o Copom disse isso, analise essa transação". É RAG temporal: a recuperação depende de quando a transação aconteceu, não de busca semântica livre.

O fallback importa tanto quanto o caminho feliz: se a API do Gemini cair ou demorar, `_fallback_heuristico()` assume, porque um sistema de compliance não pode travar a operação da corretora se o provedor de LLM estiver fora do ar.

---

## Docker e hardening

O `Dockerfile` roda como `appuser`, não como `root`:

```dockerfile
RUN useradd -m appuser
USER appuser
```

Se alguém encontrar uma vulnerabilidade no app (por exemplo, uma tentativa de prompt injection na Camada 3) e conseguir executar código dentro do container, rodando como root o atacante teria controle total do servidor. Como `appuser`, ele fica preso num ambiente sem permissão pra afetar o que está fora do container.

---

## Sobre o projeto

Este é um projeto de estudo, montado durante a Pós Tech AI Scientist, e continua em evolução — os débitos técnicos conhecidos estão documentados em `AGENTS.md`, não escondidos. Se você tem sugestão técnica — outro proxy macroeconômico pro IRF, uma forma melhor de medir latência da cascata, um jeito mais robusto de fazer o RAG do agente — abra uma issue ou um PR. Feedback de quem já resolveu esse tipo de problema em produção vale mais que qualquer refino que eu faria sozinho.
