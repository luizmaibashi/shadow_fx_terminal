# -*- coding: utf-8 -*-
"""
app.py - Shadow FX Terminal Dashboard
=======================================
Streamlit Dashboard premium para monitoramento do Índice de Risco Fiscal
e alertas do Motor de Compliance AML.

Execute: streamlit run app.py
"""

import sys
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils import DATA_PROC, PROJECT_ROOT as PROJ_ROOT
from pipeline_compliance import gerar_explicacao_xai
from agente_rag import preparar_prompt_llm, gerar_rascunho_coaf

# ── Configuração da página ────────────────────────────────────────────

st.set_page_config(
    page_title="Shadow FX Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Premium ───────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp { background-color: #0a0a0f; }

/* Header */
.main-header {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a0a2e 50%, #0d1f3c 100%);
    border: 1px solid #1e1e3a;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
}
.main-header h1 {
    font-size: 2.4rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00ffcc, #7c3aed, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0; padding: 0;
}
.main-header p { color: #cbd5e1; font-size: 1.0rem; margin: 8px 0 0 0; font-weight: 400; }

/* KPI cards */
.kpi-card {
    background: linear-gradient(135deg, #0f0f1a, #1a1a2e);
    border: 1px solid #1e1e3a;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}
.kpi-card:hover { transform: translateY(-3px); border-color: #3b82f6; }
.kpi-title  { color: #94a3b8; font-size: 0.85rem; font-weight: 600;
               text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px; }
.kpi-value  { font-size: 2.6rem; font-weight: 900; line-height: 1; letter-spacing: -1px; }
.kpi-sub    { color: #94a3b8; font-size: 0.85rem; margin-top: 8px; font-weight: 400; }

/* Alert badges */
.badge-verde    { background:#00ffcc22; color:#00ffcc; border:1px solid #00ffcc44;
                  padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600; }
.badge-amarelo  { background:#ffaa0022; color:#ffaa00; border:1px solid #ffaa0044;
                  padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600; }
.badge-vermelho { background:#ff336622; color:#ff3366; border:1px solid #ff336644;
                  padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600; }

/* Section titles */
.section-title {
    color: #e2e8f0; font-size: 1.1rem; font-weight: 700;
    border-left: 3px solid #7c3aed; padding-left: 12px;
    margin: 24px 0 16px 0;
}

/* Sidebar */
section[data-testid="stSidebar"] { background-color: #0d0d1a; border-right: 1px solid #1e1e3a; }

/* Customizing st.info and st.success boxes for readability */
.stAlert {
    background-color: #11111d !important;
    border: 1px solid #1e1e3a !important;
    color: #f8fafc !important;
}
.stAlert p { font-size: 0.95rem !important; color: #f8fafc !important; }

/* Improve table readability */
[data-testid="stTable"] td, [data-testid="stTable"] th {
    color: #e2e8f0 !important;
    font-size: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)


# ── Carregamento de dados com cache ───────────────────────────────────

@st.cache_data(ttl=300)
def carregar_irf():
    path = DATA_PROC / "dataset_irf_completo.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    # Suporte a v1 e v2
    if "irf_v2" in df.columns and "irf" not in df.columns:
        df["irf"] = df["irf_v2"]
    return df


@st.cache_data(ttl=300)
def carregar_compliance():
    path = DATA_PROC / "resultado_compliance.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["timestamp"])


@st.cache_data(ttl=300)
def carregar_copom():
    path = PROJ_ROOT / "data" / "raw" / "atas_copom_index.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["data"])


# ── Sidebar ───────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📊 Shadow FX Terminal")
    st.markdown("**Motor de Compliance AML**")
    st.markdown("---")

    pagina = st.radio(
        "Navegar",
        ["🏠 Dashboard", "⚖️ Compliance Scanner", "📈 Análise IRF", "ℹ️ Sobre o Projeto"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Stack**")
    st.caption("Python · Scikit-Learn · FastAPI · Streamlit")
    st.markdown("**Referência**")
    st.caption("Resoluções BCB 519-521/2026")
    st.caption("Britto, P.J. (2026) — OTC Research")

    st.markdown("---")
    with st.expander("📖 Como navegar neste demo"):
        st.markdown("""
**🏠 Dashboard** — visão geral: IRF do dia, quantas transações caíram em cada alerta (VERDE/AMARELO/VERMELHO) e o histórico do índice.

**⚖️ Compliance Scanner** — simulador: preenche os dados de uma transação e vê o score gerado na hora, com explicação e rascunho de RAS.

**📈 Análise IRF** — decompõe o índice nos 3 sinais que o formam (câmbio, USDT, atas do Copom).

**ℹ️ Sobre o Projeto** — a origem, o pivô e as limitações honestas, em texto corrido.

⚠️ Este demo público roda só o dashboard, isolado (sem a API FastAPI, sem a Camada 3/LLM ativa). Transações são simuladas; o contexto macroeconômico é dado real.
        """)


# ── Dados ─────────────────────────────────────────────────────────────

df_irf = carregar_irf()
df_comp = carregar_compliance()
df_copom = carregar_copom()

CORES = {
    "verde":    "#00ffcc",
    "amarelo":  "#ffaa00",
    "vermelho": "#ff4d88", # Um pouco mais vibrante
    "roxo":     "#8b5cf6", # Mais claro (Violet-500)
    "azul":     "#60a5fa", # Mais claro (Blue-400)
    "fundo":    "#0a0a0f",
    "card":     "#11111d",
    "texto":    "#f8fafc", # Quase branco
    "sub":      "#94a3b8", # Slate-400 (mais legível que 8892b0)
}

plt.rcParams.update({
    "figure.facecolor": CORES["fundo"],
    "axes.facecolor":   "#0f0f1a",
    "text.color":       CORES["texto"],
    "axes.labelcolor":  CORES["texto"],
    "xtick.color":      CORES["sub"],
    "ytick.color":      CORES["sub"],
    "axes.edgecolor":   "#1e1e3a",
    "grid.color":       "#1e1e3a",
    "grid.alpha":       0.5,
})


# ════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — DASHBOARD PRINCIPAL
# ════════════════════════════════════════════════════════════════════════

if "Dashboard" in pagina:
    st.markdown("""
    <div class="main-header">
        <h1>📊 Shadow FX Terminal</h1>
        <p>Motor de Monitoramento de Risco Fiscal e Compliance para Stablecoins no Brasil &nbsp;·&nbsp;
           Baseado nas Resoluções BCB nº 519, 520 e 521 (2026)</p>
    </div>
    """, unsafe_allow_html=True)

    if df_irf is None or df_comp is None:
        st.error("⚠️ Dados não encontrados. Execute o pipeline completo antes de abrir o dashboard.")
        st.code("python src/coletar_dados.py\npython src/gerar_dados_mock.py\npython src/scraper_copom.py\npython src/gerador_transacoes_mock.py\npython src/pipeline_compliance.py")
        st.stop()

    st.info(
        "**Como ler esta página:** o IRF (primeiro card) resume o risco fiscal do dia — "
        "quanto mais alto, mais \"esperado\" é que brasileiros comprem USDT como proteção. "
        "As transações simuladas foram classificadas em 3 baldes pelo motor de compliance: "
        "🟢 VERDE (normal), 🟡 AMARELO (monitorar) e 🔴 VERMELHO (ação imediata, tabela abaixo). "
        "No gráfico, áreas vermelhas marcam dias de risco alto (IRF ≥ 70)."
    )

    # ── KPIs ──────────────────────────────────────────────────────────
    irf_atual = df_irf["irf"].iloc[-1]
    data_atual = df_irf.index[-1].strftime("%d/%m/%Y")

    contagem = df_comp["alerta_final"].value_counts()
    n_verde    = int(contagem.get("VERDE", 0))
    n_amarelo  = int(contagem.get("AMARELO", 0))
    n_vermelho = int(contagem.get("VERMELHO", 0))
    total_tx   = len(df_comp)

    cor_irf = CORES["vermelho"] if irf_atual >= 70 else (CORES["amarelo"] if irf_atual >= 40 else CORES["verde"])
    label_irf = "ALTO" if irf_atual >= 70 else ("MODERADO" if irf_atual >= 40 else "BAIXO")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">IRF Atual ({data_atual})</div>
            <div class="kpi-value" style="color:{cor_irf}">{irf_atual:.1f}</div>
            <div class="kpi-sub">Risco <b style="color:{cor_irf}">{label_irf}</b></div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Transações Analisadas</div>
            <div class="kpi-value" style="color:{CORES['azul']}">{total_tx:,}</div>
            <div class="kpi-sub">Período: Jan/24–Jun/25</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">🟢 VERDE</div>
            <div class="kpi-value" style="color:{CORES['verde']}">{n_verde:,}</div>
            <div class="kpi-sub">{n_verde/total_tx*100:.1f}% do total</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">🟡 AMARELO</div>
            <div class="kpi-value" style="color:{CORES['amarelo']}">{n_amarelo:,}</div>
            <div class="kpi-sub">Monitorar</div>
        </div>""", unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">🔴 VERMELHO</div>
            <div class="kpi-value" style="color:{CORES['vermelho']}">{n_vermelho:,}</div>
            <div class="kpi-sub">Ação Imediata</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráfico: IRF Histórico ────────────────────────────────────────
    st.markdown('<div class="section-title">📈 Índice de Risco Fiscal — Histórico Completo</div>', unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(14, 4))
    x = df_irf.index
    y = df_irf["irf"]

    ax.fill_between(x, y, where=(y >= 70), alpha=0.3, color=CORES["vermelho"], label="Alto Risco (≥70)")
    ax.fill_between(x, y, where=((y >= 40) & (y < 70)), alpha=0.2, color=CORES["amarelo"])
    ax.fill_between(x, y, where=(y < 40), alpha=0.2, color=CORES["verde"])
    ax.plot(x, y, color=CORES["roxo"], linewidth=1.5, alpha=0.9)
    ax.axhline(70, color=CORES["vermelho"], linestyle="--", linewidth=0.8, alpha=0.6)
    ax.axhline(40, color=CORES["amarelo"], linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_ylabel("IRF (0–100)", fontsize=9)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8, facecolor=CORES["card"])
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Tabela de alertas VERMELHO ────────────────────────────────────
    st.markdown('<div class="section-title">🔴 Casos VERMELHO — Ação Imediata</div>', unsafe_allow_html=True)

    df_verm = df_comp[df_comp["alerta_final"] == "VERMELHO"].sort_values("score_final", ascending=False)
    cols_show = [c for c in ["user_id", "tipo_usuario", "valor_brl", "hora",
                              "wallets_unicas", "c1_razoes", "score_final"] if c in df_verm.columns]
    st.dataframe(
        df_verm[cols_show].head(15).style.background_gradient(subset=["score_final"], cmap="Reds"),
        use_container_width=True,
    )


# ════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — COMPLIANCE SCANNER
# ════════════════════════════════════════════════════════════════════════

elif "Compliance Scanner" in pagina:
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ Compliance Scanner</h1>
        <p>Pontue uma transação individualmente pelo pipeline de 3 camadas.</p>
    </div>
    """, unsafe_allow_html=True)

    irf_hoje = float(df_irf["irf"].iloc[-1]) if df_irf is not None else 50.0

    st.info(
        "**Como usar:** preencha os campos como se fosse uma transação real e clique em "
        "Analisar. O score (0-100) combina valor, horário, número de wallets e o IRF do dia — "
        "quanto maior, mais suspeita. Depois do resultado, o motor explica em texto (XAI) por "
        "que decidiu aquilo e, se o alerta for AMARELO ou VERMELHO, gera um rascunho de "
        "relatório pro COAF. **Nota de transparência:** o score aqui é uma versão simplificada "
        "e determinística, calculada na hora, sem depender de servidor — o motor completo "
        "(Isolation Forest treinado) roda no pipeline batch, não neste formulário."
    )

    with st.form("form_transacao"):
        st.markdown("**Dados da Transação**")
        col1, col2, col3 = st.columns(3)
        with col1:
            user_id     = st.text_input("User ID", value="USR_TEST_001")
            valor_brl   = st.number_input("Valor (R$)", min_value=0.0, value=9500.0, step=100.0)
            hora        = st.slider("Hora da transação", 0, 23, 3)
        with col2:
            wallets     = st.number_input("Nº Carteiras de Destino (Dia)", min_value=1, value=12)
            n_tx_dia    = st.number_input("Nº transações hoje", min_value=1, value=8)
            entropia    = st.slider("Entropia de Wallets (Smurfing Score)", 0.0, 5.0, 3.8)
        with col3:
            irf_ctx     = st.slider("IRF v2 do dia (contexto macro)", 0.0, 100.0, irf_hoje)
            c1_flag     = st.selectbox("Flag BCB ativa?", [0, 1], format_func=lambda x: "Sim" if x else "Não")

        submitted = st.form_submit_button("🔍 Analisar Transação", use_container_width=True)

    if submitted:
        # Regras BCB (Camada 1)
        razoes_c1 = []
        if valor_brl >= 10000:
            razoes_c1.append("R1: Valor ≥ R$10k")
        if 8500 <= valor_brl < 10000:
            razoes_c1.append("R4: Fracionamento suspeito")
        if hora <= 5 and valor_brl > 5000:
            razoes_c1.append("R5: Madrugada + valor alto")
        if wallets > 5:
            razoes_c1.append("R3: Muitas wallets no dia")
        c1_flag_calc = 1 if razoes_c1 else 0

        # Score final simplificado (sem modelo para não depender do servidor)
        score_base = 0.0
        score_base += min(valor_brl / 10000, 1.0) * 30
        score_base += (hora <= 5) * 20
        score_base += min(wallets / 20, 1.0) * 20
        score_base += (irf_ctx / 100) * 15
        score_base += c1_flag_calc * 15
        score_final = round(min(score_base, 100), 1)

        alerta = "VERMELHO" if score_final >= 70 else ("AMARELO" if score_final >= 40 else "VERDE")
        cor_alerta = CORES[alerta.lower()]

        st.markdown("---")
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            st.markdown(f"""
            <div class="kpi-card" style="border-color:{cor_alerta}">
                <div class="kpi-title">Score de Compliance</div>
                <div class="kpi-value" style="color:{cor_alerta}">{score_final}</div>
                <div class="kpi-sub">Alerta: <b style="color:{cor_alerta}">{alerta}</b></div>
            </div>""", unsafe_allow_html=True)

        with col_r2:
            st.markdown("**Flags da Camada 1 (Regras BCB):**")
            if razoes_c1:
                for r in razoes_c1:
                    st.error(f"🚨 {r}")
            else:
                st.success("✅ Sem flags da Camada 1")

            st.markdown(f"**IRF do dia:** `{irf_ctx:.1f}/100` — {'⚠️ Contexto de alto risco fiscal' if irf_ctx > 70 else '✅ Contexto macroeconômico normal'}")

        # PM Improvement: Explainability
        row_dict = {
            "alerta_final": alerta,
            "c1_razoes": ", ".join(razoes_c1) if razoes_c1 else "nenhuma",
            "c2_score_anomalia": score_base,
            "irf_contexto": irf_ctx,
            "wallets_unicas": wallets,
            "user_id": user_id,
            "valor_brl": valor_brl,
            "n_transacoes_dia": n_tx_dia,
            "entropia_wallets": entropia,
        }
        transacao_series = pd.Series(row_dict)
        explicacao = gerar_explicacao_xai(transacao_series)
        
        st.markdown("---")
        st.markdown('<div class="section-title">🧠 Explainable AI (XAI) — Justificativa do Motor</div>', unsafe_allow_html=True)
        st.info(f"**Análise MLOps:** {explicacao}")

        # PM Improvement: Actionability (Rascunho COAF)
        if alerta in ["AMARELO", "VERMELHO"]:
            st.markdown("---")
            st.markdown('<div class="section-title">📄 Ação Recomendada</div>', unsafe_allow_html=True)
            with st.expander("Gerar Rascunho de Relatório COAF (RAS)"):
                rascunho_coaf = gerar_rascunho_coaf(
                    user_id=user_id, valor_brl=valor_brl, wallets_unicas=wallets,
                    hora=hora, alerta=alerta, explicacao_xai=explicacao,
                    irf_contexto=irf_ctx, score=score_final,
                )
                st.text_area("Rascunho Pronto para Cópia:", value=rascunho_coaf, height=300)
                st.button("📥 Exportar para PDF (Em breve)", disabled=True)

            if alerta == "AMARELO":
                with st.expander("🤖 Prompt para Agente RAG (Camada 3)"):
                    prompt = preparar_prompt_llm(transacao_series)
                    st.code(prompt, language="text")
# ════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — ANÁLISE IRF
# ════════════════════════════════════════════════════════════════════════

elif "Análise IRF" in pagina:
    st.markdown("""
    <div class="main-header">
        <h1>📈 Análise do Índice de Risco Fiscal</h1>
        <p>Série histórica e decomposição dos 3 sinais: Câmbio · USDT · Copom</p>
    </div>""", unsafe_allow_html=True)

    if df_irf is None:
        st.error("Dados do IRF não encontrados.")
        st.stop()

    st.info(
        "**Como ler:** o IRF composto (gráfico do topo) é a soma ponderada dos 3 sinais abaixo — "
        "câmbio (40%), volume de USDT (35%) e tom das atas do Copom (25%). Use o seletor de ano "
        "pra focar num período; a tabela ao final resume o IRF médio por semestre, útil pra "
        "comparar momentos de estresse cambial (ex: 2024-S2, quando o Real bateu R$ 6,30)."
    )

    # Filtro de período
    anos = sorted(df_irf.index.year.unique())
    ano_sel = st.select_slider("Selecionar Ano", options=anos, value=(anos[0], anos[-1]))
    df_fil = df_irf[(df_irf.index.year >= ano_sel[0]) & (df_irf.index.year <= ano_sel[1])]

    col1, col2, col3 = st.columns(3)
    col1.metric("IRF Médio", f"{df_fil['irf'].mean():.1f}")
    col2.metric("IRF Máximo", f"{df_fil['irf'].max():.1f}")
    col3.metric("Dias em Alto Risco (≥70)", f"{(df_fil['irf'] >= 70).sum()}")

    # Gráfico de decomposição dos sinais
    if all(c in df_fil.columns for c in ["sinal_cambio", "sinal_usdt", "sinal_copom"]):
        fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
        fig.suptitle("Decomposição do IRF — Contribuição de Cada Sinal", fontsize=13, y=0.98)

        axes[0].plot(df_fil.index, df_fil["irf"], color=CORES["roxo"], linewidth=1.5)
        axes[0].fill_between(df_fil.index, df_fil["irf"], alpha=0.2, color=CORES["roxo"])
        axes[0].set_ylabel("IRF (0–100)")
        axes[0].set_title("IRF Composto", fontsize=10, loc="left")

        for ax, col, cor, titulo in zip(
            axes[1:],
            ["sinal_cambio", "sinal_usdt", "sinal_copom"],
            [CORES["amarelo"], CORES["verde"], CORES["azul"]],
            ["Sinal Câmbio (peso 40%)", "Sinal USDT (peso 35%)", "Sinal Copom (peso 25%)"]
        ):
            ax.plot(df_fil.index, df_fil[col], color=cor, linewidth=1.2)
            ax.fill_between(df_fil.index, df_fil[col], alpha=0.15, color=cor)
            ax.set_ylabel("Sinal (0–1)")
            ax.set_title(titulo, fontsize=10, loc="left")
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        # Só o IRF
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.plot(df_fil.index, df_fil["irf"], color=CORES["roxo"], linewidth=1.5)
        ax.fill_between(df_fil.index, df_fil["irf"], alpha=0.2, color=CORES["roxo"])
        ax.set_ylabel("IRF (0–100)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Tabela por semestre
    st.markdown('<div class="section-title">IRF Médio por Semestre</div>', unsafe_allow_html=True)
    df_fil2 = df_fil.copy()
    df_fil2["semestre"] = df_fil2.index.map(
        lambda d: f"{d.year}-S{'1' if d.month <= 6 else '2'}"
    )
    resumo = df_fil2.groupby("semestre")["irf"].agg(["mean", "max", "min"]).round(1)
    resumo.columns = ["IRF Médio", "IRF Máximo", "IRF Mínimo"]
    st.dataframe(resumo.style.background_gradient(subset=["IRF Médio"], cmap="RdYlGn_r"),
                 use_container_width=True)


# ════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — SOBRE O PROJETO
# ════════════════════════════════════════════════════════════════════════

elif "Sobre" in pagina:
    st.markdown("""
    <div class="main-header">
        <h1>ℹ️ Sobre o Shadow FX Terminal</h1>
        <p>Da análise do paper à solução de compliance — a história do projeto</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    ## 💡 A Origem
    Tudo começou com um paper: *"Dolarização Informal: Stablecoins como resposta à
    instabilidade monetária brasileira"* (Paulo J. Britto, OTC Research, 2026).

    **Objetivo inicial:** provar quantitativamente que o brasileiro compra USDT não para especular,
    mas como proteção estrutural contra a desvalorização do Real.

    ## ⚠️ O Ponto de Virada
    Enquanto construíamos a validação estatística (Correlação de Spearman, r=0.823 em 2024-S2),
    identificamos o cenário criado pelas **Resoluções BCB 519-521/2026** que enquadraram stablecoins
    como câmbio. O problema: sistemas de compliance tradicionais iriam bloquear o cidadão legítimo
    e deixar o criminoso inteligente passar.

    ## 🎯 A Solução
    Injetamos o **Índice de Risco Fiscal** (construído para validar o paper) como feature de contexto
    macroeconômico dentro de um Isolation Forest. Resultado: um pipeline inteligente que distingue
    o **Poupador Assustado** do **Fracionador (smurfing)**.

    ## 🏗️ Arquitetura
    | Fase | Entregável | Status |
    |:---|:---|:---:|
    | 1 | Correlação Spearman — prova da tese | ✅ |
    | 2 | Índice de Risco Fiscal (IRF 0-100) | ✅ |
    | 3 | Motor de Compliance AML — 3 camadas | ✅ |
    | 4 | FastAPI + Streamlit + Testes | ✅ |
    | 5 | Agente RAG (LLM lendo Atas do Copom) | ✅ |

    ## ⚖️ Limitações honestas
    - As transações processadas são **simuladas** — nenhuma validação usa dado real de cliente
      (o contexto macroeconômico que alimenta o IRF, esse sim, é 100% real).
    - O IRF melhora precisão e recall do motor, mas também **aumenta o falso positivo** no
      poupador legítimo — entre 2,3x e 3,5x, oscilando conforme a rodada de correção de bug.
      Não é uma solução sem custo, é um trade-off medido e aceito conscientemente.
    - Este demo público roda isolado: sem a API FastAPI (o dashboard chama a lógica de
      compliance direto, sem servidor) e sem a Camada 3 (LLM-as-judge) ativa.

    ## 🔗 Referências
    - Britto, P.J. (2026). *Dolarização Informal: Stablecoins como resposta à instabilidade monetária brasileira*. OTC Research.
    - Banco Central do Brasil. Resoluções BCB nº 519, 520 e 521 (2026).
    - Stanford CS230 — *Cascaded Heuristic Filters & LLM-as-judge patterns*.
    - Liu, F.T. et al. (2008). *Isolation Forest*. IEEE ICDM.

    Metodologia completa, ADRs e teste de falsificação da tese: [repositório no GitHub](https://github.com/luizmaibashi/shadow_fx_terminal).
    """)
