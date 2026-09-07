# ADR-0007: Dashboard estático em GitHub Pages

**Data:** 2026-09-07
**Status:** Accepted
**Proposto por:** Luiz Maibashi
**Contexto:** Dashboard público do Shadow FX Terminal

## Contexto

O dashboard público usava Streamlit Community Cloud para servir três CSVs já
calculados. Após 12 horas sem tráfego, a plataforma impõe cold start, criando
atrito justamente para a primeira visita de recrutador ou avaliador.

O caminho público não carrega o Isolation Forest, não chama a API FastAPI, não
escreve em banco e não usa Gemini sem chave. O Compliance Scanner é uma fórmula
determinística. Portanto, o runtime não entrega compute de servidor que justifique
seu custo operacional.

Os termos preservados nesta página são: IRF v2, Poupador Assustado, Fracionador,
Camada 1, score contextual e VERDE/AMARELO/VERMELHO. O scanner público declara
que é uma demonstração de regra, não a Camada 2 do pipeline.

## Decisão

Servir `docs/index.html` por GitHub Pages. O arquivo é gerado por
`scripts/site/gerar.py`, que reduz os três CSVs do snapshot público a um contrato
JSON único embutido no HTML. A leitura prefere `data/` do pipeline local e usa
`deploy/hf_space/data/` apenas como fallback público de geração.

Os gráficos são SVG nativo em JavaScript. Há três tipos de visualização, o que não
justifica adicionar biblioteca de gráficos. O scanner roda no navegador com a
fórmula explícita: valor, horário, carteiras, IRF e regras BCB.

## Consequências

### Positivas

- A página abre sem cold start e sem runtime Python.
- Todo número visível vem do contrato gerado, sem valor digitado no HTML.
- O payload reduz 4.509 transações a agregados e aos 15 alertas vermelhos de
  maior score, removendo campos que a página não utiliza.
- O scanner deixa de sugerir que executa Isolation Forest quando só demonstra
  a regra determinística.

### Negativas

- O snapshot só muda quando o gerador é executado e o HTML é commitado.
- A exploração livre de DataFrames do Streamlit não é reproduzida.
- A demo Streamlit fica temporariamente duplicada até a confirmação do Pages.

## Alternativas descartadas

| Opção | Motivo da rejeição |
|---|---|
| Manter Streamlit e alterar CSS | Não elimina o cold start e mantém runtime sem contrapartida. |
| Keep-alive agendado | Trata o sintoma, falha silenciosamente e mantém a dependência. |
| Framework de gráficos | Adiciona bundle e manutenção para três gráficos que SVG cobre. |
| Embutir as 4.509 transações | Aumenta a página e expõe dados que a interface não precisa. |

## Validação

- `tests/test_site_generator.py` valida agregados, omissão de `wallet_destino` e
  injeção do contrato no HTML.
- A página precisa responder em GitHub Pages e carregar sem dependência de
  Streamlit antes de aposentar a demo anterior.
- O scanner deve reproduzir os pesos 30/20/20/15/15 e indicar as regras BCB
  disparadas para qualquer cenário inserido.

## Riscos e mitigação

- Snapshot defasado: exibir a data de geração e a natureza histórica da página.
- Divergência entre fórmula Python e JavaScript: manter pesos explícitos e testes
  de contrato; qualquer alteração da regra exige revisão desta ADR.
- Leitura como produto operacional: manter limitações visíveis e a decisão humana
  como etapa final.

## Referências

- `docs/spec/deploy-pages.md`
- `scripts/site/gerar.py`
- `scripts/site/template.html`
- `docs/DECISAO_DEPLOY_PORTFOLIO.md` da Base de Conhecimento
