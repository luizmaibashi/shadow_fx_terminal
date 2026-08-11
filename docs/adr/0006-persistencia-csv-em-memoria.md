# ADR-0006 — Manter persistência em CSV/joblib carregados em memória (não migrar para banco de dados)

**Data:** 2026-08-10
**Status:** Aceito

## Contexto

O `src/api.py` carrega `dataset_irf_completo.csv`, `resultado_compliance.csv` e os artefatos do modelo (`isolation_forest_v1.joblib`, `scaler_v1.joblib`) para memória no startup (`_carregar_dados()`), sem banco de dados nem mecanismo de refresh — atualizar o dado exige reiniciar o processo.

O `docs/audit/audit_report_v2.md` classifica o projeto como "ENTERPRISE-READY (100% Validado)", o que superestima a maturidade de persistência atual. Isso foi identificado como um dos 5 débitos técnicos do projeto durante uma sessão de correção de bugs (2026-08-10), junto com um bug ativo (schema da API incompleto, corrigido nesta mesma sessão) e um caso de lógica duplicada entre `api.py` e `pipeline_compliance.py` (também corrigido).

## Decisão

**Não migrar para um banco de dados agora.** Mantemos CSV + joblib como formato de persistência.

## Justificativa

Este é um projeto de portfólio (`PROJETOS/02_PORTFOLIO/`), não um sistema em produção com usuários reais ou concorrência de escrita. Os critérios que justificariam um banco — múltiplos writers concorrentes, necessidade de query ad-hoc, volume que não cabe em memória, exigência de transação ACID — não se aplicam ao escopo atual: os dados são recalculados em lote por scripts (`coletar_dados.py`, `pipeline_compliance.py`) e servidos como leitura.

Migrar para SQLite ou Postgres agora seria overengineering: adiciona superfície de manutenção (schema, migrations, conexão) sem resolver nenhum problema real do projeto hoje, e desvia esforço de itens que têm valor de portfólio maior (rigor estatístico, governança CRISP-DM, correção de bugs).

## Alternativas consideradas

| Opção | Por que não agora |
|---|---|
| **SQLite** | Resolveria "sem banco" tecnicamente, mas sem concorrência real pra justificar — troca simplicidade operacional por infraestrutura sem ganho mensurável. |
| **Postgres + serviço de refresh** | Faz sentido só se o projeto virar proposta institucional real (multiusuário, API pública, SLA de atualização) — não é o caso hoje. |
| **Manter CSV/joblib em memória (escolhido)** | Reflete honestamente o estágio do projeto. Custo de mudança de rota é baixo se o critério de gatilho abaixo for atingido. |

## Gatilho para revisitar

Reabrir esta decisão se qualquer um destes ocorrer:
- O projeto sair de portfólio para uso institucional real (mesmo piloto).
- For necessário servir múltiplos consumidores escrevendo/lendo concorrentemente.
- O volume de dado ultrapassar o que é confortável carregar em memória no startup.

## Consequências

- `api.py` continua exigindo reinício do processo para refletir dado recalculado — aceito como limitação conhecida, não como bug.
- O relatório `docs/audit/audit_report_v2.md` deveria ser atualizado para não classificar o projeto como "100% enterprise-ready" sem qualificar esse ponto — fica registrado aqui como pendência de honestidade do relatório, não corrigido nesta sessão.
