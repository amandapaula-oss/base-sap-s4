import os
import streamlit as st
import pandas as pd
import gdown

st.set_page_config(page_title="Worker Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #f4f6fb;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 2rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}
.cockpit-header {
    background: #ffffff;
    border: 1px solid #dde3f0;
    border-left: 5px solid #2d50a0;
    border-radius: 10px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.cockpit-header h1 { color: #1a2e5a; font-size: 1.6rem; font-weight: 700; margin: 0; }
.cockpit-header p  { color: #6b7fa3; font-size: 0.85rem; margin: 0.2rem 0 0 0; }

.breadcrumb {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: #ffffff;
    border: 1px solid #dde3f0;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin-bottom: 1.2rem;
    flex-wrap: wrap;
}
.crumb-sep { color: #aab4cc; font-size: 0.9rem; }
.crumb-active { color: #2d50a0; font-weight: 700; font-size: 0.9rem; }
.crumb-inactive { color: #6b7fa3; font-size: 0.9rem; }

.kpi-card {
    background: #ffffff;
    border: 1px solid #dde3f0;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    text-align: center;
}
.kpi-label { color: #6b7fa3; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; }
.kpi-value { color: #1a2e5a; font-size: 1.35rem; font-weight: 700; }
.kpi-value.negative { color: #c0392b; }
.kpi-value.positive { color: #1a7a4a; }

.section-title {
    font-size: 1rem; font-weight: 600; color: #1a2e5a;
    margin: 1rem 0 0.6rem 0; padding-bottom: 0.3rem;
    border-bottom: 2px solid #2d50a0; display: inline-block;
}
.filter-box {
    background: #ffffff; border: 1px solid #dde3f0; border-radius: 10px;
    padding: 1rem 1.2rem 0.5rem 1.2rem; margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
[data-testid="stDataFrame"] {
    border-radius: 10px; overflow: hidden;
    border: 1px solid #dde3f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
</style>

<div class="cockpit-header">
    <h1>👷 Worker Dashboard</h1>
    <p>Receita, Custo e Margem por hierarquia de alocação</p>
</div>
""", unsafe_allow_html=True)

# ── Constantes ─────────────────────────────────────────────────────────────────

LEVELS = ['sap_code', 'client_name', 'project_id', 'worker_id']
LEVEL_LABELS = {
    'sap_code':    'Empresa',
    'client_name': 'Cliente',
    'project_id':  'Projeto',
    'worker_id':   'Worker',
}
SAP_NAMES = {'BR02': 'FCamara', 'BR07': 'Hyper', 'BR09': 'NextGen'}

# ── Dados ──────────────────────────────────────────────────────────────────────

@st.cache_data(persist="disk")
def carregar_nomes():
    if not os.path.exists("personaldata.xlsx"):
        gdown.download(id="1qXu1bjWKqL3tNMYUAFjoMSiSle417WPF", output="personaldata.xlsx", quiet=True)
    df = pd.read_excel("personaldata.xlsx", sheet_name="YY1_FCTEAM5_PERSONEW",
                       usecols=["ID Number", "Full Name"])
    df = df.dropna(subset=["ID Number"]).drop_duplicates("ID Number")
    return dict(zip(df["ID Number"], df["Full Name"]))

@st.cache_data(persist="disk")
def carregar_dados():
    if not os.path.exists("worker.xlsx"):
        gdown.download(id="1rqT1PVnd8kQq5VIDrWw1kXF21dwT3T5M", output="worker.xlsx", quiet=True)
    df = pd.read_excel("worker.xlsx", sheet_name="receita_worker")
    df['lucro_bruto'] = df['receita_liquida'] - df['cost']
    return df

# ── Session state ──────────────────────────────────────────────────────────────

if 'path' not in st.session_state:
    st.session_state.path = []

# ── Helpers ────────────────────────────────────────────────────────────────────

def aplicar_filtros(df, path):
    for item in path:
        df = df[df[item['level']] == item['value']]
    return df

def calcular_metricas(df, group_col):
    df = df.copy()
    agg_dict = dict(
        receita_bruta   = ('receita_bruta',   'sum'),
        receita_liquida = ('receita_liquida', 'sum'),
        custo           = ('cost',            'sum'),
        lucro_bruto     = ('lucro_bruto',     'sum'),
    )
    if group_col == 'worker_id':
        df['_gm_pond'] = df['gross_margin'] * df['receita_liquida']
        agg_dict['_gm_pond'] = ('_gm_pond', 'sum')


    g = df.groupby(group_col, as_index=False).agg(**agg_dict)
    safe_rl = g['receita_liquida'].replace(0, float('nan'))
    if group_col == 'worker_id':
        g['margem_bruta'] = g['_gm_pond'] / safe_rl
        g = g.drop(columns=['_gm_pond'])
    else:
        g['margem_bruta'] = g['lucro_bruto'] / safe_rl

    g = g.sort_values('receita_bruta', ascending=False).reset_index(drop=True)
    return g

def formatar_tabela(df, group_col):
    display = df.copy()
    if group_col == 'sap_code':
        display[group_col] = display[group_col].map(SAP_NAMES).fillna(display[group_col])

    if group_col == 'worker_id':
        display[group_col] = display[group_col].map(nomes).fillna(display[group_col])
        display.columns = [
            LEVEL_LABELS.get(group_col, group_col),
            'Receita Bruta', 'Receita Líquida', 'Custo', 'Lucro Bruto', 'Margem Bruta %',
        ]
        fmt = {
            'Receita Bruta':   'R$ {:,.0f}',
            'Receita Líquida': 'R$ {:,.0f}',
            'Custo':           'R$ {:,.0f}',
            'Lucro Bruto':     'R$ {:,.0f}',
            'Margem Bruta %':  '{:.1%}',
        }
        neg_cols = ['Lucro Bruto', 'Margem Bruta %']
    else:
        display.columns = [
            LEVEL_LABELS.get(group_col, group_col),
            'Receita Bruta', 'Receita Líquida', 'Custo', 'Lucro Bruto', 'Margem Bruta %',
        ]
        fmt = {
            'Receita Bruta':   'R$ {:,.0f}',
            'Receita Líquida': 'R$ {:,.0f}',
            'Custo':           'R$ {:,.0f}',
            'Lucro Bruto':     'R$ {:,.0f}',
            'Margem Bruta %':  '{:.1%}',
        }
        neg_cols = ['Lucro Bruto', 'Margem Bruta %']

    styled = display.style \
        .format(fmt) \
        .map(lambda v: 'color: #c0392b' if isinstance(v, (int, float)) and v < 0 else '',
             subset=neg_cols)
    return styled

def fmt_brl(v):
    return f"R$ {v:,.0f}"

def fmt_pct(v):
    return f"{v:.1%}" if v == v else "—"

# ── Carregar e filtrar ─────────────────────────────────────────────────────────

nomes = carregar_nomes()
df_all = carregar_dados()

# ── Filtro de competência ──────────────────────────────────────────────────────

st.markdown('<div class="filter-box">', unsafe_allow_html=True)
competencias = sorted(df_all['competencia'].dropna().unique())
comp_sel = st.multiselect("Competência", competencias, default=competencias, key="comp")
st.markdown('</div>', unsafe_allow_html=True)

df_all = df_all[df_all['competencia'].isin(comp_sel)] if comp_sel else df_all

# ── Aplicar drill-down ─────────────────────────────────────────────────────────

df_view = aplicar_filtros(df_all, st.session_state.path)
current_idx = len(st.session_state.path)
current_level = LEVELS[current_idx] if current_idx < len(LEVELS) else None

# ── Breadcrumb ─────────────────────────────────────────────────────────────────

crumb_html = '<div class="breadcrumb">'
crumbs = [('Início', -1)] + [
    (f"{LEVEL_LABELS[p['level']]}: {SAP_NAMES.get(p['value'], p['value'])}", i)
    for i, p in enumerate(st.session_state.path)
]
for i, (label, idx) in enumerate(crumbs):
    is_last = (i == len(crumbs) - 1)
    css = 'crumb-active' if is_last else 'crumb-inactive'
    crumb_html += f'<span class="{css}">{label}</span>'
    if not is_last:
        crumb_html += '<span class="crumb-sep">›</span>'
crumb_html += '</div>'
st.markdown(crumb_html, unsafe_allow_html=True)

# Botões de navegação retroativa
if st.session_state.path:
    cols_nav = st.columns(len(st.session_state.path) + 1)
    with cols_nav[0]:
        if st.button("⬅ Início"):
            st.session_state.path = []
            st.rerun()
    for i, item in enumerate(st.session_state.path[:-1]):
        with cols_nav[i + 1]:
            label = SAP_NAMES.get(item['value'], item['value'])
            if st.button(f"⬅ {label}"):
                st.session_state.path = st.session_state.path[:i + 1]
                st.rerun()

# ── KPI Cards ─────────────────────────────────────────────────────────────────

total_rb   = df_view['receita_bruta'].sum()
total_rl   = df_view['receita_liquida'].sum()
total_cost = df_view['cost'].sum()
total_lb   = df_view['lucro_bruto'].sum()
total_mg   = total_lb / total_rl if total_rl else 0

def kpi_card(label, value, fmt='brl'):
    val_str = fmt_brl(value) if fmt == 'brl' else fmt_pct(value)
    css = ''
    if isinstance(value, float) and value < 0:
        css = ' negative'
    elif fmt == 'pct' and isinstance(value, float) and value >= 0:
        css = ' positive'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value{css}">{val_str}</div>
    </div>"""

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Receita Bruta",  total_rb),   unsafe_allow_html=True)
c2.markdown(kpi_card("Custo",          total_cost), unsafe_allow_html=True)
c3.markdown(kpi_card("Lucro Bruto",    total_lb),   unsafe_allow_html=True)
c4.markdown(kpi_card("Margem Bruta",   total_mg, fmt='pct'), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Comparativo por Competência ───────────────────────────────────────────────

st.markdown('<p class="section-title">Comparativo por Competência</p>', unsafe_allow_html=True)

mensal = df_view.groupby('competencia', as_index=False).agg(
    receita_bruta   = ('receita_bruta',   'sum'),
    custo           = ('cost',            'sum'),
    receita_liquida = ('receita_liquida', 'sum'),
    lucro_bruto     = ('lucro_bruto',     'sum'),
)
mensal['margem_bruta'] = mensal['lucro_bruto'] / mensal['receita_liquida'].replace(0, float('nan'))
mensal = mensal.sort_values('competencia')

# Seletor de métrica para o gráfico
metrica_opts = {
    'Receita Bruta':   'receita_bruta',
    'Receita Líquida': 'receita_liquida',
    'Custo':           'custo',
    'Lucro Bruto':     'lucro_bruto',
    'Margem Bruta %':  'margem_bruta',
}
col_sel, _ = st.columns([2, 5])
with col_sel:
    metrica_label = st.selectbox("Métrica do gráfico", list(metrica_opts.keys()), key="metrica_comp")
metrica_col = metrica_opts[metrica_label]

# Gráfico de barras
chart_data = mensal.set_index('competencia')[[metrica_col]]
chart_data.index.name = 'Competência'
chart_data.columns = [metrica_label]
st.bar_chart(chart_data, color='#2d50a0')

# Tabela mensal formatada
tabela_mensal = mensal.copy()
tabela_mensal.columns = ['Competência', 'Receita Bruta', 'Receita Líquida', 'Custo', 'Lucro Bruto', 'Margem Bruta %']
st.dataframe(
    tabela_mensal.style
        .format({
            'Receita Bruta':   'R$ {:,.0f}',
            'Custo':           'R$ {:,.0f}',
            'Receita Líquida': 'R$ {:,.0f}',
            'Lucro Bruto':     'R$ {:,.0f}',
            'Margem Bruta %':  '{:.1%}',
        })
        .map(lambda v: 'color: #c0392b' if isinstance(v, (int, float)) and v < 0 else '',
             subset=['Lucro Bruto', 'Margem Bruta %']),
    width='stretch',
    hide_index=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabela do nível atual + drill-down ────────────────────────────────────────

if current_level:
    label_atual = LEVEL_LABELS[current_level]
    st.markdown(f'<p class="section-title">Visão por {label_atual}</p>', unsafe_allow_html=True)

    metrics = calcular_metricas(df_view, current_level)
    st.dataframe(formatar_tabela(metrics, current_level), width='stretch', hide_index=True)

    # Próximo nível disponível?
    if current_idx + 1 < len(LEVELS):
        next_label = LEVEL_LABELS[LEVELS[current_idx + 1]]
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<p class="section-title">Detalhar por {next_label}</p>', unsafe_allow_html=True)

        opcoes = sorted(df_view[current_level].dropna().unique())
        if current_level == 'worker_id':
            opcoes_display = [nomes.get(o, o) for o in opcoes]
        else:
            opcoes_display = [SAP_NAMES.get(o, o) for o in opcoes]
        opcao_map = dict(zip(opcoes_display, opcoes))

        col_sel, col_btn = st.columns([4, 1])
        with col_sel:
            escolha_display = st.selectbox(f"Selecione o {label_atual}", opcoes_display, label_visibility="collapsed")
        with col_btn:
            if st.button(f"Ver {next_label} ›", type="primary"):
                escolha_raw = opcao_map[escolha_display]
                st.session_state.path.append({'level': current_level, 'value': escolha_raw})
                st.rerun()
else:
    st.markdown('<p class="section-title">Nível mais detalhado</p>', unsafe_allow_html=True)
    st.info("Você está na visão por Worker — nível mais granular disponível.")
    detail = df_view[['worker_id', 'client_name', 'project_id', 'work_package_id',
                      'competencia', 'recorded_hours', 'receita_bruta',
                      'receita_liquida', 'cost', 'lucro_bruto']].copy()
    detail['worker_id'] = detail['worker_id'].map(nomes).fillna(detail['worker_id'])
    st.dataframe(
        detail
        .rename(columns={
            'worker_id':       'Worker',
            'client_name':     'Cliente',
            'project_id':      'Projeto',
            'work_package_id': 'Work Package',
            'competencia':     'Competência',
            'recorded_hours':  'Horas',
            'receita_bruta':   'Rec. Bruta',
            'receita_liquida': 'Rec. Líquida',
            'cost':            'Custo',
            'lucro_bruto':     'Lucro Bruto',
        })
        .style.format({
            'Rec. Bruta':   'R$ {:,.0f}',
            'Rec. Líquida': 'R$ {:,.0f}',
            'Custo':        'R$ {:,.0f}',
            'Lucro Bruto':  'R$ {:,.0f}',
            'Horas':        '{:,.1f}',
        }),
        width='stretch',
        hide_index=True,
    )
