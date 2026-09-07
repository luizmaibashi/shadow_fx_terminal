# AGENTS.md — Shadow FX Terminal

Pipeline de compliance AML pra stablecoin, com contexto macroeconômico (IRF) injetado no modelo.

**Stack:** Python, Pandas, Scikit-Learn, FastAPI, Streamlit, Gemini 2.5 Flash
Atualizado em 2026-08-11 via `/grill-with-docs` (Blind Spot Pass + sabatina), depois de `/tese` e `/wayfinder` na mesma linha de trabalho. A versão original foi preservada em espírito; as seções novas estão marcadas.

---

## Mapa do projeto

- `src/` — código de produção (utils, pipeline, API, agente RAG) + scripts de coleta/preparação de dado
- `tools/` — scripts de geração de asset pra apresentação (screenshot, diagrama, PDF). Não fazem parte do pipeline, não têm teste, não rodam em produção. Separados de `src/` em 2026-08-11
- `notebooks/` — 3 notebooks CRISP-DM (correlação, IRF, arena de modelos)
- `app.py` — dashboard Streamlit (frontend)
- `docs/adr/` — Architecture Decision Records
- `docs/audit/` — auditorias (PAVC, auditoria v2)
- `docs/tese/` — sabatinas de valor/vantagem competitiva (`/tese`)
- `docs/wayfinder/` — decomposição de escopo nebuloso em ticket (`/wayfinder`)
- `tests/` — testes unitários, 3 arquivos
- `models/` — artefatos treinados (`isolation_forest_v1.joblib`, `scaler_v1.joblib`, `score_calibracao_v1.joblib`)
- `data/` — dado bruto e processado, não versionado
- `deploy/hf_space/` — pacote isolado do demo público (Streamlit Community Cloud, ver README § Demo ao vivo). Cópia própria de `app.py` + subconjunto de `src/` + snapshot congelado de `data/processed`/`models` (única exceção deliberada à política de "dado não versionado" — dado público, sem PII, ~10MB). Sincronizado manualmente com a raiz a cada mudança de UI, não é gerado automaticamente. Tem seu próprio `.gitattributes` (git-lfs, usado só pelo push pro Hugging Face) — **nunca rodar `git add .`/`git add -A` na raiz do projeto**: como o `.gitattributes` mais próximo do arquivo sempre vence na resolução de atributos do git, isso converteria `deploy/hf_space/models/*.joblib` em ponteiro LFS de ~130 bytes dentro do histórico do GitHub, corrompendo o binário real. Sempre adicionar arquivo por nome explícito. **Sintoma pra reconhecer o risco ao vivo** (observado em 2026-08-25): `git status` mostra os 3 `.joblib` como modificados mesmo sem terem sido tocados — `git diff --stat` confirma com `Bin 2943785 -> 132 bytes` (o filtro LFS local "limpa" o binário pra ponteiro na hora de calcular o diff). O arquivo no disco continua íntegro (checar tamanho real com `ls -la`, deve bater com o blob do HEAD via `git cat-file -s`) — o alarme é o filtro, não o dado. **Nunca commitar esse diff** — faria exatamente a corrupção que o parágrafo acima descreve.

---

## Stack e dependências

- **Backend**: FastAPI (`src/api.py`) — CORS restrito, middleware de API key
- **Frontend**: Streamlit (`app.py`) — dark mode, responsivo
- **ML**: Isolation Forest (scikit-learn) pra detecção de anomalia
- **LLM**: Gemini 2.5 Flash — Camada 3 (LLM-as-Judge), opcional, implementada em `agente_rag.py` + `executar_camada3_llm()`, validada com chamada real em 2026-08-11 (o RAG trouxe contexto da ata do Copom no output, não é só fallback)
- **Container**: Docker + Docker Compose (usuário non-root)

---

## Linguagem ubíqua (termos do domínio)

| Termo | Significado neste projeto (não genérico) |
|---|---|
| **IRF** | Índice de Risco Fiscal (0-100). v1 (3 sinais, legado) e v2 (6 sinais, produção) coexistem — `irf_contexto` sempre usa v2. Não é métrica de risco de crédito nem de mercado, resume "quão hostil está o cenário macro brasileiro hoje", injetado como feature de ML |
| **Smurfing** | Fracionamento de transação pra fugir de limite regulatório |
| **Poupador Assustado** | Comprador legítimo de USDT como hedge contra a desvalorização do Real. É quem o projeto existe pra não incomodar — e é o perfil que mais sofre o trade-off medido (falso positivo aumenta 2,3x-3,5x com o IRF, faixa não número fixo, ver `TESE.md`) |
| **Fracionador** | Perfil suspeito: estrutura múltiplas transações abaixo de R$ 10k pra evitar reporte. É quem o projeto existe pra pegar |
| **Compliance** | Não é "seguir regra" — é decidir, por transação, se precisa de atenção humana, em 3 camadas de custo crescente |
| **Risco** | Probabilidade de evasão de divisas ou lavagem, nunca "risco de mercado" ou "risco de crédito" |
| **Score contextual** | Score de anomalia que muda de significado dependendo do cenário macro do dia (via IRF), não um score fixo por padrão de transação isolado |
| **Camada 1** | Filtros determinísticos das Resoluções BCB 519-521/2026 (R1-R5) |
| **Camada 2** | Isolation Forest com IRF como feature contextual |
| **Camada 3** | LLM-as-Judge com RAG temporal (atas do Copom) — validada com chamada real ao Gemini 2.5 Flash em 2026-08-11 (não é só fallback), ativa via `LLM_JUDGE_ENABLED=true` + `GEMINI_API_KEY` |
| **VERDE / AMARELO / VERMELHO** | Classificação final por `score_final` (buckets 0-40/40-70/70-100). Não confundir com `c2_classificacao` (normal/cinza/suspeito), que é saída intermediária só da Camada 2 |
| **wallets_unicas** | Contagem de wallets distintas por dia (regra R3). Não confundir com `entropia_wallets` (dispersão no histórico inteiro do usuário, escopo diferente) |
| **COAF** | Conselho de Controle de Atividades Financeiras |
| **RIF/RAS** | Relatório de Inteligência Financeira / Relatório de Atividade Suspeita |

---

## Regras de engenharia

- `FEATURES_ML` fica centralizado em `utils.py` — nunca duplicar.
- `IRF_LAG_DAYS=14` é obrigatório pra evitar vazamento de dado macro (IPCA/Selic/dívida-PIB são publicados com semanas de atraso; usar o IRF do dia exato da transação vazaria informação do futuro).
- `LLM_JUDGE_ENABLED=false` por padrão — ativa via `.env` com `GEMINI_API_KEY`.
- Docker roda non-root (`USER appuser`).
- Testes: `pytest tests/ -v` — 4 arquivos (`test_utils.py`, `test_pipeline_compliance.py`, `test_agente_rag.py`, `test_app_smoke.py`). 64 no total, mas 9 pulam via `skipif` quando faltam artefatos locais: `TestDatasetMestre` (5, integração) sem `data/raw/*.csv`, e `test_app_smoke.py` (4, uma por página do dashboard via `streamlit.testing.v1.AppTest`) sem `data/processed/`+`models/` — é o caso do CI, que roda 55.
- Log em `pipeline.log`, não versionado.
- Normalização do score do Isolation Forest é calibrada empiricamente (p1/p99) no treino e salva em `models/score_calibracao_v1.joblib` — nunca hardcodear range fixo (`carregar_calibracao_score()`/`normalizar_score_anomalia()` em `pipeline_compliance.py` são a fonte única, usada tanto no pipeline batch quanto na API).

---

## Restrições técnicas confirmadas (sabatina 2026-08-10/11)

- **A maior restrição hoje é dado sintético.** Nenhuma validação usa transação real — `gerador_transacoes_mock.py` gera com seed fixa, rótulo conhecido por construção. As métricas de precisão/recall no `TESE.md` são contra esse rótulo sintético, não contra produção.
- **Não tem banco de dados** — CSV + joblib em memória no startup da API (ADR-0006, decisão consciente, não bug).
- **Não persiste histórico por usuário** — a API não verifica a regra R2 (volume 30 dias) por transação isolada, só o pipeline batch consegue.

## Escopo negativo (o que decidimos conscientemente não fazer)

- **Não virar produto ainda.** O projeto é prova de competência metodológica, não aposta de receita (ver `TESE.md`, eixo 4).
- **Não tunar o modelo pra reduzir o trade-off de falso positivo** sem dado real (ticket 0001 do Wayfinder).

## Métrica de sucesso e cenário de falha (falsificabilidade)

Herdado do `TESE.md`: a tese (e o projeto) falha se, medido contra o rótulo de verdade do dataset sintético, o IRF não melhorar a precisão em relação a rodar sem ele. Testado em 2 rodadas de correção (`IRF_LAG_DAYS=14` + calibração empírica do IRF v2, 2026-08-11): precisão 35,9% → 44,8%, recall 34,4% → 49,9%. O critério de morte nunca disparou nas 3 versões testadas — o veredito "VAI" é robusto. O trade-off de falso positivo oscilou entre 2,3x e 3,5x conforme os bugs foram corrigidos, então é reportado como faixa (2-3,5x), não número de 1 casa decimal (ver `TESE.md`, adendo 2).

---

## ADRs registrados

| ADR | Decisão |
|---|---|
| 0001 | Isolation Forest vs. LOF vs. One-Class SVM |
| 0002 | Gemini 2.5 Flash como LLM-as-Judge |
| 0003 | IRF v2 com 6 sinais ortogonais |
| 0004 | FastAPI + Streamlit como stack de deploy |
| 0006 | Persistência em CSV/joblib em memória (não migrar pra banco agora) |

---

## Débitos técnicos conhecidos

1. Dado em memória (DataFrame) — não escala pra milhões de transação. Aceito conscientemente via ADR-0006.
2. Sem banco de dados — dado volátil entre restart. Mesmo débito do item 1, ADR-0006.
3. `starlette` preso em 1.3.1, com várias vulnerabilidades altas/médias apontadas pelo Dependabot. Não dá pra atualizar pra 1.6.0 porque `streamlit<1.4.0,>=0.46.0` exige essa faixa. Só resolve atualizando o Streamlit pra uma versão que aceite `starlette` mais novo, ou trocando o dashboard de framework — nenhuma das duas é trivial. Registrado, não corrigido.
4. Resíduo de vulnerabilidade no stack Jupyter (`jupyterlab`, `notebook`, `tornado`, `mistune`, usados só pelos 3 notebooks CRISP-DM, não em produção) — sem fix publicado ainda na maioria dos casos (`pip list --outdated` não aponta versão nova disponível). Superfície de risco baixa porque não roda em produção/API, mas fica registrado.

Nenhum outro débito técnico aberto no momento — os 4 que restavam (CI/CD, timestamp malformado, `preparar_prompt_llm` arquitetural, thresholds do IRF v2) foram corrigidos em 2026-08-11 (ver abaixo).

### Auditoria de dependência — 2026-08-11

O GitHub Dependabot acusou 136 vulnerabilidades (2 críticas, 66 altas) logo depois do primeiro push. Investigando, achei que o `requirements-lock.txt` tinha sido gerado com `pip freeze` direto no Python desta máquina, que captura o ambiente inteiro — inclusive ferramenta de outros projetos meus (`torch`, `pyspark`, `langchain`, `chromadb`, `GitPython`, nada disso usado aqui). Regenerei a partir de um venv limpo, instalando só `requirements.txt`: 163 pacotes, não ~300 — eliminou as 2 críticas e a maioria das altas (nenhuma delas era dependência real do projeto). 60/60 testes confirmados nesse ambiente limpo. Achado colateral: `scikit-learn` sobe pra 1.9.0 no lock novo, mas o modelo treinado (`isolation_forest_v1.joblib`) foi salvo com 1.8.0 — funciona (aviso de compatibilidade, não erro), mas é fragilidade de reprodutibilidade real, ainda não corrigida (exigiria fixar a versão ou retreinar).

### Corrigido em 2026-08-11 (Blind Spot Pass + reconciliação com histórico real)

- **Timestamp malformado sem validação defensiva.** `camada1_filtros_bcb()` e `engenharia_features()` usavam `pd.to_datetime()` com `errors="raise"` (default) — uma transação com timestamp ilegível derrubava o lote inteiro. Corrigido com `errors="coerce"` + regra nova R6 (timestamp malformado ou ausente é tratado como suspeito em si, não passa silenciosamente pelas regras que dependem de tempo). Também corrigido antes: coluna `hora` dessincronizada do timestamp real em transações fracionadas (`gerador_transacoes_mock.py`).
- **`preparar_prompt_llm` duplicado no pipeline.** Movido pra `agente_rag.py`, junto com o resto da lógica de LLM/RAG. Import tardio em `pipeline_compliance.py`, mesmo padrão de fallback gracioso que `executar_camada3_llm()` já usava.
- **Sem CI/CD robusto.** Adicionado job de lint (`ruff`, config enxuta em `ruff.toml`) ao `.github/workflows/ci.yml`. Também corrigido um bug de path que fazia o CI apontar pra um diretório que não existe dentro do próprio repo.
- **Thresholds de normalização do IRF v2** (`calcular_irf_v2` em `utils.py`) eram constante hardcoded, calibrada uma vez sobre 2022-2025 — mesma categoria de fragilidade do bug de calibração do Isolation Forest. Corrigido: `calcular_calibracao_irf_v2()` calcula p95 empiricamente sobre o dado real, `recalcular_irf.py` salva como artefato (`data/processed/irf_v2_calibracao.json`). Achado real: o threshold de IPCA estava em 4.5, o valor calibrado é 11,4 (2,5x maior) — o sinal de IPCA saturava fácil demais. Retrocompatível: `calcular_irf_v2()` aceita `thresholds=None` e cai no fallback (`THRESHOLDS_IRF_V2_DEFAULT`, mesmos valores hardcoded originais).
- Regra R2 (`camada1_filtros_bcb`) usava janela de 30 transações, não 30 dias calendário — corrigido com `.rolling("30D")`.
- `api.py`: schema `TransacaoInput` não declarava `hora` nem `wallets_unicas`, mas o endpoint `/compliance/score` os usava — causava `AttributeError` garantido. Corrigido.
- `api.py`: normalização de score e prompt do LLM-as-judge duplicados e divergentes do `pipeline_compliance.py` — consolidados numa fonte única.
- `api.py`: texto de razão do C1 (XAI) só checava 2 das 5 regras reais — agora cobre R1/R3/R4/R5; R2 documentado como não-verificável sem histórico do usuário.
- Bug de calibração do score do Isolation Forest (range hardcoded `-0.5/0.5` não batia com a distribuição real) — corrigido com calibração empírica (p1/p99), salva como artefato.

### Corrigido em 2026-08-27 (3 das 5 lacunas de deploy do README)

- **Auth fail-open em `src/api.py`.** Antes: sem `API_KEY_INTERNA`, só logava warning e deixava os endpoints protegidos abertos. Agora recusa subir (`RuntimeError` no import) — só abre sem chave se `API_AUTH_OPCIONAL=true` for setado explicitamente (dev local isolado). Confirmado com teste manual (import sem a env var levanta o erro).
- **CORS hardcoded pra `localhost:8501`.** Agora lê `CORS_ORIGINS` (lista separada por vírgula), com o mesmo default de antes se a variável não for setada — não quebra o fluxo local existente.
- **`docker-compose up --build` não funcionava sozinho na primeira vez.** `entrypoint.sh` novo detecta `data/`/`models/` vazios e roda o pipeline de setup automaticamente antes de subir o serviço (serializado via `depends_on: backend: condition: service_healthy` — só o backend roda o setup, o dashboard já encontra os dados prontos). `docker-compose run setup` continua existindo, agora só pra forçar regeneração manual.
- Item 4 (CI não builda a imagem Docker) também corrigido — job `docker-build` novo em `.github/workflows/ci.yml`.
- Os 2 itens que restam (sem banco/dado em memória, `starlette` preso) já eram decisão de escopo documentada (ADR-0006) ou gate estrutural registrado na base — não é trabalho pendente, é fronteira assumida.
- 60/60 testes confirmados depois da mudança de deploy (nenhum teste importa `api.py` diretamente, então o fail-closed não quebrou CI). Contagem subiu pra 64 depois, com `test_app_smoke.py` (ver seção de UI abaixo).

### Redesign da UI do dashboard — 2026-08-27

Motivação: a paleta anterior (neon cyan/violeta, texto em gradiente, cards com glow no hover) lia como demo de hackathon de IA, não como ferramenta de compliance — problema real quando o público-alvo passa a incluir empresa séria do setor (KYC/AML), não só recrutador de portfólio.

- **Paleta trocada pela paleta de status validada da skill `dataviz`** (`references/palette.md`): verde/amarelo/vermelho agora vêm de `good`/`warning`/`critical` (hex `#0ca30c`/`#fab219`/`#d03b3b`), validados por `scripts/validate_palette.js` contra contraste e separação de daltonismo — não escolhidos no olho. Fundo, cards e tipografia seguem os tokens de "Chart chrome & ink" do mesmo arquivo.
- **Gráficos matplotlib estáticos (`st.pyplot`) trocados por Plotly interativo** (`st.plotly_chart`, hover com tooltip) — os 3 gráficos do dashboard (IRF histórico, decomposição de 4 sinais, respectivo fallback). A decomposição usa cores categóricas de identidade (azul/laranja/aqua/violeta), nunca as cores de status — regra da skill `dataviz`: status é reservado, nunca reusado como "série 4".
- **Removidos**: emoji decorativo em cabeçalho/título de seção (ficou só onde é sinal funcional, ex. dentro do badge de alerta), gradiente de texto no `<h1>`, hover-glow nos KPI cards, border-radius grande (16px→6px).
- Nova dependência: `plotly` (`requirements.txt` + `requirements-lock.txt==6.7.0`).
- Novo teste: `tests/test_app_smoke.py` — roda as 4 páginas do dashboard via `streamlit.testing.v1.AppTest` (sem browser) e falha se qualquer uma levantar exceção. Pula sem `data/processed/`+`models/` locais, mesmo padrão do `TestDatasetMestre`.
- **Screenshots do README/reports/ ficaram desatualizados** (mostram a paleta antiga) — pendente recapturar, ver débito registrado no Context Bridge.

### O job docker-build (recém-criado) pegou um bug real no primeiro push — 2026-08-27

`software-properties-common` no `Dockerfile` quebrava o build: o pacote não existe mais no repositório "trixie" que `python:3.13-slim` passou a resolver, e não era usado por nenhum script do projeto (sem `add-apt-repository` em lugar nenhum) — dead weight herdado de algum template, nunca detectado porque o CI nunca tinha buildado a imagem antes. Removido. Confirma o valor do gate: existia desde antes desta sessão, só ficou visível quando o job de build passou a existir.

Revisão adicional da página do repositório no GitHub (a pedido do Luiz, "veja se está tudo certo"): description/topics/homepage estavam vazios (sem subtítulo, sem tag de descoberta, sem link pro demo em destaque) — preenchidos. Badge de status do CI adicionado ao README (não existia).

---

## Artefatos de raciocínio (não é código, mas é parte do produto)

- `docs/tese/shadow-fx-vantagem-competitiva/TESE.md` — sabatina de valor: o projeto ganha vantagem competitiva real frente a Chainalysis/TRM/Elliptic? Veredito: VAI, com 3 condições.
- `docs/wayfinder/tese-veredito-condicoes/` — decomposição das 3 condições em tickets, todos resolvidos, `SPEC_FINAL.md` compilado.
- Este arquivo (`AGENTS.md`) — mesclado via `/grill-with-docs` em cima do original.

## Referências externas citadas nas decisões

- Resoluções BCB 519, 520, 521/2025 (vigor fev/2026) — cria a obrigação legal de AML pra VASP.
- Capital mínimo pra VASP: R$ 10,8 milhões (fonte: NDM Advogados).
- Preço de mercado dos incumbentes: Chainalysis US$ 50-200K/ano, TRM Labs €60-150K/ano, Elliptic €80-180K/ano (fonte: Costbench, Finconduit).
- Dinamismo regulatório (2026-08-11): cerca de 7 mudanças regulatórias relevantes em 18 meses (Lei 14.478/2022 → 4 consultas públicas 2023-2024 → Resoluções 519/520/521 → Resolução 561 → IN 701/2026 → IOF sobre stablecoin). Fonte: Agência Brasil, Mattos Filho, Forbes. Nenhuma evidência pública de Chainalysis/TRM/Elliptic priorizando o Brasil especificamente. R$ 388 bi declarados em cripto por brasileiro em 9 meses de 2025, mais de 70% em stablecoin — fonte: Blue Consult. Detalhe completo em `docs/wayfinder/tese-veredito-condicoes/0003-perfil-exchanges-br-nicho.md` (adendo).
