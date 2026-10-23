# Prompt para o Codex: Fase 2 + revisão do projeto

Abra a sessão do Codex com o diretório de trabalho em `PROJETOS/02_PORTFOLIO/shadow_fx_terminal` e cole o bloco abaixo inteiro.

---

```text
Você vai fazer duas tarefas neste repositório (shadow_fx_terminal), nesta ordem. Responda em português.

## Antes de tudo, leia
1. AGENTS.md (linguagem ubíqua, regras de engenharia, aviso sobre LFS)
2. docs/revisao/SPEC_FASE2_CASCATA.md (contrato da tarefa 1)
3. docs/adr/0008-criterio-decisao-teto-de-dano.md e docs/adr/0009-cascata-real.md
4. docs/revisao/2026-10-REVISAO.md, §2 e §5

Regras que valem para as duas tarefas:
- NUNCA use `git add .` nem `git add -A`. Adicione arquivo por nome. Os 3 .joblib em
  deploy/hf_space/models/ aparecem modificados por causa do filtro LFS: não toque neles, não faça commit deles.
- Não toque em docs/spec/ nem em dev/ (pertencem a outra sessão).
- Commits em Conventional Commits, em português, sem trailer Co-Authored-By e sem mencionar IA.
- Não faça push.
- Se algo na spec for ambíguo ou parecer errado, PARE e escreva a dúvida em vez de decidir sozinho.

## Tarefa 1: implementar a Fase 2
Implemente exatamente o que está em docs/revisao/SPEC_FASE2_CASCATA.md, respeitando o escopo do §2
(arquivos incluídos e fora de escopo). Siga os commits sugeridos no §6.
Antes de cada commit, rode `pytest tests/ -v` e `ruff check .`.
Use o Python do .venv do projeto, se existir.
Pronto = os critérios do §4 atendidos.

## Tarefa 2: revisão do projeto (só leitura, sem correção)
Depois da tarefa 1, revise o repositório inteiro procurando problemas que a revisão de 2026-10 NÃO cobriu.
Não corrija nada: só registre. Prioridades:
- Bugs de lógica em src/ (pipeline, api.py, agente_rag.py, utils.py, gerador_transacoes_mock.py)
- Vazamento de dado (IRF_LAG_DAYS, features calculadas com informação do futuro, uso do rótulo)
- Divergência entre src/ e a cópia em deploy/hf_space/src/
- Afirmações do README.md, PROBLEM.md e AGENTS.md que o código ou os números não sustentam
- Testes que passam sem testar nada (asserção fraca, skip silencioso, mock que esconde o comportamento)
- Segurança da API (auth, CORS, validação de entrada, clamp silencioso de valor)
- Dependências e reprodutibilidade (scikit-learn 1.8 vs 1.9, lock, Dockerfile)

Grave em docs/revisao/2026-10-ACHADOS_CODEX.md uma tabela com estas colunas:
| # | Severidade (alta/média/baixa) | Arquivo:linha | Achado | Evidência (comando ou trecho que reproduz) | Sugestão |
Só entra achado com evidência verificável. Separe "confirmado (reproduzi)" de "suspeita (não reproduzi)".
Não repita o que já está em docs/revisao/2026-10-REVISAO.md nem nos débitos do AGENTS.md.
Faça commit desse arquivo separadamente: `docs(revisao): achados da revisão do Codex`.

## Ao terminar, me responda com
1. Os hashes dos commits, com 1 linha cada
2. A saída do bloco novo de `python src/medir_escada.py`
3. Os testes alterados em tests/test_pipeline_compliance.py e o motivo de cada um
4. O que ficou ambíguo na spec e a decisão que você tomou (se houver)
5. Quantos achados da revisão existem por severidade, e os 3 mais graves em 1 linha cada
```
