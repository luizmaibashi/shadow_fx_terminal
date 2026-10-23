# Spec — Fase 2b: C3 só onde o modelo acusa sem regra

**Data:** 2026-10-23 · **Implementa:** Codex · **Audita:** Claude · **Aprova:** Luiz
**Origem:** ADR-0009, revisado no mesmo dia (tabela de decisão e item 5). Esta spec **substitui** o trecho de `SPEC_FASE2_CASCATA.md` §3.3 que define `zona_cinza` como XOR. O resto daquela spec continua valendo.

## 1. Objetivo

Na primeira medição, 676 dos 688 casos enviados ao LLM eram "regra sim, modelo não": casos que já têm motivo legível. A mudança faz o C3 receber só "modelo sim, regra não".

## 2. Contrato (`decisao_cascata` em `src/pipeline_compliance.py`)

| `c1_suspeita` | `c2_positivo` | `alerta_final` | `zona_cinza` (vai a C3) |
|---|---|---|---|
| sim | sim | VERMELHO | False |
| não | não | VERDE | False |
| sim | não | AMARELO | **False** |
| não | sim | AMARELO | True |

- `zona_cinza = c2_positivo & ~c1_suspeita`.
- Com `limiar=None`, `zona_cinza` é False em tudo. Regra positiva continua AMARELO.
- A cor não muda em relação à versão atual. Muda só quem vai ao C3.

## 3. Escopo

**Incluído:** `src/pipeline_compliance.py` (`decisao_cascata` e a docstring), `src/medir_escada.py`, `tests/test_decisao.py`, `tests/test_medir_escada.py`.

**Já feito pelo Claude, não tocar:** `docs/adr/0009-cascata-real.md` e `docs/adr/README.md`.

**Fora de escopo:** o mesmo da spec da Fase 2 (`deploy/`, `.joblib`, app, API, site, `docs/spec/`, `dev/`) e os achados de `2026-10-ACHADOS_CODEX.md`.

**Dívida pequena, incluída:** `medir_escada.py` (linha ~127) recalcula `c1_suspeita` com o mesmo regex de `camada1_filtros_bcb`. Extraia uma função única em `pipeline_compliance.py` (por exemplo, `suspeita_de_razoes(razoes: pd.Series) -> pd.Series`) e use-a nos dois lugares.

## 4. Critério de aceitação

1. `tests/test_decisao.py`: a parametrização da tabela reflete o §2, com a linha "regra sim, modelo não" → AMARELO e `zona_cinza=False`. Novo teste: nenhuma linha com `c1_suspeita=True` tem `zona_cinza=True`, para qualquer limiar.
2. `tests/test_medir_escada.py`: atualizar `zona_cinza_transacoes_C3`, `zona_cinza_usuarios` e `fraudes_novas_por_100_cinza` para os números novos, que devem vir da execução e não de cálculo à mão. Precisão, recall, FP e poupadores tocados da cascata **não podem mudar**. Se mudarem, pare e reporte.
3. Os números da Fase 1 continuam iguais.
4. `pytest tests/ -q` verde e `ruff check src/ tests/ app.py tools/` limpo (o escopo do CI).

## 5. Entrega

- 1 commit: `fix(cascata): C3 só quando o modelo acusa sem regra (ADR-0009)`. O corpo traz os 3 números novos da zona cinza.
- Sem trailer `Co-Authored-By`, sem menção a IA, sem push, nada de `git add .`.
- Responder com o hash, o bloco "Cascata" de `python src/medir_escada.py` e a confirmação de que as 4 métricas de cor não mudaram.
