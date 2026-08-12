---
title: Shadow FX Terminal
emoji: 📊
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: "1.51.0"
app_file: app.py
pinned: false
license: mit
---

# Shadow FX Terminal — Demo

Dashboard de compliance AML pra stablecoin com contexto macroeconômico (IRF) injetado no modelo.

**Este é o demo isolado do dashboard** — sem o backend FastAPI (o dashboard chama a lógica de compliance direto em processo, não via API) e sem a Camada 3 (LLM-as-judge) ativa, pra não gerar custo de API em cima de tráfego público.

Transações processadas são **simuladas** (dataset sintético com perfil conhecido); o contexto macroeconômico (câmbio, IPCA, Selic, atas do Copom) é **100% real**. Detalhe completo da metodologia, do trade-off medido e das limitações: [repositório no GitHub](https://github.com/luizmaibashi/shadow_fx_terminal).
