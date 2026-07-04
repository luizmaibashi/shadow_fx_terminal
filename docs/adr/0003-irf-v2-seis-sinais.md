# ADR-0003: IRF v2 com 6 Sinais Ortogonais

**Data**: 2026-05-05
**Status**: Accepted (supersedes IRF v1 — 3 sinais)
**Proposto por**: Luiz Maibashi
**Contexto**: Shadow FX Terminal — Feature de contexto macroeconômico

---

## 1. CONTEXTO (O QUÊ?)

O IRF v1 (3 sinais: câmbio, USDT, Copom) mostrou correlação forte com demanda por stablecoins (r=+0.707 com Dívida/PIB), mas deixava de capturar sinais importantes de risco fiscal estrutural. Precisávamos de um índice mais robusto que:
- Isolasse o efeito do dólar global (DXY) do risco Brasil puro
- Capturasse inflação desancorada, dominância fiscal e atividade econômica
- Tivesse pesos matematicamente justificados (não arbitrários)

---

## 2. DECISÃO (POR QUÊ?)

**O que escolhemos:**
IRF v2 com 6 sinais ortogonais, pesos calibrados por correlação histórica (Spearman vs demanda USDT) e PCA para validação de ortogonalidade.

| # | Sinal | Peso | Fonte | r (vs USDT) |
|---|-------|------|-------|-------------|
| 1 | Dívida Bruta/PIB (variação) | 30% | BCB | +0.707 |
| 2 | BRL ajustado por DXY (30d) | 20% | yfinance + derivado | +0.521 |
| 3 | Desvio IPCA vs meta (3%) | 15% | BCB | +0.45 |
| 4 | Tom Copom (hawkish/dovish) | 15% | Scraper Copom | -0.38 |
| 5 | Variação USDT (30d, log) | 10% | yfinance | +0.50 |
| 6 | IBC-Br (atividade, variação) | 10% | BCB | -0.32 |

**Razão principal (ROI statement):**
"IRF v2 explica 72% da variância da demanda por USDT vs 51% do v1 (R² ajustado). A adição de Dívida/PIB como preditor principal (r=+0.707) e o ajuste por DXY eliminam o principal confundidor (dólar global), reduzindo falsos positivos em período de estresse global."

---

## 3. CONSEQUÊNCIAS

**Positivas (Wins):**
- Aumento de 21pp no R² vs IRF v1
- Pesos defensáveis estatisticamente (PCA + correlação histórica)
- `brl_adj_dxy` isola risco local — decisivo para compliance regulatório
- Log-transform na variação USDT suaviza outliers (ex: +421% no pico FTX)
- Interpretabilidade: score 0-100 é compreensível para analistas de compliance

**Negativas (Custo/Risco):**
- 6 sinais = 6 pipelines de coleta de dados (mais pontos de falha)
- Dívida/PIB tem frequência mensal — cria descontinuidade no índice diário
- IPCA tem lag de publicação de ~15 dias (mitigado por IRF_LAG_DAYS=14)
- Dependência do scraper Copom para score hawkish/dovish

**Timeline:**
- Implementação: 3 dias (análise, calibração, refatoração)
- Benefit realization: imediato após deploy

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| **IRF v1 (3 sinais)** | Simples, já implementado | ❌ R² = 0.51 vs 0.72 do v2 — perdia Dívida/PIB que é o preditor mais forte |
| **Random Forest como IRF** | Captura interações não-lineares | ❌ Caixa-preta — compliance regulatório exige índice transparente e auditável |
| **Índice composto com pesos iguais** | Mais simples de calibrar | ❌ Dívida/PIB (r=0.707) merece mais peso que IBC-Br (r=0.32) — pesos iguais reduziriam acurácia |

---

## 5. IMPACTO ROI & VALIDAÇÃO

**Métrica de sucesso:**
- R² ajustado > 0.70 na correlação com demanda USDT (atingido: 0.72)
- Redução de 30% nos falsos positivos do pipeline (IRF v1 vs v2 em teste A/B com 1.000 transações)

**Monitoramento:**
- Recalcular correlações semestralmente (dados novos podem mudar pesos)
- Alerta se R² cair abaixo de 0.50

---

## 6. REFERÊNCIES & LINKS

- `src/utils.py` — `calcular_irf_v2()` (implementação)
- `notebooks/02_indice_risco_fiscal.ipynb` — Análise PCA e calibração
- `src/recalcular_irf.py` — Script de recálculo contínuo
- Britto, P.J. (2026). "Dolarização Informal" — OTC Research
