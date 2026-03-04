import streamlit as st
import pandas as pd
import gdown

st.set_page_config(page_title="Base SAP S4", layout="wide")
st.title("📊 Base SAP S4 - Prévia")

@st.cache_data
def carregar_dados():
    url = "https://drive.google.com/uc?id=1Lm-G9ZJUC2Hzc9iIKIb6LCemYJqtzNQO"
    gdown.download(url, "dados.xlsx", quiet=True)
    return pd.read_excel("dados.xlsx")

df = carregar_dados()

col1, col2, col3 = st.columns(3)
col1.metric("Linhas", df.shape[0])
col2.metric("Colunas", df.shape[1])
col3.metric("Células", df.shape[0] * df.shape[1])

st.subheader("📋 Dados")
st.dataframe(df, use_container_width=True)

with st.expander("📈 Estatísticas"):
    st.dataframe(df.describe(), use_container_width=True)
