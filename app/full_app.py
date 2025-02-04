import streamlit as st

pages = {
    "Home": [
        st.Page("adicionar_vendas.py", title="Gestão de vendas e reuniões"),
        st.Page("modificar_reunioes.py", title="Modificar reuniões"),
    ]
}

pg = st.navigation(pages)
pg.run()
