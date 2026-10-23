# Revisão Shadow FX Terminal — outubro/2026

**Data:** 2026-10-23 · **Fase:** diagnóstico e plano (sem código) · **Lente:** escada de degraus (processo/dado → regra → ML clássico → chamada LLM → agente); o LLM lê, propõe ou explica, quem decide é o código ou uma pessoa; ROI do processo inteiro; todo número com `n` e intervalo.

**Fonte das medições:** `deploy/hf_space/data/processed/resultado_compliance.csv` (snapshot do demo), lido sem alteração. Intervalos são Wilson 95%. Scripts de medição ficaram fora do repo (rascunho de sessão); a Fase 1 do plano os versiona.

---

## 0. Resumo em 5 linhas

1. **No dado sintético, a regra resolve o problema sozinha.** R3∪R4∪R5 pega 1.314 das 1.315 transações de fracionador (99,9% [99,6; 100,0], n=1.315), com 13 falsos positivos em 3.194 legítimas (0,4% [0,2; 0,7]). O Isolation Forest não acrescenta nenhuma fraude que a regra não pegou e acrescenta 225 alarmes falsos.
2. **Isso acontece porque o gerador embute o rótulo na regra.** Fraude é sorteada com valor uniforme entre R$ 8.500 e R$ 9.900 (= R4) em hora média 2h (= R5). O teste é circular: mede se o código reencontra o que o gerador escreveu.
3. **O IRF não tem como carregar sinal neste dado.** O gerador sorteia a data sem olhar o macro; o IRF é igual nas três classes (média 25,6 / 26,3 / 25,9; KS poupador × fracionador p=0,19). O ganho de 35,9% → 44,8% é efeito colateral da geometria do modelo, não do contexto. O poupador que compra mais quando o câmbio sobe nunca foi simulado.
4. **A cascata desenhada não é a cascata implementada, e o juiz não decide nada.** A Camada 2 roda em todas as transações; o veredito do LLM (`c3_veredito`) não entra em `score_final`, na API nem no app.
5. **O `n` que importa é de usuários: 10 fracionadores, 100 poupadores, 15 institucionais.** Intervalos por transação (n=4.509) dão falsa certeza, porque transações do mesmo usuário não são independentes.

**O que isso muda no pitch:** o projeto continua valioso, mas o valor está em outro lugar. A frase defensável hoje é "testei a escada e sei dizer, com número, quando subir um degrau não se paga". A tese do IRF continua de pé como hipótese, sem evidência a favor nem contra, porque o dado atual não consegue testá-la.

---

## 1. Dor e comprador

### O que o repo afirma

- `PROBLEM.md` e `TESE.md`: a obrigação nasce das Resoluções BCB 519-521 (VASP reporta suspeita ao COAF). O comprador implícito é a corretora autorizada (capital mínimo R$ 10,8 mi), que sofre com fila de alerta de regra fixa.
- O README cita R$ 4,9 bi de fraude via Pix (BC, via LAI) como contexto. **Não é** o custo da dor do comprador: fraude Pix é outro produto, outro fluxo, outro responsável.

### O que falta (e não dá pra tirar do repo)

| Pergunta | Estado | Evidência |
|---|---|---|
| Quem sofre? | Hipótese: time de compliance de VASP BR | Nenhuma conversa documentada (`TESE.md`, condição 3, aberta desde 2026-08) |
| Quanto custa hoje? | **Desconhecido** | Não há volume de alertas/dia, custo por analista nem tempo por caso |
| Custo do fracionador que passa (FN) | **Desconhecido** | Faixa de sanção do BCB e risco reputacional não levantados |
| Custo do poupador barrado (FP) | **Desconhecido** | Taxa de abandono após bloqueio não levantada |

Na sabatina de 23/10 o Luiz respondeu "comprador: não sei ainda". Isso é honesto, e transforma a pergunta em item de validação (Fase 4), não em premissa.

### "Equilíbrio perfeito" não existe; existe uma regra de decisão

O Luiz pediu equilíbrio entre pegar o fracionador e não punir o poupador. Não existe um ponto que maximize os dois: baixar o limiar pega mais fracionador e barra mais poupador, sempre. O que existe é escolher **a regra de decisão** que torna o trade-off explícito. Há duas formas clássicas:

1. **Custo esperado (quando se sabe quanto custa cada erro).** Sinaliza se `P(fraude | caso) > C_FP / (C_FP + C_FN)`. Se deixar um fracionador passar custa 50 vezes mais que barrar um poupador, o limiar cai para ~2%. Problema: hoje não sabemos `C_FN` nem `C_FP`.
2. **Teto de dano + máximo de captura (Neyman-Pearson).** Fixa-se um teto para o dano ao poupador ("no máximo X% dos poupadores podem cair na fila") e, dentro desse teto, escolhe-se o limiar que pega mais fracionador. Esse teto é decisão de negócio, não de modelo, e é bom porque dispensa saber o custo exato em reais.

**Recomendação:** usar a forma 2 com uma restrição operacional a mais, a capacidade da fila (K casos por dia que o analista consegue ver). A pergunta vira: *"com no máximo X% de poupadores incomodados e no máximo K alertas por dia, quantos fracionadores eu pego?"*. Isso é medível, comparável entre degraus e explicável para um diretor de compliance. A forma 1 entra como análise de sensibilidade (razões FN:FP de 1:1, 10:1 e 50:1), até a Fase 4 trazer números reais.

→ **Pede ADR** (critério de decisão do sistema). Ver §5.

---

## 2. Escada de degraus: cada degrau se paga?

### 2.1 A cascata de papel × a implementada

| Desenho (`PROBLEM.md`) | Código (`src/pipeline_compliance.py`) |
|---|---|
| C1 libera o verde; só o caso com flag vai para C2 | `inferir_score()` roda em **todas** as linhas (l. 377) |
| Zona cinza de C2 vai para C3 | Zona cinza = score 40-70 em todas as linhas, com ou sem flag de C1 (l. 384) |
| C3 julga e decide | `c3_veredito` não é lido por `score_final` (l. 405-408), pela API nem pelo app |
| Score final combina camadas | `score_final = 0,6·C2 + 16·C1`; o maior valor possível com flag e C2=100 é 76 |

Consequência: dos 1.164 casos cinza, 82 são de poupador **sem flag nenhum de regra** (60 usuários). Na cascata desenhada eles teriam sido liberados no primeiro degrau, sem custo.

### 2.2 Medição degrau a degrau (unidade: transação, n=4.509)

| Degrau | Sinaliza | Precisão | Recall (fracionador) | FP em legítimos |
|---|---|---|---|---|
| C1 completa (R1-R6) | 3.345 | 39,3% [37,7; 41,0] | 100% [99,7; 100,0] | 2.030/3.194 = 63,6% [61,9; 65,2] |
| **Regra de comportamento R3∪R4∪R5** | 1.327 | **99,0% [98,3; 99,4]** | **99,9% [99,6; 100,0]** | **13/3.194 = 0,4% [0,2; 0,7]** |
| C2 "suspeito" (>70) | 369 | 39,0% [34,2; 44,1] | 11,0% [9,4; 12,8] | 7,0% [6,2; 8,0] |
| `alerta_final` ≠ VERDE | 1.460 | 44,8% [42,3; 47,4] | 49,7% [47,0; 52,4] | 25,2% [23,8; 26,8] |

Leitura:
- R1/R2 (valor e volume) acertam o institucional legítimo em cheio: todos os 2.030 casos de B caem ali. São regras de **reporte obrigatório**, não de suspeita; misturá-las com R3-R5 no mesmo `c1_flag` é o que infla a Camada 1 para 74%.
- O modelo dá score < 40 a 654 transações de fracionador que a regra pegou, e score > 70 a 225 transações sem nenhuma regra de comportamento, todas legítimas (0/225, IC [0; 1,7]). **Neste dado, o degrau 2 tem valor marginal negativo:** só acrescenta alarme falso.
- Por usuário (o `n` honesto): a regra R3∪R4∪R5 pega 10/10 fracionadores (IC [72; 100]) e toca 10/115 legítimos (8,7% [4,8; 15,3]), todos institucionais com transação de madrugada; poupadores tocados: 0/100 (IC [0; 3,7]).

### 2.3 Por que a regra ganha: o gerador é circular

`src/gerador_transacoes_mock.py`: fracionador gera `valor ~ U(8.500; 9.900)` (l. 73) e `hora ~ N(2, 2)` (l. 138). As regras R4 (R$ 8.000-9.999) e R5 (0h-5h e > R$ 5.000) foram escritas com o mesmo número. Não é bug de modelo, é desenho de teste: a pergunta "a regra pega o fracionador?" foi respondida na hora em que o gerador foi escrito.

**Diagnóstico da escada:** o resultado atual não diz se o ML ou o LLM se pagam no mundo real. Diz que **o dado não tem nenhum caso em que a regra falha**, e sem esse caso nenhum degrau acima tem trabalho a fazer. Antes de estreitar a zona cinza, é preciso um dado em que a regra erre.

### 2.4 Como estreitar a zona cinza, e com que critério

Cortar o intervalo 40-70 no olho só troca um número arbitrário por outro (50-70 dá 603 casos, 13,4%; 60-70 dá 263, 5,8%). O critério certo é **rendimento por chamada**:

> **Zona cinza = casos em que os degraus baratos discordam** (regra de comportamento diz sim e o modelo diz não, ou o contrário), restritos aos casos que C1 não liberou.
>
> **Métrica de corte:** fracionadores *novos* encontrados por 100 casos enviados ao degrau seguinte (os que a regra sozinha não pegaria), comparada com o custo por caso desse degrau. O degrau só se liga se o rendimento, com IC, ficar acima do ponto em que o custo do caso iguala o valor de uma fraude evitada.

No dado atual, esse rendimento é zero: os casos em que só o modelo acusa têm 0 fraudes em 225 (IC [0; 1,7]). Ou seja, com este dado **o juiz não deveria ser ligado**, e isso é um resultado, não uma falha. A meta "≤ 1% para o LLM" vira consequência do critério, não um número escolhido.

→ **Pede ADR** (cascata real: separar reporte obrigatório R1/R2 de suspeita R3-R6; zona cinza por discordância). Ver §5.

---

## 3. Juiz LLM: eval mínimo e custo

### 3.1 O que existe

- `src/agente_rag.py`, `julgar_transacao_llm()`: Gemini 2.5 Flash, `temperature=0.2`, saída em texto com `VEREDITO/JUSTIFICATIVA/RASCUNHO COAF`, extraída linha a linha por `startswith`.
- "RAG" = a ata do Copom mais recente antes da data, cortada em 500 caracteres, mais o tom (hawkish/dovish). Uma consulta por data, sem busca semântica.
- Validado uma vez com chamada real (2026-08-11). **Nunca avaliado contra gabarito.** No CSV, os 1.164 casos estão em `FALLBACK`.

### 3.2 Três problemas que impedem avaliar agora

1. **Vazamento de rótulo no prompt.** O juiz recebe `c1_razoes` ("R4:fracionamento_suspeito|R5:madrugada"). No sintético, isso é o próprio rótulo. Um eval agora mediria se o LLM sabe ler "fracionamento_suspeito" e responder "SUSPEITO".
2. **O veredito não tem consequência.** Mesmo correto, não altera nenhuma decisão. Pela filosofia (LLM lê, propõe ou explica; quem decide é código ou pessoa), isso pode estar certo, mas então o papel do juiz precisa ser escrito: **ordenar a fila do analista e redigir o rascunho**, não decidir.
3. **Parse frágil.** Uma resposta com markdown (`**VEREDITO:**`) cai no default `REQUER_INVESTIGACAO` sem aviso. Falha silenciosa que parece resultado. Saída estruturada (schema JSON) resolve.

### 3.3 Eval proposto (pequeno, honesto)

| Item | Desenho |
|---|---|
| **Pergunta** | O juiz ordena a fila melhor que o score sozinho, nos casos em que os degraus baratos discordam? |
| **Gabarito** | 60 casos da zona cinza do gerador v2 (§4), estratificados **por usuário** (no máximo 2 casos por usuário): 30 de fracionador, 30 de poupador/institucional. Rótulo do gerador + 1 linha de justificativa escrita pelo Luiz **antes** de ver a saída do LLM. |
| **Entrada do juiz** | Sem `c1_razoes` cru; só os fatos (valor, hora, nº de wallets, IRF, ata). |
| **Métricas** | (a) acerto do veredito binário com IC Wilson; com n=60, 80% de acerto dá [68; 88], ou seja, o eval só distingue diferenças acima de ~15 p.p.; (b) taxa de `REQUER_INVESTIGACAO` (abstenção); (c) estabilidade: mesmos 60 casos em 3 execuções, % de concordância; (d) taxa de parse falho. |
| **Baseline obrigatório** | Regra + score de C2 nos mesmos 60 casos. O juiz só fica se o IC do ganho sobre o baseline não cruzar zero. |
| **Abandono** | Ganho com IC cruzando zero → juiz vira só redator de rascunho COAF (sem papel na ordem da fila), e o pitch para de dizer "LLM-as-Judge". |
| **Custo de rotular** | ~60 casos × 1-2 min ≈ 1-2 h do Luiz. É aí que o aprendizado fica com ele (zona de julgamento). |

Liga à frente `evals_observabilidade` (`brain/sessions/frentes/evals_observabilidade.md`): é um caso real e pequeno para aplicar a lição de gabarito + IC + baseline, em vez de exemplo de curso.

### 3.4 Custo por caso

Estimativa pelo prompt atual: ~200 tokens de instrução de sistema + ~150 de dados + ~150 de ata ≈ **500 tokens de entrada**; saída de ~200 tokens, mais os tokens de raciocínio que o Gemini 2.5 Flash usa por padrão (podem ir de 0 a ~1.500 por caso, cobrados como saída).

`custo_por_caso = 500 × P_in + (200 + tokens_de_raciocínio) × P_out`

Com o preço de tabela que conheço (US$ 0,30 por milhão de tokens de entrada e US$ 2,50 por milhão de saída; **conferir na página de preços do Google antes de rodar**, porque muda): de ~US$ 0,0007 (raciocínio desligado) a ~US$ 0,004 por caso. Para 1.164 casos, US$ 0,8 a 4,6 por execução; multiplicar pelo câmbio do dia para R$.

**Leitura de negócio:** o custo em dinheiro do LLM é irrelevante. O custo que importa é **o tempo do analista que lê o que o juiz mandou para a fila**. Se o juiz manda 1.164 casos por lote para revisão humana a ~3 min cada, são ~58 horas de analista. É por isso que o rendimento por chamada (§2.4) vale mais que o preço do token. O eval deve registrar tokens reais por caso (`usage_metadata`), não esta estimativa.

---

## 4. IRF: o que sustentaria a tese

### 4.1 Por que o resultado atual não sustenta nem derruba

- O IRF varia no tempo; as três classes sorteiam datas da mesma forma. Distribuição do `irf_contexto` por classe: médias 25,6 / 26,3 / 25,9; KS poupador × fracionador D=0,043, p=0,19. **Por construção, o IRF não informa nada sobre o rótulo.**
- Então o ganho de precisão 35,9% → 44,8% não pode ser "o modelo entende o contexto". É o Isolation Forest isolando pontos de outro jeito porque ganhou uma dimensão a mais. A oscilação de 2,3x a 3,5x no FP do poupador entre rodadas de correção de bug é o sintoma: um efeito real não oscila tanto com mudança de calibração.
- A ablação não está versionada e foi feita por transação; com 10 fracionadores, qualquer IC honesto (por usuário) seria largo.
- A tese promete **reduzir** o FP do poupador em dia de estresse. O resultado medido vai na direção oposta (FP sobe). O README já registra isso, o que é correto.

### 4.2 O que medir

1. **Gerador v2 com o mecanismo da tese.** O poupador passa a comprar mais (frequência e valor) quando o câmbio/IRF sobe; o fracionador **não** reage ao macro. Incluir também fracionadores que não cabem na regra (valor fora de 8.000-9.999, horário comercial, poucas wallets), senão a regra continua resolvendo tudo. Subir o número de usuários (ex.: 200 fracionadores, 1.000 poupadores) para o IC por usuário ficar útil.
2. **Placebo.** Mesmo gerador v2, com o acoplamento macro desligado. O IRF **tem** que dar ganho ≈ 0 aqui. Se "ganhar" no placebo, o método de medição está quebrado e nenhum resultado vale.
3. **Ablação no ponto de operação certo.** Comparar com IRF × sem IRF no mesmo teto de dano ao poupador (§1, ex.: ≤ 2% dos poupadores incomodados) e mesma capacidade de fila, não no limiar 40/70 implícito.
4. **Recorte de estresse.** Medir o FP do poupador separadamente nos dias de IRF alto (quartil superior). É a promessa central.
5. **Unidade e intervalo.** Bootstrap por usuário (reamostra usuários, não transações), IC 95%. Split de treino/teste por usuário (`GroupShuffleSplit`), ajuste de limiar só no treino.

### 4.3 Critério de abandono (o Luiz pediu ajuda para definir)

Um critério de abandono responde: *"que resultado me faria parar de defender isto?"*. Precisa ser escrito antes de rodar, senão vira racionalização depois. Para o IRF, proponho três condições; **falhar em qualquer uma tira o IRF do pitch como diferencial**:

| # | Condição | Por quê |
|---|---|---|
| A | No placebo, ganho do IRF com IC contendo zero | Prova que a medição não inventa efeito |
| B | No v2, ganho de recall (com IRF − sem IRF), no mesmo teto de dano ao poupador, com limite inferior do IC 95% > 0 | O IRF agrega algo além do degrau sem ele |
| C | Nos dias de IRF alto, FP do poupador com IRF ≤ FP sem IRF (limite superior do IC da diferença ≤ +1 p.p.) | É a promessa do projeto; ganhar recall barrando mais poupador não é a tese, é outra coisa |

Ressalva que vale escrever no README se passar: **passar no sintético prova que o mecanismo funciona quando existe, não que existe no mundo.** O gerador v2 é escrito por quem tem a tese, então sempre há risco de construir o resultado. A prova de existência só vem com dado real ou com alguém do setor confirmando o comportamento (Fase 4).

---

## 5. Decisões que pedem ADR

| ADR proposto | Decisão a registrar | Identificador que o critério cita |
|---|---|---|
| 0008 — Critério de decisão por teto de dano | Ponto de operação = máximo recall de fracionador com FP de poupador ≤ X% e alertas/dia ≤ K; sensibilidade de custo 1:1, 10:1, 50:1 | `escolher_limiar_operacao` (a criar) |
| 0009 — Cascata real | Separar reporte obrigatório (R1/R2) de suspeita comportamental (R3-R6); C2 só no que não foi decidido; zona cinza = discordância entre degraus | `camada1_filtros_bcb`, `inferir_score`, `mask_cinza` |
| 0010 — Papel do juiz LLM | LLM ordena a fila e redige rascunho; não decide; saída estruturada com schema; sem `c1_razoes` no prompt | `julgar_transacao_llm`, `c3_veredito` |
| 0011 — Gerador v2 + placebo | Acoplamento macro só no poupador; fracionador fora da regra; flag de placebo; avaliação por usuário | `gerar_dataset` |

O ADR-0002 (Gemini como juiz) fica como está até o eval; se o critério de abandono do §3.3 disparar, vira `Superseded` pelo 0010.

---

## 6. Plano em fases

Orçamento combinado: **~2 semanas**, concorrendo com TC4 (16/11) e com a etapa final da Innoscience. Sequência pedida pelo Luiz: portfólio honesto primeiro, validação de dor depois.

| Fase | Entrega | Esforço | Critério de pronto | Critério de abandono / corte |
|---|---|---|---|---|
| **1. Narrativa honesta** (antes de 16/11) | README/PROBLEM: escada medida (§2.2), circularidade do gerador, IRF "não testável no dado atual", juiz "não avaliado e sem efeito na decisão". Script de medição versionado (`reports/`) | 1-2 dias | Todo número da §2.2 reproduzível por um comando, com `n` e IC | — (é correção de afirmação pública; não se corta) |
| **2. Cascata real + regra de decisão** | ADRs 0008 e 0009; implementação via spec (Codex implementa, Claude audita) | 2-3 dias | Mesma tabela da §2.2 com a cascata nova; fração enviada a C3 medida | Se a TC4 apertar, para aqui. O portfólio já fica coerente com a Fase 1 |
| **3. Gerador v2 + teste do IRF** | ADR 0011; placebo + v2; ablação por usuário | 3-4 dias | Condições A, B e C da §4.3 avaliadas | Qualquer condição falha → IRF sai do pitch como diferencial e vira "contexto exibido ao analista" |
| **4. Eval do juiz** | ADR 0010; gabarito de 60 casos rotulado pelo Luiz; métricas da §3.3 | 2 dias + 1-2 h de rótulo | Acerto e ganho sobre baseline com IC | IC do ganho cruza zero → juiz vira só redator de RIF |
| **5. Validar a dor** (após 16/11) | 1-2 conversas com compliance de VASP BR; volume de alerta/dia, tempo por caso, custo de FN/FP | 1 semana corrida, poucas horas | Notas de conversa com números | Nenhum interlocutor em 30 dias → projeto fica como portfólio fechado, sem tese de receita |

**Decisão do Luiz (2026-10-23):** aprovado. Antes de 16/11, só a Fase 1. Fases 2-4 depois do TC4.

**Revista no mesmo dia (2026-10-23, depois do CI verde da Fase 1):** o Luiz decidiu adiantar as Fases 2-4 antes do TC4, ciente de que concorrem com as pendências da TC4 (prévias da spec 0012, ensaio do vídeo, publicação do repo). O `/tese` continua obrigatório antes da Fase 3. O corte da Fase 2 ("se a TC4 apertar, para aqui") continua valendo.

Fases 1-4 somam ~9-11 dias úteis: dentro das 2 semanas, mas apertado com o TC4. **Recomendação:** fazer só a Fase 1 antes de 16/11. Ela tem o maior retorno por hora (corrige uma afirmação pública e vira a melhor história de entrevista: "achei que meu próprio teste era circular"). Fases 2-4 depois do TC4.

Pelo checklist da skill `tese`, o plano completo passa de 2 semanas e mexe com carreira (2 de 3 "sim"): **rodar `/tese` antes da Fase 3**, com a pergunta "vale gastar mais 1-2 semanas no Shadow FX, ou o portfólio corrigido já basta para a vaga-alvo?".

---

## 7. Riscos verificados

- **Gates que dispararam:** proporção sem `n`/IC (corrigido aqui); unidade de análise vazando (transação × usuário, §4.2); comparação modelo × baseline (regra nunca foi baseline do ML, §2.2); saída de LLM como gabarito (evitado: o gabarito é rótulo do gerador + humano, §3.3).
- **Omitido de propósito:** reprodução da ablação do IRF (não versionada; refazer é Fase 3); preço oficial do Gemini (estimado, marcado para conferência).
- **Origem do dado:** sintético, `gerador_transacoes_mock.py`, seed 2024. Nenhuma transação real.
- **Clone local:** os 3 `.joblib` em `deploy/hf_space/models/` aparecem modificados pelo filtro LFS (ver `AGENTS.md`); não foram tocados nesta revisão e não devem ser commitados.
