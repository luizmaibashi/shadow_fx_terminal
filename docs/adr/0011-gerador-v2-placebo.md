# ADR-0011: Gerador v2 com placebo para testar o IRF

**Data:** 2026-10-23
**Status:** Accepted
**Proposto por:** Luiz Maibashi
**Contexto:** `src/gerador_transacoes_mock.py` (`gerar_dataset`), `src/macro_disponibilidade.py`, `src/decisao.py`. Origem: `docs/revisao/2026-10-REVISAO.md` §4. Decisão de seguir: `docs/tese/shadow-fx-fase3-vale-a-pena/TESE.md`

## Contexto

O dado atual não consegue testar a tese do IRF (Índice de Risco Fiscal), e isso acontece por construção, não por azar:

- `gerar_usuario` sorteia a data de toda transação com `np.random.randint(0, DIAS_TOTAL)`, igual para as três classes. O IRF é idêntico nas três (médias 25,6 / 26,3 / 25,9; KS poupador × fracionador p=0,19).
- O fracionador é sorteado com valor uniforme entre R$ 8.500 e R$ 9.900 em hora média 2h, o que é exatamente o que R4 e R5 procuram. A regra pega 1.314 de 1.315 transações de fracionador, e não sobra nada para o modelo provar.
- São 10 fracionadores. Qualquer intervalo de confiança por usuário fica largo demais para separar efeito de ruído.

Conferência dos offsets de publicação (`OFFSET_DISPONIBILIDADE_DIAS`, contados do dia 1 do mês de referência), feita em 2026-10-23:

| Série (SGS) | Offset atual | Evidência | Margem |
|---|---|---|---|
| IPCA (433) | 45 | Set/2026 já disponível em 23/10 (IBGE divulga por volta do dia 10 de M+1, ~40 dias) | ~5 dias |
| IBC-Br (24364) | 80 | Mai/2026 divulgado em 17/07/2026 (77 dias); Ago/2026 já disponível em 23/10 (≤83 dias) | **3 dias ou negativa** |
| Dívida bruta (4537) | 65 | Dez/2025 divulgado em 30/01/2026 (60 dias) | 5 dias |
| "Expectativa IPCA 12m" (13521) | 35 | **A série é a meta de inflação, não a expectativa Focus**: 3,50 (2022), 3,25 (2023), 3,00 (2024+) | — |

Achados colaterais:
- `desvio_meta_ipca = ipca_acum_12m − 3,0` usa a meta fixa em 3,0, mas a meta era 3,5 em 2022 e 3,25 em 2023. A calibração p95 do IRF v2 (2022-2025) herda esse erro. No período do gerador (2024-01 a 2025-06) a meta é 3,0, então as transações não mudam, mas os limiares de calibração mudam.
- `divida_bruta_pib` local começa em 88,28% (jan/2022), e a DBGG publicada fechou 2025 em 78,7%. A série 4537 pode ser outra definição (metodologia antiga ou outro recorte). A API SGS recusou a consulta em 23/10, então isso fica como verificação, não como fato.

## Decisão

### 1. Offsets e meta (antes de gerar qualquer dado)

- IBC-Br: 80 → **90 dias**. Dívida bruta: 65 → **70 dias**. IPCA continua em 45. No lote D+1, um sinal que chega atrasado custa pouco, porque o macro é lento. Um sinal que chega adiantado é vazamento.
- A coluna 13521 vira `meta_inflacao`, com offset 0 (o CMN fixa a meta com anos de antecedência). `desvio_meta_ipca = ipca_acum_12m − meta_inflacao`, sem a constante 3,0.
- Verificar a definição da série 4537 nos metadados do SGS. Se não for DBGG, trocar o código, registrar no `AGENTS.md` e recalibrar.
- Regenerar `dataset_irf_completo.csv` (`recalcular_irf.py`) depois dessas mudanças. O `IRF_LAG_DAYS = 14` do pipeline continua por cima (margem dupla, consciente).

### 2. Gerador v2 em módulo novo

`src/gerador_v2.py`, com `gerar_dataset_v2(irf_diario, acoplamento, seed)`. O v1 **não muda**, porque o teste da Fase 1 trava os números do snapshot do demo.

| Classe | Usuários | Comportamento |
|---|---|---|
| Poupador | 1.000 | Intensidade diária `λ(t) = λ₀ · exp(β · z(t))` e ticket `× (1 + γ · max(z(t), 0))`, com `z` = IRF padronizado **disponível em t**. Com acoplamento: β=0,7 e γ=0,3 |
| Fracionador clássico | 100 | Como o v1 (dentro de R4/R5). Não reage ao macro |
| Fracionador fora da regra | 100 | Valor R$ 4.000-7.900 (fora de R4), hora 9-18 (fora de R5), 2-4 wallets distintas por dia (fora de R3); frequência 3-6 tx/dia em rajadas. Não reage ao macro |
| Institucional | 50 | Como o v1 |

**Placebo:** a mesma função com `acoplamento=False` (β=γ=0), com `λ₀` reescalado para que o volume esperado do poupador seja igual ao do v2. Assim a única diferença entre os dois mundos é o acoplamento com o macro.

β e γ ficam fixados aqui, **antes** de medir. Eles não serão ajustados depois para fazer o IRF passar. Com β=0,7, um dia no quartil superior do IRF (z ≈ 1) tem ~2x a intensidade de compra de um dia médio.

### 3. Medição (`src/medir_irf.py`)

- Para cada mundo (v2 e placebo), treinar dois Isolation Forest (com e sem `irf_contexto`, mesmo `random_state`) **só nos usuários de calibração** (`split_por_usuario`, seed 42).
- O limiar de cada modelo vem de `escolher_limiar_operacao` com `x_max=0,05` (ADR-0008), na calibração. A medição é feita na avaliação.
- Bootstrap pareado por usuário (B=2.000; reamostra usuários de avaliação dentro de cada classe; a mesma reamostra para com e sem IRF). IC 95% percentil da diferença.
- Condições de abandono, como em `docs/revisao/2026-10-REVISAO.md` §4.3:
  - **A:** no placebo, o IC do ganho de recall contém zero.
  - **B:** no v2, o limite inferior do IC do ganho de recall é > 0.
  - **C:** no v2, nos dias de IRF no quartil superior, o limite superior do IC da diferença de FP do poupador (com − sem) é ≤ +1 p.p.
- Falhar em qualquer condição tira o IRF do pitch como diferencial. Ele passa a ser "contexto exibido ao analista".

## Consequências

- **Positivas:** o experimento passa a poder falhar. A regra não resolve mais tudo, e o placebo mostra se a medição inventa efeito. O `n` de 200 fracionadores dá IC por usuário com largura útil.
- **Negativas:** o gerador v2 é escrito por quem tem a tese. Passar prova que o mecanismo funciona **quando existe**, não que existe no mundo. Isso vai para o README se passar.
- **Fora de escopo:** regenerar o snapshot do demo, o modelo publicado, o app e o site. Isso só acontece depois do resultado, e por decisão separada.

## Alternativas descartadas

- **Editar o v1:** quebraria o teste que trava os números da Fase 1 e apagaria a comparação antes/depois.
- **Acoplar o fracionador ao macro também:** tornaria o IRF inútil por construção, e o teste viraria outro.
- **Escolher β depois de ver o resultado:** seria ajuste ao resultado. Também foi descartada uma varredura de β como critério; ela pode entrar como análise de sensibilidade, nunca como gate.
- **Usar o IRF de t sem atraso de publicação no gerador:** o poupador reagiria a uma informação que ninguém tinha no dia.

## Validação

- Testes em `tests/test_gerador_v2.py` e `tests/test_medir_irf.py` (spec `docs/revisao/SPEC_FASE3_GERADOR_V2.md`).
- Sinal de que o gerador faz o que diz: correlação de Spearman entre z(t) e o número de compras diárias do poupador > 0 no v2 e ≈ 0 no placebo; fracionador ≈ 0 nos dois.
- Predição do Luiz registrada **antes** de rodar `medir_irf.py` em tamanho real.
