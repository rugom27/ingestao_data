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
)
import re


tipo_cliente_options = [
    "Distribuição",
    "Produção animal",
    "Técnico/Consultor",
    "Consumidor Final - Outros",
    "Agricultor - Frutículas",
    "Cooperativa",
    "Revendedor - Biocidas",
    "Agricultor - Outros",
    "Revendedor - Cooperativa",
    "Revenda - Cash and Carry",
    "Distribuidor",
    "Revenda",
    "Revenda - Casa Agrícola",
    "Revendedor",
    "Revenda - Outros",
    "Agricultor",
    "Agricultor - Vinha",
    "Revenda - Cooperativa",
    "Revenda - Brico",
    "Revendedor - Casa agrícola",
    "Revenda-Gr. Distribuição",
    "Revenda - Drogaria",
]

distribuidor_options = {
    "Fertidouro, Lda": 1,
    "Pereiras & Almeida, Lda.": 2,
    "Nobre E Azevedo Unipessoal, Lda": 3,
    "GREMIORITA, PRODUTOS PARA AGRICULTURA, LDA": 4,
    "Joaquim Domingos Duarte Comba Ribeiro": 5,
    "Prorural-Produtos Agricolas, Lda": 6,
    "Manuel Gomes Lourenço, Lda": 7,
    "António Augusto Laja": 8,
    "Moncorvagri-Com. Prod.Agricolas,Lda": 9,
    "Nitrilon": 10,
    "União de Fruticultores da Cova da Beira": 11,
    "Sem Distribuidor": None,
}

# def display_page_to_rafael():
st.markdown(
    """
    <style>
    .centered-title {
        text-align: center;
    }
    </style>
    <h1 class='centered-title'>Gestão Comercial</h1>
    """,
    unsafe_allow_html=True,
)


tab1, tab2 = st.tabs(["Gestão de Clientes", "Adicionar Clientes/Produtos"])

with tab1:
    clientes = get_clientes()
    nomes_clientes = [c[1] for c in clientes]
    # Selecionar cliente
    cliente_selecionado_nome = st.selectbox("Selecione um cliente:", nomes_clientes)

    # ---------------------------------Obter numero máximo de cliente para sugerir-----------------------------
    lista_numeros_clientes = get_max_cliente()

    # Extrair apenas valores numéricos, ignorando alfanuméricos como "9A"
    numeros_validos = [
        int(row[0])
        for row in lista_numeros_clientes
        if row[0] and re.fullmatch(r"\d+", row[0])
    ]

    # Se houver números válidos, retorna o maior +1; senão, começa em 1
    ultimo_numero_cliente = str(max(numeros_validos) + 1) if numeros_validos else "1"

    cliente_id_selecionado = None
    for cliente in clientes:
        if cliente[1] == cliente_selecionado_nome:
            cliente_id_selecionado = cliente[0]
            break

    # ----------------------------TABELA DE REUNIOES-----------------------------------------------------------
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
                "Última Atualização",
                "Distribuidor",
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
                "Valor da Venda Total",
                "Data Criação",
                "Última Atualização",
                "Distribuidor",
            ],
        )
    else:
        st.warning("Não existem reuniões para este cliente.")

    # ---------------------REGISTO DE REUNIÃO--------------------------

    # Selecionar se houve não uma venda
    if "houve_venda" not in st.session_state:
        st.session_state["houve_venda"] = "Não"

    houve_venda = st.radio(
        "Foi feita uma venda?",
        ("Sim", "Não"),
        index=0 if st.session_state["houve_venda"] == "Sim" else 1,
    )
    st.session_state["houve_venda"] = houve_venda  # Atualiza o estado do formulario

    # Criar lista de produtos no session state se ainda não existir
    if "produtos_venda" not in st.session_state:
        st.session_state["produtos_venda"] = []

    st.header("Reunião")
    data_reuniao = st.date_input("Data da Reunião")
    descricao_reuniao = st.text_area("Descrição da Reunião")

    if st.session_state["houve_venda"] == "Sim":
        produtos = get_produtos()
        nomes_produtos = [p[1] for p in produtos]
        produto_selecionado = st.selectbox("Selecione um produto:", nomes_produtos)
        produto_id = next(p[0] for p in produtos if p[1] == produto_selecionado)
        quantidade = st.number_input("Quantidade vendida", min_value=1, step=1)
        preco_unitario = st.number_input("Preço unitário (€)", min_value=0.01)
        valor_total = quantidade * preco_unitario

        st.text(
            f"Valor de venda total do produto {produto_selecionado}: {valor_total:.2f} EUR"
        )

        # Botão para adicionar produto à lista de produtos vendidos
        if st.button("Adicionar Produto"):
            st.session_state["produtos_venda"].append(
                {
                    "Produto_id": produto_id,
                    "Produto": produto_selecionado,
                    "Quantidade": quantidade,
                    "Preço Unitário": preco_unitario,
                    "Valor Total": valor_total,
                }
            )
            st.success(f"Produto {produto_selecionado} adicionado!")

        # Mostrar lista de produtos adicionados à lista de produtos vendidos
        if st.session_state["produtos_venda"]:
            st.subheader("Produtos Adicionados")
            # Criar o dataframe com os produtos adicionados
            df_produtos = pd.DataFrame(st.session_state["produtos_venda"])
            # Criar o total da venda
            total_venda = df_produtos["Valor Total"].sum()

            # Exibir a tabela com os produtos adicionados
            st.dataframe(df_produtos, hide_index=True)

            # Exibir o total da venda estilizado
            st.markdown(
                f"""
                <div style="
                    background-color: #173928; 
                    color: white; 
                    padding: 10px; 
                    border-radius: 5px; 
                    text-align: center; 
                    font-size: 18px; 
                    font-weight: bold;
                    margin-bottom: 20px;">  <!-- Adiciona mais espaço abaixo -->
                    Total da venda: {total_venda:.2f} EUR
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        razao_nao_venda = st.text_area("Razão da não venda")
    st.write("")
    st.write("")
    st.write("")
    # REGISTAR REUNIÃO
    if st.button("Registar Reunião"):
        if cliente_id_selecionado is None:
            st.error("Por favor, selecione um cliente antes de registar a reunião.")
        else:
            reuniao_data = {
                "cliente_id": cliente_id_selecionado,
                "data_reuniao": str(data_reuniao),
                "descricao": descricao_reuniao,
                "houve_venda": st.session_state["houve_venda"],
            }

            if st.session_state["houve_venda"] == "Sim":
                if not st.session_state["produtos_venda"]:
                    st.error(
                        "Adicione pelo menos um produto antes de registar a venda!"
                    )
                else:
                    for produto in st.session_state["produtos_venda"]:
                        add_reuniao(
                            {
                                "cliente_id": cliente_id_selecionado,
                                "data_reuniao": str(data_reuniao),
                                "descricao": descricao_reuniao,
                                "houve_venda": "Sim",
                                "produto_id": produto[
                                    "Produto_id"
                                ],  # Corrigido para usar o produto correto
                                "quantidade_vendida": produto[
                                    "Quantidade"
                                ],  # Corrigido para usar a quantidade correta
                                "preco_vendido": produto[
                                    "Preço Unitário"
                                ],  # Corrigido para usar o preço correto
                                "razao_nao_venda": None,
                            }
                        )

                    st.success("Reunião e vendas registadas com sucesso!", icon="✅")

                    # Limpar a lista de produtos
                    st.session_state["produtos_venda"] = []

            elif st.session_state["houve_venda"] == "Não":
                if not razao_nao_venda.strip():
                    st.error("Por favor, preencha a razão pela qual não houve venda.")
                else:
                    add_reuniao(
                        {
                            "cliente_id": cliente_id_selecionado,
                            "data_reuniao": str(data_reuniao),
                            "descricao": descricao_reuniao,
                            "houve_venda": "Não",
                            "produto_id": None,
                            "quantidade_vendida": None,
                            "preco_vendido": None,
                            "razao_nao_venda": razao_nao_venda.strip(),
                        }
                    )

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
            tipo_cliente_novo = st.selectbox("Tipo de Cliente", tipo_cliente_options)
            distrito_novo = st.text_input("Distrito")
            latitude_novo = st.number_input("Latitude", format="%.6f")
            longitude_novo = st.number_input("Longitude", format="%.6f")
            distribuidor_novo = st.selectbox(
                "Distribuidor", list(distribuidor_options.keys())
            )
            distribuidor_novo = distribuidor_options[
                distribuidor_novo
            ]  # to get the value of the dict to the db
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
                        "distribuidor": distribuidor_novo,
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


# if st.button("Clear cache from connection"):
#     # Clears all st.cache_resource caches:
#     st.cache_resource.clear()
#     st.rerun()  # Atualiza a página imediatamente
