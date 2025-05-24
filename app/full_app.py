import streamlit as st

# Exibir o logo no topo da aplicação
st.image("logo_jovagro.png")  # Ajusta a largura conforme necessário

pages = {
    "Home": [
        st.Page("adicionar_vendas.py", title="Gestão de vendas e reuniões"),
        st.Page("modificar_reunioes.py", title="Ver relatórios"),
        st.Page("visualizacao_graficos.py", title="Visualizar dados"),
        st.Page("analise_distribuidores.py", title="Análise de Distribuidores"),
        st.Page("assistant.py", title="Assistente Pessoal"),
        st.Page("sugestao_venda.py", title="Sugestões de Venda por Cliente"),
    ]
}

pg = st.navigation(pages)
pg.run()
