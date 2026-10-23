# Spec: Fase 3 — offsets, gerador v2, placebo e medição do IRF

**Data:** 2026-10-23 · **Implementa:** Codex · **Audita o diff:** Claude · **Aprova o push:** Luiz
**Decisão:** `docs/adr/0011-gerador-v2-placebo.md` (leia antes). **Origem:** `docs/revisao/2026-10-REVISAO.md` §4.

## 1. Objetivo

Construir um experimento em que o IRF **possa falhar**:
- um mundo sintético em que o poupador reage ao macro e o fracionador não;
- um placebo idêntico, mas sem esse acoplamento;
- uma medição por usuário, com IC, das condições A, B e C do ADR-0011.

O Codex entrega código e testes com dado pequeno. **Não roda a medição em tamanho real.** O Luiz registra a predição dele antes, e o Claude roda depois.

## 2. Decisões já tomadas (não reabrir)

- Pipeline em lote D+1 (`AGENTS.md`). `IRF_LAG_DAYS = 14` continua.
- β=0,7 e γ=0,3 ficam fixos. Teto de dano `x_max=0,05` (ADR-0008). Split por usuário com seed 42 (`decisao.split_por_usuario`).
- O v1 (`gerador_transacoes_mock.py`) e os números travados em `tests/test_medir_escada.py` **não mudam**.

## 3. Contrato

### 3.1 Offsets e meta (`src/macro_disponibilidade.py`, `src/coletar_dados.py`, `src/recalcular_irf.py`)

1. `OFFSET_DISPONIBILIDADE_DIAS`: `ibc_br` passa a 90 e `divida_bruta_pib` passa a 70. Atualize o comentário para citar a conferência de 23/10 (ADR-0011).
2. Renomeie `expectativa_ipca_12m` para `meta_inflacao` (SGS 13521) em `coletar_dados.py` e em `macro_disponibilidade.py`, com offset 0.
   - **Atenção:** offset 0 só é correto porque a meta é anual e conhecida de antemão. Escreva isso no comentário.
   - **Compatibilidade:** se o `data/raw/macro_bcb.csv` local ainda tiver a coluna antiga, aceite-a renomeando na leitura. Não falhe por causa disso.
3. `derivar_mensais`: `desvio_meta_ipca = ipca_acum_12m − meta_inflacao` quando a coluna existir. Sem ela, mantenha 3,0 e emita `logger.warning` (falha visível, não silenciosa).
4. **SGS 4537:** consulte os metadados no SGS (`https://api.bcb.gov.br/dados/serie/bcdata.sgs.4537/dados/ultimos/1?formato=json` ou a página da série) e **reporte** o nome oficial. **Não troque o código da série.** A troca depende de decisão do Luiz.

### 3.2 Gerador v2 (`src/gerador_v2.py`, novo)

```python
def gerar_dataset_v2(irf_diario: pd.Series, acoplamento: bool, seed: int = 2026,
                     n_poupadores: int = 1000, n_frac_classico: int = 100,
                     n_frac_fora_regra: int = 100, n_institucionais: int = 50,
                     beta: float = 0.7, gama: float = 0.3) -> pd.DataFrame
```

**Entrada e contrato:**
- `irf_diario`: série diária do `irf_v2` **já com o atraso de publicação** (saída de `recalcular_irf.py`), indexada por data.
  - Período de 2024-01-01 a 2025-06-30.
  - `z(t)` = padronização (média e desvio) **sobre o período**.
  - Se houver dia sem IRF dentro do período, levante `ValueError`. Não preencha.
- Use `rng = np.random.default_rng(seed)` local, nunca `np.random.seed` global.
- Mesmas colunas do v1, mais `classe_v2` (`poupador`, `frac_classico`, `frac_fora_regra`, `institucional`) e `z_irf_dia` (só para diagnóstico; **não pode entrar em `FEATURES_ML`**).
- `tipo_usuario`: mantenha os rótulos do v1. Os dois tipos de fracionador usam `C_suspeito_fracionamento`, para que `rotulos()` funcione sem mudança.

**Comportamento de cada classe:**
- **Poupador:**
  - Número de compras no dia t ~ Poisson(`λ₀ · exp(β·z(t))`) se `acoplamento`, senão Poisson(`λ₀'`).
  - `λ₀` é calibrado para ~12 compras por usuário no período (como o v1).
  - **`λ₀'` é escolhido para que o total esperado seja igual ao do mundo acoplado.**
  - Ticket: `uniform(800, 3500)` por usuário × `(1 + γ·max(z(t),0))` se `acoplamento`. No placebo, o multiplicador é a **média ponderada pelo número esperado de compras**, `Σ λ(t)·m(t) / Σ λ(t)`, para que o valor movimentado esperado seja igual ao do v2 (esclarecimento §8.1).
  - Horário e wallet como no v1.
- **Fracionador clássico:** como o v1 (valores 8.500-9.900, madrugada, 15-40 wallets, rajadas). Datas uniformes, **sem acoplamento nos dois mundos**.
- **Fracionador fora da regra:** valor `uniform(4000, 7900)`, hora 9-18, 2-4 wallets distintas por dia, rajadas de 3-6 transações num mesmo dia, ~8-15 dias de rajada no período. Sem acoplamento.
  - Ele precisa escapar de R3, R4 e R5 **na maioria das transações**. O teste do §5 mede isso.
- **Institucional:** como o v1.

### 3.3 Medição (`src/medir_irf.py`, novo)

Função principal:

```python
medir_mundo(df_tx, df_irf, seed=42, x_max=0.05, B=2000) -> dict
```

Passos:
1. `engenharia_features` do pipeline, sem cópia.
2. `split_por_usuario(seed=42)`.
3. Dois `IsolationForest(n_estimators=200, contamination=0.07, random_state=42)` treinados **só na calibração**:
   - um com `FEATURES_ML`;
   - outro com `FEATURES_ML` sem `irf_contexto`.

   O scaler é ajustado na calibração. O score é normalizado com p1/p99 da calibração (mesma lógica de `normalizar_score_anomalia`).
4. Limiar de cada modelo: `escolher_limiar_operacao(..., x_max=x_max, usuarios=calibracao)`.
5. Na avaliação, por usuário:
   - recall de fracionador;
   - fração de poupadores tocados;
   - **FP de estresse** = poupadores com ≥1 alerta num dia de `irf_contexto` no quartil superior, sobre os poupadores com ≥1 transação nesses dias. O quartil é calculado na calibração.
6. Bootstrap pareado: reamostra usuários de avaliação **dentro de cada classe**, B vezes, e usa a mesma reamostra para os dois modelos. Devolve o ponto e o IC 95% percentil das diferenças (com − sem) de recall, FP geral e FP de estresse. Devolva também o recall separado por `classe_v2`.

Saída e CLI:
- CLI `python src/medir_irf.py --mundo v2|placebo`.
- Imprime a tabela e grava `reports/irf_fase3_<mundo>.json`.
- `avaliar_condicoes(res_v2, res_placebo) -> dict` devolve A, B e C como booleanos, com o número que decidiu cada uma.

Se `escolher_limiar_operacao` devolver `None`, **pare com erro explícito**. Não use limiar padrão.

## 4. Escopo

**Incluídos:**
- `src/macro_disponibilidade.py`, `src/coletar_dados.py` e `src/recalcular_irf.py` (§3.1);
- `src/gerador_v2.py` e `src/medir_irf.py` (novos);
- `tests/test_gerador_v2.py` e `tests/test_medir_irf.py` (novos);
- ajuste mínimo em `tests/test_vazamento_temporal.py`, só se o renome do §3.1 quebrar o teste. Nesse caso, mantenha a mesma asserção.

**Fora de escopo:**
- `gerador_transacoes_mock.py`, `pipeline_compliance.py` (não alterar `FEATURES_ML`), `decisao.py`, `treinar_modelo.py`, `api.py`, `app.py`;
- `deploy/hf_space/**` (inclusive os `.joblib`), `data/`, `models/`, `docs/spec/`, `dev/`, README e PROBLEM.

`reports/irf_fase3_*.json` **não** é gerado nem commitado nesta entrega.

## 5. Critério de aceitação

Todos com dado de brinquedo e sem rede (IRF sintético com uma onda senoidal e n pequeno: 60 poupadores, 20+20 fracionadores, 5 institucionais).

1. **Offsets:** `OFFSET_DISPONIBILIDADE_DIAS["ibc_br"] == 90`, `["divida_bruta_pib"] == 70`, `meta_inflacao` com offset 0. `desvio_meta_ipca` usa a meta do mês: com meta 3,5 em 2022 e ipca_acum 5,0, o desvio é 1,5. Sem a coluna, o desvio é 3,0 e há warning.
2. **Determinismo:** a mesma seed gera um DataFrame idêntico, e seeds diferentes geram DataFrames diferentes. O gerador não toca no estado global do numpy (`np.random.get_state()` igual antes e depois).
3. **Acoplamento existe:** no v2, a correlação de Spearman entre `z_irf_dia` e as compras diárias do poupador é > 0,3. No placebo, |ρ| < 0,1. Para o fracionador, |ρ| < 0,1 nos dois. Use n maior se precisar estabilizar, sem passar de ~5 s.
4. **Placebo com volume igual:** o total de transações do poupador no placebo fica a ±5% do v2, e o valor total a ±5%.
5. **Fora da regra:** ≥80% das transações de `frac_fora_regra` não acionam R3, R4 nem R5 (use `camada1_filtros_bcb` real). Para `frac_classico`, ≥80% acionam pelo menos uma.
6. **Sem vazamento do rótulo em feature:** `z_irf_dia` e `classe_v2` não estão em `FEATURES_ML`, e o `medir_irf` não as usa como feature.
7. **IRF ausente:** um dia faltando no período levanta `ValueError`.
8. **Medição:**
   - o split não mistura usuários;
   - o modelo "sem IRF" não recebe a coluna;
   - o bootstrap é pareado (a mesma reamostra para os dois modelos: teste com semente fixa e contagem de usuários);
   - `limiar None` levanta erro;
   - `avaliar_condicoes` devolve A/B/C corretos para três resultados fabricados à mão (passa, falha B, falha C).
9. `pytest tests/ -q` verde, **com `tests/test_medir_escada.py` sem alteração**. `ruff check src/ tests/ app.py tools/` limpo.

## 6. Riscos

- **Mecanismo do IF:** pode ser que o Isolation Forest não use bem o `irf_contexto` mesmo no v2. Esse é um resultado legítimo, não um bug. Não ajuste β, γ, a contamination nem as features para "fazer passar". Se algo parecer exigir isso, pare e reporte.
- **Gerador de quem tem a tese:** a ressalva do ADR-0011 vai para o README só depois do resultado. Não mexa no README agora.
- **IRF regenerado:** rodar `recalcular_irf.py` após o §3.1 muda `data/processed/` local. Não commite `data/`. Informe quantos dias passaram a ser NaN no início por causa dos offsets novos.

## 7. Entrega

Commits pequenos, sem push, sem trailer `Co-Authored-By`, sem menção a IA, nada de `git add .` e nunca os `.joblib` de `deploy/hf_space/models/`. Sugestão de commits:
1. `fix(macro): offsets de IBC-Br e dívida conferidos; meta de inflação por ano`
2. `feat(gerador): mundo v2 com acoplamento macro e placebo`
3. `feat(medicao): ablação do IRF por usuário com bootstrap pareado`

Responder com:
- os hashes;
- o nome oficial da série SGS 4537;
- o número de dias com NaN no início;
- a confirmação de que `test_medir_escada.py` não mudou e passa;
- toda divergência entre o código real e esta spec, com a decisão tomada. O ideal é parar e perguntar antes de decidir.

## 8. Esclarecimentos (2026-10-23, depois que o Codex parou)

### 8.1 Multiplicador do ticket no placebo

A versão anterior desta spec pedia a média simples de `m(t) = 1 + γ·max(z(t),0)` entre os dias. Isso é um erro da spec: no mundo acoplado, quantidade e ticket sobem juntos, então o valor esperado é `Σ λ(t)·m(t)`, e não `Σ λ(t) · média(m)`. Na onda de teste, a média simples dá 1,135 e a ponderada dá 1,238, o que deixa o placebo 8,4% abaixo do v2.

**Regra:** use a média ponderada pelo número esperado de compras. O critério de ±5% do §5.4 **continua valendo**. O objetivo do placebo é ter o mesmo volume e o mesmo valor, de modo que a única diferença entre os mundos seja a correlação com o macro.

### 8.2 Ambiente de teste

O erro na criação do diretório temporário é do ambiente, não do código. Rode `pytest tests/ -q --basetemp=.pytest_tmp`. O `.pytest_tmp/` não vai para commit. A entrega só conta como validada com a suíte inteira verde.

### 8.3 Série da dívida (decisão do Luiz, 2026-10-23)

O Codex confirmou que a SGS 4537 é a "Dívida bruta do governo geral (% PIB) — Metodologia utilizada até 2007". O mercado acompanha a DBGG da metodologia vigente, que fechou 2025 em 78,7% (Estatísticas Fiscais do BCB, 30/01/2026). **Decisão: trocar pela série vigente.**

- Localize no SGS o código da DBGG em % do PIB pela metodologia vigente. O candidato é 13762, **mas confirme pelo nome oficial**: a API recusou a consulta do Claude.
- Confira um ponto: dez/2025 ≈ 78,7.
- Troque o código em `coletar_dados.py`. O nome da coluna (`divida_bruta_pib`) e o offset de 70 dias continuam iguais.
- Registre o motivo da troca em uma linha do `AGENTS.md`, na seção de fontes macro.
- **Não rode a coleta com rede no teste.** Se tiver rede, rode `coletar_dados.py` e `recalcular_irf.py` uma vez, sem commitar `data/`, e informe o primeiro e o último valor da série nova.
- Se não achar uma série vigente com o nome confirmado, **pare e reporte**. Não troque por palpite.

### 8.4 Calendário do IRF × calendário diário do gerador (2026-10-23)

Conferido no mestre local (`carregar_dataset_mestre`): desde 2024 ele tem **só dias úteis**, com 387 dias de 2024-01-01 a **2025-06-27**. Os buracos são fins de semana (3 dias) e um feriado longo (5 dias). O IRF herda esse calendário. Não é um dado faltando: é o mercado fechado.

**Regra:**
1. **A saída de `recalcular_irf.py` não muda.** A expansão acontece dentro do gerador, numa função própria (`irf_calendario_diario(irf, inicio, fim, max_gap_dias=4)`), coberta por teste.
2. **Dia sem observação recebe o último IRF observado (`ffill`).** É o que estava disponível naquele dia, a mesma semântica do `asof` do pipeline. Nunca use `bfill` nem interpolação.
3. **Limite:** no máximo 4 dias corridos seguidos preenchidos, o que cobre o feriado longo. Um buraco maior levanta `ValueError`, que é a falha visível de dado faltando de verdade.
4. **Período efetivo:**
   - início = max(2024-01-01, primeira data com IRF não nulo);
   - fim = **min(2025-06-30, última data com IRF)**.

   Nada é estendido além da última observação. No dado local, o fim é 27/06/2025. Registre o período efetivo na saída do gerador e no JSON da medição.
5. **Testes novos:**
   - um IRF só de dias úteis vira diário, com sábado e domingo iguais à sexta;
   - 4 dias seguidos sem observação (datas observadas a 5 dias de distância, como o feriado real) passam; 5 ou mais dias seguidos sem observação (distância ≥ 6) levantam erro;
   - o fim nunca passa da última observação;
   - nenhum valor anterior à primeira observação é preenchido.
