import os
import streamlit as st
import pandas as pd
import gdown

st.set_page_config(page_title="Cockpit FP&A", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* ── Fundo e fonte global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #f4f6fb;
    font-family: 'Segoe UI', sans-serif;
}

/* ── Remove padding padrão do topo ── */
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 2rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}

/* ── Header customizado ── */
.cockpit-header {
    background: #ffffff;
    border: 1px solid #dde3f0;
    border-left: 5px solid #2d50a0;
    border-radius: 10px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.cockpit-header h1 {
    color: #1a2e5a;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.3px;
}
.cockpit-header p {
    color: #6b7fa3;
    font-size: 0.85rem;
    margin: 0.2rem 0 0 0;
}

/* ── Abas ── */
[data-testid="stTabs"] [role="tablist"] {
    gap: 0.3rem;
    border-bottom: 2px solid #dde3f0;
}
[data-testid="stTabs"] button[role="tab"] {
    background: #f4f6fb;
    border: 1px solid #dde3f0;
    border-radius: 8px 8px 0 0;
    color: #5a6a8a;
    font-weight: 500;
    font-size: 0.9rem;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: #ffffff;
    color: #2d50a0;
    border-color: #dde3f0;
    border-bottom: 2px solid #2d50a0;
    font-weight: 700;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    background: #eef2ff;
    color: #1a2e5a;
}

/* ── Subtítulos de seção ── */
.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #1a2e5a;
    margin: 1rem 0 0.6rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #2d50a0;
    display: inline-block;
}

/* ── Caixas de filtro ── */
[data-testid="stMultiSelect"] > div,
[data-testid="stSelectbox"] > div {
    border-radius: 8px;
    border: 1px solid #c8d3ea;
    background: #ffffff;
}
[data-testid="stMultiSelect"] label,
[data-testid="stSelectbox"] label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #3a4f7a;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #dde3f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* ── Divisor de filtros ── */
.filter-box {
    background: #ffffff;
    border: 1px solid #dde3f0;
    border-radius: 10px;
    padding: 1rem 1.2rem 0.5rem 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
</style>

<div class="cockpit-header">
    <div>
        <h1>📊 Cockpit FP&A</h1>
        <p>Visualização gerencial de resultados financeiros</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Data Loading ───────────────────────────────────────────────────────────────

COMPANY_NAMES = {
    "BR02": "FCamara",
    "BR07": "Hyper",
    "BR09": "NextGen",
    "BR05": "SGA",
    "BR06": "Dojo",
    "BR04": "Nação Digital",
}

@st.cache_data(persist="disk")
def carregar_sap():
    if not os.path.exists("dados_sap.xlsx"):
        url = "https://drive.google.com/uc?id=1Lm-G9ZJUC2Hzc9iIKIb6LCemYJqtzNQO"
        gdown.download(url, "dados_sap.xlsx", quiet=True)
    df = pd.read_excel("dados_sap.xlsx", usecols=[
        "CompanyCode", "agrupador_fpa", "FiscalPeriod",
        "AmountInCompanyCodeCurrency", "vertical", "ProfitCenter"
    ])
    df["CompanyCode"] = df["CompanyCode"].map(COMPANY_NAMES).fillna(df["CompanyCode"])
    return df

@st.cache_data(persist="disk")
def carregar_nexus():
    if not os.path.exists("nexus.xlsx"):
        gdown.download(
            id="1BBjfSYTGLAeuxMih4CDMgyfmVDGfkxkW",
            output="nexus.xlsx",
            quiet=True,
        )
    cols = [
        "[Tipo]", "[Empresa]", "[Competência]", "[Vertical]",
        "[Stream]", "[Agrupador FP&A - COA]", "[Valor]", "[Moeda]",
    ]
    df = pd.read_excel("nexus.xlsx", sheet_name="Nexus_Consolidado", usecols=cols)
    df["[Competência]"] = pd.to_datetime(df["[Competência]"])
    df["Período"] = df["[Competência]"].dt.to_period("M").astype(str)
    df["Ano"] = df["[Competência]"].dt.year
    return df

# ── P&L Engine ─────────────────────────────────────────────────────────────────

COSTS_ITEMS = [
    "Payroll costs",
    "Third-party costs",
    "Licenses and infrastructure costs",
    "Other costs",
]

SGA_ITEMS = [
    "Payroll expenses",
    "Third-party expenses",
    "Commission expenses",
    "Marketing and selling expenses",
    "General and administrative expenses",
    "Consulting expenses",
    "Occupancy expenses",
    "Travel expenses",
    "Tax expenses",
    "Other operating income (expenses) net",
]

SUBTOTALS = {
    "Net revenue", "Total costs", "Gross profit", "Gross margin %",
    "Total SG&A", "EBITDA", "EBITDA %",
}
PCT_ROWS = {"Gross margin %", "EBITDA %"}

PL_ORDER = [
    "Gross revenue", "Deductions and taxes", "Net revenue",
    "Payroll costs", "Third-party costs", "Licenses & infra costs", "Other costs", "Total costs",
    "Gross profit", "Gross margin %",
    "Payroll expenses", "Third-party expenses", "Commission expenses",
    "Marketing & selling exp.", "G&A expenses", "Consulting expenses",
    "Occupancy expenses", "Travel expenses", "Tax expenses", "Other operating net",
    "Total SG&A", "EBITDA", "EBITDA %",
]

LABEL_MAP = {
    "Licenses & infra costs":  "Licenses and infrastructure costs",
    "Marketing & selling exp.": "Marketing and selling expenses",
    "G&A expenses":             "General and administrative expenses",
    "Other operating net":      "Other operating income (expenses) net",
}

def compute_pl(df, col_group):
    piv = df.pivot_table(
        index="[Agrupador FP&A - COA]", columns=col_group,
        values="[Valor]", aggfunc="sum", fill_value=0,
    )
    cols = list(piv.columns)

    def g(display_label):
        raw = LABEL_MAP.get(display_label, display_label)
        return piv.loc[raw].copy() if raw in piv.index else pd.Series(0.0, index=cols)

    gross   = g("Gross revenue")
    deduct  = g("Deductions and taxes")
    net_rev = gross + deduct
    costs   = sum(g(c) for c in COSTS_ITEMS)
    gp      = net_rev + costs
    sga     = sum(g(s) for s in SGA_ITEMS)
    ebitda  = gp + sga
    safe    = net_rev.replace(0, float("nan"))

    data = {
        "Gross revenue":        gross,
        "Deductions and taxes": deduct,
        "Net revenue":          net_rev,
        "Payroll costs":        g("Payroll costs"),
        "Third-party costs":    g("Third-party costs"),
        "Licenses & infra costs": g("Licenses & infra costs"),
        "Other costs":          g("Other costs"),
        "Total costs":          costs,
        "Gross profit":         gp,
        "Gross margin %":       (gp / safe).fillna(0),
        "Payroll expenses":     g("Payroll expenses"),
        "Third-party expenses": g("Third-party expenses"),
        "Commission expenses":  g("Commission expenses"),
        "Marketing & selling exp.": g("Marketing & selling exp."),
        "G&A expenses":         g("G&A expenses"),
        "Consulting expenses":  g("Consulting expenses"),
        "Occupancy expenses":   g("Occupancy expenses"),
        "Travel expenses":      g("Travel expenses"),
        "Tax expenses":         g("Tax expenses"),
        "Other operating net":  g("Other operating net"),
        "Total SG&A":           sga,
        "EBITDA":               ebitda,
        "EBITDA %":             (ebitda / safe).fillna(0),
    }

    result = pd.DataFrame(data).T
    result.columns = cols
    result = result.loc[PL_ORDER]
    result["Total"] = result.sum(axis=1)

    nr_t = result.loc["Net revenue", "Total"]
    result.loc["Gross margin %", "Total"] = (
        result.loc["Gross profit", "Total"] / nr_t if nr_t else 0
    )
    result.loc["EBITDA %", "Total"] = (
        result.loc["EBITDA", "Total"] / nr_t if nr_t else 0
    )
    return result


def style_pl(df):
    def highlight(s):
        return [
            "font-weight:bold; background-color:#dce6f7; color:#1a2e5a" if s.name in SUBTOTALS else ""
            for _ in s
        ]

    styled = df.style.apply(highlight, axis=1)
    num_rows = [r for r in df.index if r not in PCT_ROWS]
    pct_rows = [r for r in df.index if r in PCT_ROWS]
    if num_rows:
        styled = styled.format("{:,.0f}", subset=pd.IndexSlice[num_rows, :])
    if pct_rows:
        styled = styled.format("{:.1%}", subset=pd.IndexSlice[pct_rows, :])
    return styled


# ── Tabs ───────────────────────────────────────────────────────────────────────

tab_sap, tab_dre, tab_streams, tab_matricial = st.tabs([
    "📋 Base SAP S4",
    "🏢 DRE por Empresa",
    "🌊 P&L por Stream",
    "📐 P&L Matricial",
])

# ── Tab 1: SAP S4 ──────────────────────────────────────────────────────────────

with tab_sap:
    st.markdown('<p class="section-title">Base SAP S4 — Soma por Agrupador FP&A x Mês</p>', unsafe_allow_html=True)
    df_sap = carregar_sap()

    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    companies = sorted(df_sap["CompanyCode"].dropna().unique())
    selecionadas = st.multiselect("Empresa", companies, default=companies, key="sap_co")
    df_f = df_sap[df_sap["CompanyCode"].isin(selecionadas)]
    c1, c2 = st.columns(2)
    with c1:
        vert_sel = st.multiselect("Vertical (opcional)",
                                  sorted(df_f["vertical"].dropna().unique()), key="sap_v")
        if vert_sel:
            df_f = df_f[df_f["vertical"].isin(vert_sel)]
    with c2:
        pc_sel = st.multiselect("Profit Center (opcional)",
                                sorted(df_f["ProfitCenter"].dropna().unique()), key="sap_pc")
        if pc_sel:
            df_f = df_f[df_f["ProfitCenter"].isin(pc_sel)]
    st.markdown('</div>', unsafe_allow_html=True)

    pivot = df_f.pivot_table(
        index="agrupador_fpa", columns="FiscalPeriod",
        values="AmountInCompanyCodeCurrency", aggfunc="sum", fill_value=0,
    )
    pivot.columns = [f"Mês {int(c)}" for c in pivot.columns]
    pivot["Total"] = pivot.sum(axis=1)
    st.dataframe(pivot.style.format("{:,.2f}"), width='stretch')

# ── Tab 2: DRE por Empresa ─────────────────────────────────────────────────────

with tab_dre:
    st.markdown('<p class="section-title">DRE por Empresa — Resultado x Período</p>', unsafe_allow_html=True)
    df_nx = carregar_nexus()

    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        anos = sorted(df_nx["Ano"].unique())
        ano_dre = st.multiselect("Ano", anos, default=anos, key="dre_ano")
    with c2:
        tipo_dre = st.selectbox("Tipo", ["Actual", "Budget"], key="dre_tipo")
    with c3:
        empresas = sorted(df_nx["[Empresa]"].dropna().unique())
        emp_dre = st.multiselect("Empresa", empresas, default=empresas, key="dre_emp")
    st.markdown('</div>', unsafe_allow_html=True)

    df_dre = df_nx[
        df_nx["Ano"].isin(ano_dre) &
        (df_nx["[Tipo]"] == tipo_dre) &
        df_nx["[Empresa]"].isin(emp_dre) &
        (df_nx["[Moeda]"] == "BRL")
    ]

    if df_dre.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        result_dre = compute_pl(df_dre, "Período")
        st.dataframe(style_pl(result_dre), width='stretch')

# ── Tab 3: P&L por Stream ──────────────────────────────────────────────────────

with tab_streams:
    st.markdown('<p class="section-title">P&L por Stream — Resultado x Stream</p>', unsafe_allow_html=True)
    df_nx3 = carregar_nexus()

    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ano_str = st.multiselect("Ano", sorted(df_nx3["Ano"].unique()),
                                 default=sorted(df_nx3["Ano"].unique()), key="str_ano")
    with c2:
        tipo_str = st.selectbox("Tipo", ["Actual", "Budget"], key="str_tipo")
    with c3:
        emp_str = st.multiselect("Empresa",
                                 sorted(df_nx3["[Empresa]"].dropna().unique()),
                                 default=sorted(df_nx3["[Empresa]"].dropna().unique()),
                                 key="str_emp")
    with c4:
        stream_str = st.multiselect("Stream",
                                    sorted(df_nx3["[Stream]"].dropna().unique()),
                                    default=sorted(df_nx3["[Stream]"].dropna().unique()),
                                    key="str_stream")
    st.markdown('</div>', unsafe_allow_html=True)

    df_str = df_nx3[
        df_nx3["Ano"].isin(ano_str) &
        (df_nx3["[Tipo]"] == tipo_str) &
        df_nx3["[Empresa]"].isin(emp_str) &
        df_nx3["[Stream]"].isin(stream_str) &
        (df_nx3["[Moeda]"] == "BRL")
    ]

    if df_str.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        result_str = compute_pl(df_str, "[Stream]")
        st.dataframe(style_pl(result_str), width='stretch')

# ── Tab 4: P&L Matricial ───────────────────────────────────────────────────────

with tab_matricial:
    st.markdown('<p class="section-title">P&L Matricial — KPIs por Empresa</p>', unsafe_allow_html=True)
    df_nx4 = carregar_nexus()

    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        ano_mat = st.multiselect("Ano", sorted(df_nx4["Ano"].unique()),
                                 default=sorted(df_nx4["Ano"].unique()), key="mat_ano")
    with c2:
        tipo_mat = st.selectbox("Tipo", ["Actual", "Budget"], key="mat_tipo")
    st.markdown('</div>', unsafe_allow_html=True)

    df_mat = df_nx4[
        df_nx4["Ano"].isin(ano_mat) &
        (df_nx4["[Tipo]"] == tipo_mat) &
        (df_nx4["[Moeda]"] == "BRL")
    ]

    if df_mat.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        result_mat = compute_pl(df_mat, "[Empresa]")

        kpi_rows = ["Net revenue", "Gross profit", "Gross margin %",
                    "Total SG&A", "EBITDA", "EBITDA %"]
        mat = result_mat.loc[[r for r in kpi_rows if r in result_mat.index]].T

        def highlight_total(s):
            return [
                "font-weight:bold; background-color:#dce6f7; color:#1a2e5a" if s.name == "Total" else ""
                for _ in s
            ]

        styled_mat = mat.style.apply(highlight_total, axis=1)
        num_cols = [c for c in mat.columns if c not in PCT_ROWS]
        pct_cols = [c for c in mat.columns if c in PCT_ROWS]
        if num_cols:
            styled_mat = styled_mat.format("{:,.0f}", subset=pd.IndexSlice[:, num_cols])
        if pct_cols:
            styled_mat = styled_mat.format("{:.1%}", subset=pd.IndexSlice[:, pct_cols])

        st.dataframe(styled_mat, width='stretch')
