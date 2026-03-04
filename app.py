import streamlit as st
import pandas as pd
import gdown

st.set_page_config(page_title="Base SAP S4", layout="wide")
st.title("📊 Base SAP S4 - Prévia")

@st.cache_data
def carregar_dados():
    url = "https://drive.google.com/uc?id=1Lm-G9ZJUC2Hzc9iIKIb6LCemYJqtzNQO"
    gdown.download(url, "dados.xlsx", quiet=True)
    colunas = ["CompanyCode", "agrupador_fpa", "FiscalPeriod", "AmountInCompanyCodeCurrency", "vertical", "ProfitCenter"]
    return pd.read_excel("dados.xlsx", usecols=colunas)

df = carregar_dados()

# Filtro 1 - CompanyCode (obrigatório)
companies = sorted(df["CompanyCode"].dropna().unique())
selecionadas = st.multiselect("🏢 Company Code", companies, default=companies)
df_filtrado = df[df["CompanyCode"].isin(selecionadas)]

col1, col2 = st.columns(2)

# Filtro 2 - Vertical (opcional)
with col1:
    verticais = sorted(df_filtrado["vertical"].dropna().unique())
    vertical_sel = st.multiselect("🔹 Vertical (opcional)", verticais)
    if vertical_sel:
        df_filtrado = df_filtrado[df_filtrado["vertical"].isin(vertical_sel)]

# Filtro 3 - ProfitCenter (opcional)
with col2:
    profits = sorted(df_filtrado["ProfitCenter"].dropna().unique())
    profit_sel = st.multiselect("🔸 Profit Center (opcional)", profits)
    if profit_sel:
        df_filtrado = df_filtrado[df_filtrado["ProfitCenter"].isin(profit_sel)]

# Pivot Table
pivot = df_filtrado.pivot_table(
    index="agrupador_fpa",
    columns="FiscalPeriod",
    values="AmountInCompanyCodeCurrency",
    aggfunc="sum",
    fill_value=0
)

pivot.columns = [f"Mês {int(c)}" for c in pivot.columns]
pivot["Total"] = pivot.sum(axis=1)

st.subheader("📋 Soma por Agrupador FP&A x Mês")
st.dataframe(pivot.style.format("{:,.2f}"), use_container_width=True)
