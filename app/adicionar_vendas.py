import streamlit as st
import traceback
import pandas as pd
from db import (
    get_clientes,
    get_produtos,
    get_ultimas_reunioes,
    add_cliente,
    add_produto,
    add_reuniao,
    get_max_cliente,
    get_connection,
    close_connection,
)


# def display_page_to_rafael():
st.markdown(
    """
    <style>
    .centered-title {
        text-align: center;
    }
    </style>
    <h1 class='centered-title'>Gestão Comercial - Jovagro</h1>
    """,
    unsafe_allow_html=True,
)

ultimo_numero_cliente = get_max_cliente()

tab1, tab2 = st.tabs(["Gestão de Clientes", "Adicionar Clientes/Produtos"])

with tab1:
    clientes = get_clientes()
    nomes_clientes = [c[1] for c in clientes]
    cliente_selecionado_nome = st.selectbox("Selecione um cliente:", nomes_clientes)

    cliente_id_selecionado = None
    for cliente in clientes:
        if cliente[1] == cliente_selecionado_nome:
            cliente_id_selecionado = cliente[0]
            break

    # ---------------------TABELA DE REUNIOES--------------------------
    reunioes = get_ultimas_reunioes(cliente_id_selecionado)

    # Verifica se há reuniões e converte para DataFrame
    if reunioes and isinstance(reunioes, list):
        df_reunioes = pd.DataFrame(
            reunioes,
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
            ],
        )
        st.dataframe(
            df_reunioes,
            use_container_width=True,
            hide_index=True,
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
            ],
        )
    else:
        st.warning("Não existem reuniões para este cliente.")

    # ---------------------FORMULARIO DA REUNIAO--------------------------

    # Selecionar se houve não uma venda
    if "houve_venda" not in st.session_state:
        st.session_state["houve_venda"] = "Não"

    houve_venda = st.radio(
        "Foi feita uma venda?",
        ("Sim", "Não"),
        index=0 if st.session_state["houve_venda"] == "Sim" else 1,
    )
    st.session_state["houve_venda"] = houve_venda  # Atualiza o estado do formulario

    # Formulário de reunião
    # with st.form("formulario_de_reuniao", clear_on_submit=False, enter_to_submit=False):
    #     st.header("Reunião")
    #     data_reuniao = st.date_input("Data da Reunião")
    #     descricao_reuniao = st.text_area("Descrição da Reunião")

    #     # houve_venda = st.radio("Foi feita uma venda?", ("Sim", "Não"))

    #     produto_id = None
    #     quantidade = None
    #     valor_total = None
    #     razao_nao_venda = None

    #     if houve_venda == "Sim":
    #         produtos = get_produtos()
    #         nomes_produtos = [p[1] for p in produtos]
    #         produto_selecionado = st.selectbox(
    #             "Selecione um produto ou adicione um novo:", nomes_produtos
    #         )
    #         produto_id = next(p[0] for p in produtos if p[1] == produto_selecionado)

    #         quantidade = st.number_input("Quantidade vendida", min_value=1, step=1)
    #         valor_total = st.number_input(
    #             "Valor total da venda (€)", min_value=0.01, step=0.01
    #         )
    #         valor_calculado = quantidade * valor_total
    #         st.text(f"Valor total calculado (sugestão): {valor_calculado:.2f} EUR")
    #     else:
    #         razao_nao_venda = st.text_area("Razão da não venda")

    #     submit_button = st.form_submit_button("Registar Reunião")

    with st.form("formulario_de_reuniao", clear_on_submit=False, enter_to_submit=False):
        st.header("Reunião")
        data_reuniao = st.date_input("Data da Reunião")
        descricao_reuniao = st.text_area("Descrição da Reunião")

        if st.session_state["houve_venda"] == "Sim":
            produtos = get_produtos()
            nomes_produtos = [p[1] for p in produtos]
            produto_selecionado = st.selectbox("Selecione um produto:", nomes_produtos)
            produto_id = next(p[0] for p in produtos if p[1] == produto_selecionado)
            quantidade = st.number_input("Quantidade vendida", min_value=1, step=1)
            valor_total = st.number_input(
                "Valor total da venda (€)", min_value=0.01, step=0.01
            )
            valor_calculado = quantidade * valor_total
            st.text(f"Valor total calculado (sugestão): {valor_calculado:.2f} EUR")
        else:
            razao_nao_venda = st.text_area("Razão da não venda")

        submit_button = st.form_submit_button("Registar Reunião")
        # ------------------------------------------------------------- #
        if submit_button:
            if cliente_id_selecionado is None:
                st.error("Por favor, selecione um cliente antes de registar a reunião.")
            else:
                reuniao_data = {
                    "cliente_id": cliente_id_selecionado,
                    "data_reuniao": str(data_reuniao),
                    "descricao": descricao_reuniao,
                    "houve_venda": houve_venda,
                }

                if houve_venda == "Sim":
                    if produto_id is None or quantidade <= 0 or valor_total <= 0:
                        st.error(
                            "Por favor, preencha todos os campos relacionados à venda."
                        )
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
                    if not razao_nao_venda.strip():
                        st.error(
                            "Por favor, preencha a razão pela qual não houve venda."
                        )
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
                    st.error(f"Erro ao registar reunião: {e}")
                    st.text_area("Detalhes do erro", traceback.format_exc())

with tab2:

    with st.expander("Cliente novo?"):
        with st.form("novo_cliente_form", enter_to_submit=False):
            name_novo = st.text_input("Nome do Cliente", max_chars=100)

            col1, col2 = st.columns([3, 1])
            with col1:
                numero_cliente_novo = st.text_input(
                    "Número do Cliente", key="numero_cliente"
                )

            with col2:
                if ultimo_numero_cliente.isnumeric():
                    st.markdown(
                        f'<p style="text-align: center; font-size: 14px; color: lightgray;">'
                        f"Último número de cliente registado:<br>"
                        f'<span style="color: #00FF00; font-weight: bold;">{ultimo_numero_cliente}</span></p>',
                        unsafe_allow_html=True,
                    )

            cod_postal_novo = st.text_input("Código Postal")
            tipo_cliente_novo = st.text_input("Tipo de Cliente")
            distrito_novo = st.text_input("Distrito")
            latitude_novo = st.number_input("Latitude", format="%.6f")
            longitude_novo = st.number_input("Longitude", format="%.6f")

            submit_cliente = st.form_submit_button("Registar Cliente")

            if submit_cliente:
                if (
                    not name_novo
                    or not numero_cliente_novo
                    or not cod_postal_novo
                    or not tipo_cliente_novo
                    or not distrito_novo
                ):
                    st.error("Por favor, preencha todos os campos obrigatórios.")
                else:
                    cliente_data = {
                        "name": name_novo,
                        "numero_cliente": numero_cliente_novo,
                        "cod_postal": cod_postal_novo,
                        "tipo_cliente": tipo_cliente_novo,
                        "distrito": distrito_novo,
                        "latitude": latitude_novo,
                        "longitude": longitude_novo,
                    }
                    try:
                        add_cliente(cliente_data)
                        st.success(
                            f"Cliente '{name_novo}' registado com sucesso com o número {numero_cliente_novo}!"
                        )
                        st.rerun()  # Atualiza a página imediatamente
                    except Exception as e:
                        st.error(f"Erro ao registar cliente: {e}")
                        st.text_area("Detalhes do erro", traceback.format_exc())

    with st.expander("Produto novo?"):
        with st.form("novo_produto_form", enter_to_submit=False):
            novo_produto = st.text_input("Nome do Novo Produto")
            adicionar_produto = st.form_submit_button("Adicionar Produto")
            if adicionar_produto and novo_produto:
                produto_id = add_produto(novo_produto)
                st.success("Produto adicionado com sucesso!")
                st.rerun()  # Atualiza a página imediatamente


# # Show different content based on the user's email address.
# if st.experimental_user.email == "rafacavac@gmail.com":
#     display_page_to_rafael()
# elif st.experimental_user.email == "ruigomes950@gmail.com":
#     display_page_to_rafael()
# else:
#     st.write("Please contact us to get access!")


if st.button("Abrir conexão à base de dados"):
    conn = get_connection()  # Chama a função para abrir a conexão
    st.success("Conexão aberta com sucesso!")

if st.button("Fechar conexão à base de dados"):
    close_connection()  # Chama a função para fechar a conexão
    st.warning("Conexão fechada!")
