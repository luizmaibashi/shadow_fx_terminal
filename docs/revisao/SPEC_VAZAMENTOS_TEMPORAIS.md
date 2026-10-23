# Spec: correção dos vazamentos temporais (achados 1, 2, 6 e 7)

**Data:** 2026-10-23 · **Implementa:** Codex · **Audita o diff:** Claude · **Aprova o merge:** Luiz
**Origem:** `docs/revisao/2026-10-ACHADOS_CODEX.md` (achados 1, 2, 6, 7). Pré-requisito da Fase 3: a ablação do IRF não vale nada com feature que enxerga o futuro.

## 1. Objetivo

Garantir que nenhuma feature de uma transação no dia D use informação publicada depois de D. A garantia é provada por **teste de perturbação**: mudar um dado do futuro não pode mudar nenhuma feature do passado.

## 2. Decisões do Luiz (2026-10-23)

1. **O pipeline é lote D+1.** Regras e features podem usar o dia inteiro da transação, mas nunca dias posteriores. Por isso a R3 (`wallets_unicas` do dia) e o `n_transacoes_dia` **continuam por dia**. Isso é desenho, não vazamento, e passa a ficar escrito. A entropia de wallets, que hoje usa o histórico inteiro do usuário, passa a usar só o histórico até o fim do dia da transação.
2. **Só código e testes.** Não regenerar `data/processed`, o IRF salvo, o modelo nem o snapshot de `deploy/hf_space/`. A Fase 3 regenera tudo com o gerador v2. Os números travados das Fases 1 e 2 (`tests/test_medir_escada.py`) **não podem mudar**.

## 3. Contrato

### 3.1 Novo módulo `src/macro_disponibilidade.py` (achados 1 e 7)

```python
# Dias entre a data de referência da observação mensal (dia 1 do mês, como vem do SGS)
# e o primeiro dia em que o número está público. ESTIMATIVA conservadora; conferir no
# calendário IBGE/BCB antes da Fase 3 (débito registrado).
OFFSET_DISPONIBILIDADE_DIAS = {
    "ipca_mensal": 45,            # IBGE divulga ~10 dias após o fim do mês de referência
    "ibc_br": 80,                 # BCB divulga ~2,5 meses depois
    "divida_bruta_pib": 65,       # estatísticas fiscais do BCB, ~fim do mês seguinte
    "expectativa_ipca_12m": 35,   # média mensal do Focus, fechada após o mês
}
SERIES_DIARIAS = {"selic_meta": 1}  # meta vale a partir do dia seguinte à reunião

def mensal_de_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """Recupera as observações mensais originais de um macro já interpolado
    (linhas do dia 1 de cada mês). Se o arquivo já for mensal, é identidade."""

def derivar_mensais(mensal: pd.DataFrame) -> pd.DataFrame:
    """Derivadas calculadas na frequência MENSAL, antes da expansão:
    ipca_acum_12m = soma de 12 meses; desvio_meta_ipca = ipca_acum_12m - 3.0;
    divida_pib_var = pct_change(1) mensal * 100; ibc_br_var = pct_change(1) mensal * 100.
    Cada derivada herda o offset da série de origem."""

def para_diaria_sem_lookahead(mensal: pd.DataFrame, indice_diario: pd.DatetimeIndex) -> pd.DataFrame:
    """Reposiciona cada observação em data_referencia + offset e faz ffill no índice diário.
    Antes da primeira disponibilidade: NaN (sem bfill, sem interpolação)."""
```

- **Gate de lista manual:** se aparecer uma coluna mensal sem entrada em `OFFSET_DISPONIBILIDADE_DIAS` ou em `SERIES_DIARIAS`, levantar `ValueError`. Nunca aprovar por omissão.
- `mensal_de_diaria` levanta `ValueError` se faltar o dia 1 de algum mês dentro do intervalo, ou seja, se o arquivo não estiver ancorado no início do mês. Nada de adivinhar.

### 3.2 Onde ligar

- `src/coletar_dados.py` (`coletar_macro_bcb`): **remover** o `resample("D").interpolate` e as derivadas calculadas sobre a série diária. Salvar o macro na frequência original.
- `src/utils.py` (carregamento do macro no dataset mestre): `mensal_de_diaria` → `derivar_mensais` → `para_diaria_sem_lookahead` antes do join. Deve funcionar com o `data/raw/macro_bcb.csv` atual (diário interpolado) e com o arquivo novo (mensal).
- `src/recalcular_irf.py`: **remover** `pct_change(1)` sobre `divida_bruta_pib` e `ibc_br` diários. Usar `divida_pib_var` e `ibc_br_var` que já vêm do mestre. Se faltarem, usar 0.0 com `logger.warning`, como no comportamento atual.

### 3.3 Copom (achado 6), em `src/recalcular_irf.py`

- O tom vem da ata, publicada cerca de 6 dias depois da reunião: `ATA_COPOM_OFFSET_DIAS = 6` (estimativa, a conferir junto com a tabela do §3.1).
- Reposicionar cada ata em `data + 6` e fazer `ffill`. **Remover o `bfill`.** Antes da primeira ata disponível, usar 0.5 (neutro, o mesmo valor que o fallback atual já usa) e registrar no log quantos dias receberam o neutro.

### 3.4 Entropia de wallets (achado 2), em `src/pipeline_compliance.py` (`engenharia_features`)

- `entropia_wallets` de uma transação no dia D = entropia da distribuição de wallets do usuário em todas as transações com `data <= D`. Inclui o dia D inteiro (lote D+1) e nada depois.
- R3 e `n_transacoes_dia` não mudam. A docstring de `camada1_filtros_bcb` e de `engenharia_features` passa a dizer "lote D+1: usa o dia inteiro, nunca dias posteriores".
- `FEATURES_ML` não muda (o nome da coluna é o mesmo).

### 3.5 Documentação mínima

- `AGENTS.md`, seção "Regras de engenharia": acrescentar 1 linha. "Pipeline é lote D+1: feature e regra usam no máximo o dia inteiro da transação. Macro mensal entra pela data de disponibilidade (`macro_disponibilidade.py`), não por interpolação."
- Não editar o README. O alinhamento de documentação pública é uma fase separada.

## 4. Escopo

**Incluídos:** `src/macro_disponibilidade.py` (novo), `src/coletar_dados.py`, `src/utils.py`, `src/recalcular_irf.py`, `src/pipeline_compliance.py`, `tests/test_vazamento_temporal.py` (novo), `AGENTS.md` (1 linha).

**Fora de escopo:** `deploy/hf_space/**` (inclusive os `.joblib` e a cópia de `src/`), `app.py`, `src/api.py` (o achado 3 é separado), `src/scraper_copom.py` (achado 4, separado), notebooks, `data/`, `models/`, `docs/spec/`, `dev/`. Não mudar `IRF_LAG_DAYS`; ele continua como margem extra. Atualize só o comentário em `utils.py`, dizendo que o atraso de publicação do macro agora é tratado pelos offsets.

## 5. Critério de aceitação

`tests/test_vazamento_temporal.py`, todos com dado de brinquedo e sem rede:

1. **Perturbação macro:** alterar a observação mensal de março não muda nenhum valor diário anterior a `01/03 + offset` em nenhuma coluna, inclusive nas derivadas. O teste vale para cada série do dicionário.
2. `ipca_acum_12m` é igual à soma dos 12 meses de referência anteriores (o bug atual somava 12 dias).
3. `divida_pib_var` em um mês é igual à variação percentual mensal × 100, e não à variação diária (achado 7).
4. Antes da primeira disponibilidade, o resultado é NaN e não o valor seguinte (sem `bfill`).
5. Uma coluna mensal sem offset levanta `ValueError`, e um arquivo diário sem o dia 1 de algum mês também.
6. `mensal_de_diaria` sobre um diário interpolado recupera exatamente os valores mensais originais.
7. **Copom:** uma ata em D só afeta dias ≥ D+6. Antes da primeira ata, o valor é 0.5. Alterar uma ata futura não muda o passado.
8. **Entropia:** acrescentar uma transação num dia posterior não muda a entropia de linhas anteriores. Acrescentar uma no mesmo dia muda, e isso é o D+1 documentado. O caso do achado 2 (6 transações das 09h às 14h) continua dando R3 e `n_transacoes_dia=6` em todas, por desenho.
9. `pytest tests/ -q` verde, **com `tests/test_medir_escada.py` sem nenhuma alteração**, e `ruff check src/ tests/ app.py tools/` limpo.
10. Se o `data/raw/macro_bcb.csv` local existir, rodar o carregamento do mestre e informar quantos dias passaram a ser NaN no início da série por causa dos offsets. Só informar, sem commitar artefato.

## 6. Riscos

- Os offsets são estimativas. Se estiverem curtos demais, ainda vaza; se longos demais, só perde frescor. Na dúvida, o conservador (mais longo) é o lado seguro. Fica registrado como débito: conferir no calendário oficial antes da Fase 3.
- O início da série fica com NaN, porque os primeiros meses não têm macro disponível. O cálculo do IRF já trata ausência com fallback, mas confirme que o NaN não vira 0 silencioso no `calcular_irf_v2`. Se virar, pare e reporte.
- O snapshot publicado continua com o IRF vazado. Isso é aceito até a Fase 3, e a revisão já diz que o IRF não é testável no dado atual.

## 7. Entrega

- Commits pequenos, sem push, sem trailer `Co-Authored-By`, sem menção a IA, nada de `git add .`. Sugestão:
  1. `fix(macro): disponibilidade por data de publicação, sem interpolação`
  2. `fix(irf): derivadas mensais e Copom sem bfill`
  3. `fix(features): entropia de wallets só até o dia da transação`
  4. `docs(agents): pipeline em lote D+1`
- Responder com: os hashes; a confirmação de que `test_medir_escada.py` não mudou e passa; o número de dias com NaN no início (§5.10); e qualquer ponto em que o código real divergiu desta spec, com a decisão tomada (o ideal é parar e perguntar antes).
