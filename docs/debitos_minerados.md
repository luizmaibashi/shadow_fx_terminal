# Débitos minerados — shadow_fx_terminal

> Rodada 1: 2026-08-25, via skill `/minerar-debitos`. Fonte: `AGENTS.md` § Débitos técnicos conhecidos (4 itens numerados) + 1 fragilidade citada em prosa na seção "Auditoria de dependência — 2026-08-11" (não numerada, sem débito remanescente registrado formalmente).

| # | Débito (resumo) | Classificação | Destino |
|---|---|---|---|
| 1 | Dado em memória (DataFrame), não escala pra milhões de transação | Específico | — decisão de escopo consciente, ADR-0006 |
| 2 | Sem banco de dados, dado volátil entre restart | Específico | — mesmo débito do #1, ADR-0006 |
| 3 | `starlette` preso em 1.3.1 por constraint transitivo do Streamlit, CVEs altas/médias sem fix | Estrutural (gate novo) | Gate manual novo em `AGENTS.md` § Regras de engenharia: "Dependência transitiva trava patch de CVE sem revisão agendada". Sem sinal automático testado — texto do débito vive em prosa, não em formato grepável em `requirements.txt` |
| 4 | Resíduo de vulnerabilidade no stack Jupyter, sem uso em produção | Específico | — superfície de risco delimitada e documentada (não roda em prod/API) |
| 5 (não numerado) | `requirements-lock.txt` pinado em scikit-learn 1.9.0, mas `isolation_forest_v1.joblib` foi salvo com 1.8.0 — funciona com aviso, não corrigido | Estrutural (furo em gate existente) | Gate "Dependências travadas com versão exata" (`dados.md:185`) checa só **se existe pin**, não **se o pin bate com a versão real do artefato serializado**. Furo documentado como adendo MANUAL no mesmo gate — sem sinal automático (exigiria carregar o artefato pra ler a versão de serialização) |

## Achado da rodada

**2 débitos estruturais genuínos** (#3 e #5), nenhum automatizável com sinal barato testado — os dois ficam MANUAL, mesmo padrão das rodadas anteriores (payflow, pos_tech).

- **#3** é gate novo: primeira vez que a base registra o padrão "dependência transitiva trava CVE sem data de reavaliação" — pode se repetir em qualquer projeto com stack de UI (Streamlit/Gradio/etc) que force range de versão pra baixo.
- **#5** não é gate novo, é **furo num gate já existente** (o de dependências travadas, `dados.md:185`) — o próprio `shadow_fx_terminal` era citado nesse gate como *exemplo correto* (tem lock pinado), mas o pin existir não significa que ele corresponde à versão real usada pra treinar/serializar o modelo. Achado que só apareceu porque o texto do débito original ia além do que o gate checava — reforça a lição já registrada na rodada do stable-treasury: "ter pin" e "pin correto" são checagens diferentes.

3 débitos (#1, #2, #4) confirmados como específicos — decisões de escopo já documentadas via ADR ou risco delimitado, sem padrão generalizável novo.
