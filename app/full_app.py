import streamlit as st
from db import get_connection, close_connection

# Criar barra lateral para navegação e controle da conexão
st.sidebar.markdown("## 🔧 Controlo de Ligação (Base de dados)")
st.sidebar.markdown("---")

if st.sidebar.button("🟢 Abrir Conexão", key="abrir"):
    get_connection()

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
