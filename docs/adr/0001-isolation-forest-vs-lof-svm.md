# ADR-0001: Isolation Forest como Motor de Detecção de Anomalias

**Data**: 2026-05-17
**Status**: Accepted
**Proposto por**: Luiz Maibashi
**Contexto**: Shadow FX Terminal — Camada 2 do pipeline de compliance

---

## 1. CONTEXTO (O QUÊ?)

Precisávamos de um algoritmo de detecção de anomalias não-supervisionado para classificar transações de stablecoins como normais ou suspeitas, usando features comportamentais + macroeconômicas (IRF).

**Restrições técnicas:**
- Pipeline precisa processar milhares de transações/dia com latência < 10ms por transação
- Dados são tabulares com 4 features contínuas
- Non-stationarity: o comportamento "normal" muda com o cenário macro (IRF)
- Precisa ser explicável para auditoria regulatória (BCB/COAF)

**Métricas alvo:**
- Latência média: < 5ms por amostra
- AUC-ROC > 0.85 no benchmark
- Score normalizado [0, 100] interpretável por analistas de compliance

---

## 2. DECISÃO (POR QUÊ?)

**O que escolhemos:**
Isolation Forest (scikit-learn) como modelo campeão, com `n_estimators=200`, `contamination=0.07`.

**Razão principal (ROI statement):**
"Isolation Forest oferece O(n log n) escalabilidade (vs O(n²) do LOF), não assume distribuição dos dados (vs One-Class SVM), e produz scores nativamente interpretáveis como 'profundidade de isolamento' — sem custo de infraestrutura adicional (roda em CPU, sem GPU)."

---

## 3. CONSEQUÊNCIAS

**Positivas (Wins):**
- Escalabilidade linear: 4.500 transações processadas em ~45ms
- Score nativo de anomalia sem necessidade de calibração de threshold (basta normalizar)
- Sem premissa de distribuição normal dos dados (adequado para dados financeiros com cauda pesada)
- Fácil serialização com joblib para paridade treino-serviço

**Negativas (Custo/Risco):**
- Isolation Forest assume features independentes — entropia_wallets e irf_contexto podem ter interação não capturada
- Sem detecção de outliers locais (LOF é superior para padrões regionais)
- Contamination rate é hiperparâmetro sensível (calibrado em 0.07 via grid search)

**Timeline:**
- Implementação: 2 dias (notebook 03 + treinar_modelo.py)
- Benefit realization: imediato após deploy

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| **LOF (Local Outlier Factor)** | Melhor para outliers locais | ❌ O(n²) no pior caso — não escala para >10k transações; instável com dados esparsos |
| **One-Class SVM** | Robusto para fronteiras não-lineares | ❌ O(n²) a O(n³) — inviável para pipeline em tempo real; requer tuning de kernel e gamma |
| **Autoencoder (Deep Learning)** | Captura interações não-lineares | ❌ Overkill para 4 features; custo de infra (GPU); difícil explicabilidade para auditoria |

---

## 5. IMPACTO ROI & VALIDAÇÃO

**Métrica de sucesso:**
- AUC-ROC no benchmark: 0.91 vs 0.84 (LOF) e 0.79 (One-Class SVM) — Notebook 03
- Pipeline de 4.500 transações: 45ms (vs 320ms LOF, 890ms SVM)

**Monitoramento:**
- Log de latência por amostra no pipeline.log
- Alerta se latência média > 20ms
- Re-treino mensal com drift detection via PSI (Population Stability Index)

---

## 6. REFERÊNCIES & LINKS

- `notebooks/03_motor_compliance.ipynb` — Arena de modelos com benchmark
- `src/treinar_modelo.py` — Script de treino
- `src/pipeline_compliance.py` — Pipeline de inferência
- Liu, Ting, Zhou (2008). "Isolation Forest" — ICDM.
