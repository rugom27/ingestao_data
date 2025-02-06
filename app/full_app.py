import streamlit as st
from db import open_connection, close_connection


# ----------------------CONEXÃO À DB------------------
# Criar um estado no Streamlit para seguir a conexão
if "db_connection" not in st.session_state:
    st.session_state["db_connection"] = None

if "force_refresh" not in st.session_state:
    st.session_state["force_refresh"] = False
# ----------------------------------------------------

# Criar barra lateral para navegação e controle da conexão
st.sidebar.markdown("## 🔧 Controlo de Ligação (Base de dados)")
st.sidebar.markdown("---")

if st.sidebar.button("🟢 Abrir Conexão", key="abrir"):
    open_connection()

if st.sidebar.button("🔴 Fechar Conexão", key="fechar"):
    close_connection()


pages = {
    "Home": [
        st.Page("adicionar_vendas.py", title="Gestão de vendas e reuniões"),
        st.Page("modificar_reunioes.py", title="Ver relatórios"),
    ]
}

pg = st.navigation(pages)
pg.run()
