import streamlit as st
import pandas as pd
from db import (
    get_clientes,
    get_produtos,
    get_ultimas_reunioes,
    add_cliente,
    add_produto,
    add_reuniao,
    get_max_cliente,
    update_reuniao,
)
import time


clientes_p2 = get_clientes()
nomes_clientes_p2 = [c[1] for c in clientes_p2]
cliente_selecionado_nome_p2 = st.selectbox("Selecione um cliente:", nomes_clientes_p2)

cliente_id_selecionado_p2 = None
for cliente in clientes_p2:
    if cliente[1] == cliente_selecionado_nome_p2:
        cliente_id_selecionado_p2 = cliente[0]
        break

reunioes_p2 = get_ultimas_reunioes(cliente_id_selecionado_p2)

# Verifica se há reuniões e converte para DataFrame
if reunioes_p2 and isinstance(reunioes_p2, list):
    df_reunioes = pd.DataFrame(
        reunioes_p2,
        columns=[
            "ID",
            "Cliente ID",
            "Data",
            "Descrição",
            "Houve Venda",
            "Produto ID",
            "Quantidade",
            "Preço",
            "Razão Não Venda",
            "Data Criação",
            "Última Atualização",
        ],
    )
    edited_df = st.data_editor(
        df_reunioes,
        use_container_width=True,
        hide_index=True,
        disabled=("ID", "Cliente ID", "Data Criação"),
        column_order=[
            "ID",
            "Cliente ID",
            "Data",
            "Descrição",
            "Houve Venda",
            "Razão Não Venda",
            "Produto ID",
            "Quantidade",
            "Preço",
            "Data Criação",
            "Última Atualização",
        ],
        key="edit_reunioes",
    )
else:
    st.warning("Não existem reuniões para este cliente.")

if st.button("Guardar Alterações"):
    for i in range(len(df_reunioes)):
        original = df_reunioes.iloc[i]
        edited = edited_df.iloc[i]

        # Verifica se houve alterações
        if not original.equals(edited):
            update_reuniao(
                reuniao_id=edited["ID"],
                descricao=edited["Descrição"],
                houve_venda=edited["Houve Venda"],
                razao_nao_venda=edited["Razão Não Venda"],
                produto_id=edited["Produto ID"],
                quantidade=edited["Quantidade"],
                preco=edited["Preço"],
            )
