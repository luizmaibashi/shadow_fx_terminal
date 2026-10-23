# Spec — Fase 2: cascata real + regra de decisão

**Data:** 2026-10-23 · **Implementa:** Codex · **Audita o diff:** Claude · **Aprova o merge:** Luiz
**Decisões de origem:** `docs/adr/0008-criterio-decisao-teto-de-dano.md`, `docs/adr/0009-cascata-real.md`. Em caso de dúvida, leia os dois ADRs. Esta spec não repete o porquê.

## 1. Objetivo

Fazer o pipeline executar a cascata que o ADR-0009 descreve e escolher o ponto de operação da Camada 2 pela regra do ADR-0008. Ao final, `src/medir_escada.py` deve mostrar na mesma tabela da revisão (§2.2) o degrau "cascata (ADR-0009)", com `n` e IC, e a fração de casos que iria ao LLM.

## 2. Escopo

**Incluído (só estes arquivos):**

| Arquivo | Mudança |
|---|---|
| `src/pipeline_compliance.py` | colunas `c1_reporte`/`c1_suspeita`; `decisao_cascata`; `executar_pipeline` usa a cascata |
| `src/decisao.py` (novo) | `escolher_limiar_operacao`, `split_por_usuario`, `limiar_por_custo` |
| `src/medir_escada.py` | degrau novo + bloco de limiar (ADR-0008) |
| `tests/test_decisao.py` (novo) | testes de `decisao.py` e `decisao_cascata` |
| `tests/test_pipeline_compliance.py` | ajustar só os testes que dependem da semântica antiga (ver §4) |
| `tests/test_medir_escada.py` | travar os números novos |

**Fora de escopo (não tocar):**
- `deploy/hf_space/**` (inclusive os 3 `.joblib` e a cópia de `src/`), `app.py`, `src/api.py`, `scripts/site/`, `docs/index.html`. A cor muda de significado só no pipeline. O alinhamento de UI, API e snapshot é uma fase separada.
- `docs/spec/` e `dev/` (são de outra sessão).
- O gerador (`gerar_transacoes_mock.py`) e o IRF: são a Fase 3.
- Fazer `c3_veredito` decidir: é a Fase 4 e o ADR-0010.
- **Nunca** usar `git add .` / `git add -A`. Adicionar arquivos por nome.

## 3. Contrato

### 3.1 Camada 1 (`camada1_filtros_bcb`)

- Novas colunas booleanas: `c1_reporte` = R1 ∨ R2, e `c1_suspeita` = R3 ∨ R4 ∨ R5 ∨ R6.
- `c1_flag` e `c1_razoes` ficam **idênticos** ao comportamento atual, valendo `c1_flag == c1_reporte | c1_suspeita`.

### 3.2 `src/decisao.py`

```python
def split_por_usuario(df, frac_calibracao=0.5, seed=42) -> tuple[pd.Index, pd.Index]:
    """Usuarios de calibracao e de avaliacao, estratificado por tipo_usuario.
    Todo tipo com >=2 usuarios aparece nos dois lados."""

def escolher_limiar_operacao(df, score_col="c2_score_anomalia", x_max=0.05,
                             k_max=None, usuarios=None) -> float | None:
    """ADR-0008. Positivo = df[score_col] >= limiar.
    Restricoes: fracao de poupadores (tipo_usuario comeca com 'A_') com >=1 positivo <= x_max;
    se k_max nao for None, positivos por 100 transacoes <= k_max.
    Objetivo: maximo recall POR USUARIO de fracionador (fraude = tipo_usuario contem 'suspeito').
    Empate: o MAIOR limiar (menos alertas). Sem limiar viavel: None.
    `usuarios` restringe o calculo a esse subconjunto (lado de calibracao)."""

def limiar_por_custo(df, score_col, razao_fn_fp: float, usuarios=None) -> float:
    """Sensibilidade: limiar que minimiza razao_fn_fp*FN + FP, contado por usuario."""
```

- Os candidatos a limiar são os valores únicos de `score_col` mais `+inf` (o "desligado", que nunca é positivo e equivale a recall 0, mas é sempre viável no X). **Atenção:** se o único limiar viável for o desligado, `escolher_limiar_operacao` devolve `None`.
- O rótulo de fraude e o tipo de poupador seguem as definições de `src/medir_escada.py` (`carregar`). Reaproveite, não duplique a regra.
- Entrada sem contrato: `x_max` fora de (0, 1], `k_max` ≤ 0, `score_col` ausente ou com NaN levantam `ValueError` com mensagem. Nada de clamp silencioso.

### 3.3 Cascata (`pipeline_compliance.py`)

```python
def decisao_cascata(df, limiar: float | None) -> pd.DataFrame:
    """ADR-0009. Adiciona c2_positivo, zona_cinza, alerta_final."""
```

- `c2_positivo = c2_score_anomalia >= limiar`. Se `limiar is None`, é `False` em tudo.
- `alerta_final`: `c1_suspeita & c2_positivo` → VERMELHO; nenhum dos dois → VERDE; XOR → AMARELO, com `zona_cinza=True`.
- `c1_reporte` **não** entra na cor.
- `executar_pipeline(df_tx, df_irf, limiar_operacao=...)`:
  - Ordem de resolução do limiar: argumento explícito → `models/limiar_operacao.json` (`{"limiar": float | null, "x_max":..., "k_max":..., "data":...}`) → legado 70.0, com `logger.warning` dizendo que o limiar do ADR-0008 não foi calibrado. Gravar a origem na coluna `c2_limiar_origem` (`"argumento"`, `"artefato"` ou `"legado_70"`).
  - **C3 roda só onde `zona_cinza`**, substituindo o `mask_cinza` de `c2_classificacao == "cinza"`. `c3_veredito` não altera `alerta_final`.
  - `score_final` mantém a fórmula atual (é prioridade de fila). Os buckets de `score_final` **não** definem mais `alerta_final`.
  - `c2_classificacao` continua existindo, sem mudança (saída intermediária).
- Não gravar `models/limiar_operacao.json` dentro do pipeline. Ele é escrito por `python -m medir_escada --salvar-limiar` (ou flag equivalente), a partir do lado de calibração.

### 3.4 `src/medir_escada.py`

O snapshot já tem `c1_razoes` e `c2_score_anomalia`. A cascata é recalculada sobre ele, **sem rodar o modelo de novo e sem reescrever o CSV**:

1. Derivar `c1_suspeita` de `c1_razoes` (R3, R4, R5 ou R6 presente).
2. `split_por_usuario(seed=42)` → `limiar = escolher_limiar_operacao(..., usuarios=calibracao)`.
3. Reportar no lado de **avaliação**, por transação e por usuário, com Wilson: precisão, recall, FP em legítimos, poupadores tocados, tamanho da zona cinza e "fracionadores que só a cascata pegou além da regra por 100 casos cinza".
4. Imprimir o limiar escolhido, os limiares de `limiar_por_custo` para 1:1, 10:1 e 50:1, e uma linha explícita quando `limiar is None` ("degrau C2 desligado pelo ADR-0008").
5. A tabela antiga continua igual: os números da Fase 1 não podem mudar.

## 4. Critério de aceitação

1. `pytest tests/ -v` verde, local. O CI precisa continuar verde depois do push.
2. `ruff check .` sem erro novo.
3. `tests/test_decisao.py` cobre, no mínimo:
   - As 4 linhas da tabela do ADR-0009, mais `limiar=None`.
   - R1 sozinho e R2 sozinho → `c1_reporte=True`, `c1_suspeita=False`, VERDE com `c2_positivo=False`.
   - `escolher_limiar_operacao` num dado de brinquedo com ótimo conhecido, num caso sem limiar viável (`None`), com empate (maior limiar vence) e com `k_max` ativo mudando a escolha.
   - `split_por_usuario`: os lados não se sobrepõem, cobrem todos os usuários, são estratificados e reproduzíveis com a mesma seed.
   - `ValueError` para cada entrada inválida do §3.2.
4. `tests/test_medir_escada.py` mantém as asserções da Fase 1 e acrescenta as da cascata: limiar escolhido e contagens (k, n) do lado de avaliação, como números exatos.
5. Em `tests/test_pipeline_compliance.py`, só mudam os testes que assumiam C3 = `c2_classificacao == "cinza"` ou a cor por bucket de `score_final`. Cada mudança é justificada no corpo do commit.
6. `python src/medir_escada.py` roda sobre o snapshot e imprime o bloco novo.

## 5. Restrições e riscos

- **Dado:** sintético, sem PII. O snapshot é só lido.
- **Vazamento:** o limiar nunca é escolhido sobre os usuários de avaliação. O teste deve verificar isso (por exemplo, mudar o rótulo de um usuário de avaliação não pode mudar o limiar).
- **Resultado esperado no v1** (não é bug): a zona cinza vai ser formada quase só por "regra sim, modelo não", e o ganho da cascata sobre a regra vai ser ≈ 0. Não ajuste nada para "melhorar" esse número.
- **Testes que pulam no CI** (`TestDatasetMestre`, `test_app_smoke`): não dá para conferir lá. Rodar local, se possível, e dizer qual rodou.

## 6. Entrega

- Commits pequenos (Conventional Commits, em português), por exemplo:
  1. `feat(c1): separa reporte obrigatório de suspeita`
  2. `feat(decisao): limiar por teto de dano (ADR-0008)`
  3. `feat(pipeline): cascata por discordância (ADR-0009)`
  4. `feat(medir): degrau da cascata com n e IC`
- **Sem** trailer `Co-Authored-By` e sem menção a IA na mensagem. **Não fazer push.** O Claude audita o diff antes.
- No fim, colar a saída do bloco novo de `medir_escada.py` e listar os testes alterados, com o motivo de cada um.
