import streamlit as st

# Exibir o logo no topo da aplicação
st.image("logo_jovagro.png")  # Ajusta a largura conforme necessário

pages = {
    "Home": [
        st.Page("adicionar_vendas.py", title="Gestão de vendas e reuniões"),
        st.Page("modificar_reunioes.py", title="Ver relatórios"),
        st.Page("visualizacao_graficos.py", title="Visualizar dados"),
    ]
}

pg = st.navigation(pages)
pg.run()
