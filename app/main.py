import streamlit as st
import psycopg2
import pandas as pd
from db import (
    get_connection,
    get_clientes,
    get_produtos,
    get_ultimas_reunioes,
    add_cliente,
    add_produto,
    add_reuniao,
)

get_connection()

# Interface Streamlit
st.title("Gestão Comercial - Jovagro")

# Seleção de Cliente
clientes = get_clientes()

# Colocar a informação da query em listas
# cliente_id = [c[0] for c in clientes]
nomes_clientes = [c[1] for c in clientes]
# numeros_clientes = [c[2] for c in clientes]
# cod_postal_clientes = [c[3] for c in clientes]
# tipo_clientes = [c[4] for c in clientes]
# distritos_clientes = [c[5] for c in clientes]
# latitudes_clientes = [c[6] for c in clientes]
# longitudes_clientes = [c[7] for c in clientes]

cliente_selecionado_nome = st.selectbox("Selecione um cliente:", nomes_clientes)

for cliente in clientes:
    if cliente[1] == cliente_selecionado_nome:
        cliente_id_selecionado = cliente[0]
        break


novo_cliente = st.checkbox("Cliente novo?")
if novo_cliente:
    with st.form("novo_cliente_form"):
        name = st.text_input("Nome do Cliente", max_chars=100)
        numero_cliente = st.text_input(
            "Número do Cliente (Opcional)"
        )  # Por enquanto deixar assim mas depois gerar uma função para o caso de isto não ser preenchido, colocar um número de cliente aleatório (nao presente na tabela).
        cod_postal = st.text_input("Código Postal")
        tipo_cliente = st.text_input("Tipo de Cliente")
        distrito = st.text_input("Distrito")
        latitude = st.number_input("Latitude", format="%.6f")
        longitude = st.number_input("Longitude", format="%.6f")
        submit_cliente = st.form_submit_button("Registar Cliente")

        if submit_cliente:
            cliente_data = {
                "name": name,
                "numero_cliente": numero_cliente or None,
                "cod_postal": cod_postal,
                "tipo_cliente": tipo_cliente,
                "distrito": distrito,
                "latitude": latitude,
                "longitude": longitude,
            }
            try:
                add_cliente(cliente_data)
                st.success("Cliente registado com sucesso!")
            except Exception as e:
                st.error("Erro ao registar cliente")

st.header("Reunião")
data_reuniao = st.date_input("Data da Reunião")
descricao_reuniao = st.text_area("Descrição da Reunião")

# Perguntar se houve venda
houve_venda = st.radio("Foi feita uma venda?", ("Sim", "Não"))

if houve_venda == "Sim":
    produtos = get_produtos()
    nomes_produtos = [p[1] for p in produtos]
    produto_selecionado = st.selectbox(
        "Selecione um produto ou adicione um novo:", nomes_produtos + ["Adicionar Novo"]
    )

    if produto_selecionado == "Adicionar Novo":
        novo_produto = st.text_input("Nome do Novo Produto")
        if st.button("Adicionar Produto") and novo_produto:
            produto_id = add_produto(novo_produto)
            st.success("Produto adicionado com sucesso!")
    else:
        produto_id = next(p[0] for p in produtos if p[1] == produto_selecionado)

    quantidade = st.number_input("Quantidade vendida", min_value=1, step=1)
    valor_total = st.number_input("Valor total da venda (€)", min_value=0.01, step=0.01)
    valor_calculado = quantidade * valor_total  # Pequena ajuda para utilizador saber
    st.text(f"Valor total calculado (sugestão): {valor_calculado:.2f} EUR")
else:
    razao_nao_venda = st.text_area("Razão da não venda")

if st.button("Registar Reunião"):
    # Garantir que o cliente_id é válido
    if cliente_id_selecionado is None:
        st.error("Por favor, selecione um cliente antes de registar a reunião.")
    else:
        # Construção inicial do JSON
        reuniao_data = {
            "cliente_id": cliente_id_selecionado,
            "data_reuniao": str(data_reuniao),
            "descricao": descricao_reuniao,
            "houve_venda": houve_venda,
        }

        # Dados adicionais dependendo de "houve_venda"
        if houve_venda == "Sim":
            # Verificar campos obrigatórios para vendas
            if produto_id is None or quantidade <= 0 or valor_total <= 0:
                st.error("Por favor, preencha todos os campos relacionados à venda.")
            else:
                reuniao_data.update(
                    {
                        "produto_id": produto_id,
                        "quantidade_vendida": quantidade,
                        "preco_vendido": valor_total,
                        "razao_nao_venda": None,
                    }
                )
        elif houve_venda == "Não":
            # Garantir que a razão da não venda está preenchida
            if not razao_nao_venda.strip():
                st.error("Por favor, preencha a razão pela qual não houve venda.")
            else:
                reuniao_data.update(
                    {
                        "produto_id": None,
                        "quantidade_vendida": None,
                        "preco_vendido": None,
                        "razao_nao_venda": razao_nao_venda.strip(),
                    }
                )
        try:
            add_reuniao(reuniao_data)
            st.success("Reunião registada com sucesso!")
        except Exception as e:
            st.error("Erro ao registar reunião")
