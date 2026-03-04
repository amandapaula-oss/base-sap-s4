import streamlit as st
import pandas as pd
import gdown

st.set_page_config(page_title="Base SAP S4", layout="wide")
st.title("📊 Base SAP S4 - Prévia")

@st.cache_data
def carregar_dados():
    url = "https://drive.google.com/uc?id=1Lm-G9ZJUC2Hzc9iIKIb6LCemYJqtzNQO"
    gdown.download(url, "dados.xlsx", quiet=True)
    colunas = ["CompanyCode", "agrupador_fpa", "FiscalPeriod", "AmountInCompanyCodeCurrency"]
    return pd.read_excel("dados.xlsx", usecols=colunas)

df = carregar_dados()

# Filtro por Company
companies = sorted(df["CompanyCode"].dropna().unique())
selecionadas = st.multiselect("🏢 Filtrar por Company Code", companies, default=companies)

df_filtrado = df[df["CompanyCode"].isin(selecionadas)]

# Pivot Table
pivot = df_filtrado.pivot_table(
    index="agrupador_fpa",
    columns="FiscalPeriod",
    values="AmountInCompanyCodeCurrency",
    aggfunc="sum",
    fill_value=0
)

# Formatar colunas de mês
pivot.columns = [f"Mês {int(c)}" for c in pivot.columns]

# Total por linha
pivot["Total"] = pivot.sum(axis=1)

st.subheader("📋 Soma por Agrupador FP&A x Mês")
st.dataframe(pivot.style.format("{:,.2f}"), use_container_width=True)
