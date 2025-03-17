import streamlit as st
from db import get_all_reunioes_para_vizualizacao, get_taxa_de_conversao
import pandas as pd
from pandasql import sqldf
import altair as alt
import matplotlib.pyplot as plt
from datetime import datetime

now = datetime.now()
current_year = now.year
current_month = now.month

reunioes = (
    get_all_reunioes_para_vizualizacao()
)  # Obtem a tabela completa de reuniões e clientes

f_reunioes = pd.DataFrame(
    reunioes,
    columns=[
        "id_reuniao",
        "cliente_id",
        "data_reuniao",
        "descricao",
        "houve_venda",
        "produto_id",
        "quantidade_vendida",
        "preco_vendido",
        "razao_nao_venda",
        "data_criacao_linha_tabela_reunioes",
        "ultima_atualizacao",
        "id_cliente",
        "name",
        "numero_cliente",
        "cod_postal",
        "tipo_cliente",
        "cultura",
        "area_culturas",
        "responsavel_principal",
        "responsavel_secundario",
        "distrito",
        "latitude",
        "longitude",
        "data_criacao_linha_tabela_clientes",
    ],
)

st.title("Dashboard de Vendas")
col1, col2 = st.columns([2, 2])

with col1:
    # -----------------------------------------------------------------------------
    # 1. Cartão com o total de vendas total

    # -----------------------------------------------------------------------------
    valor_total_de_vendas = f_reunioes["preco_vendido"].sum()
    st.metric(
        f"Total de Vendas {current_year}",
        f"{float(valor_total_de_vendas)} €",
        border=True,
    )
    # -----------------------------------------------------------------------------
    # 2. Cartão com Month over Month Sales

    # -----------------------------------------------------------------------------
    # Vendas do Mês Atual
    df_mes_atual = f_reunioes[
        (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.year == current_year)
        & (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.month == current_month)
    ]
    valor_vendas_mes_atual = df_mes_atual["preco_vendido"].sum()

    # Vendas do Mês Anterior
    previous_year = current_year
    previous_month = current_month - 1
    if previous_month == 0:
        previous_month = 12
        previous_year -= 1

    df_mes_anterior = f_reunioes[
        (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.year == previous_year)
        & (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.month == previous_month)
    ]
    valor_vendas_mes_anterior = df_mes_anterior["preco_vendido"].sum()

    # Cálculo do Month-over-Month (M-o-M)

    if valor_vendas_mes_anterior != 0:
        delta_percent = (
            (valor_vendas_mes_atual - valor_vendas_mes_anterior)
            / valor_vendas_mes_anterior
            * 100
        )
    else:
        delta_percent = 0

    # Formata os nomes dos meses para exibição (ex: "February 2025")
    mes_atual_legivel = now.strftime("%B %Y")
    mes_anterior_legivel = datetime(previous_year, previous_month, 1).strftime("%B %Y")

    # Exibe a Métrica no Streamlit
    st.metric(
        label=f"Vendas {mes_atual_legivel}",
        value=f"{valor_vendas_mes_atual:.2f} €",
        delta=f"{delta_percent:.2f} % (MoM)",
        border=True,
    )


with col2:
    # -----------------------------------------------------------------------------
    # 2. Cartão com a taxa de conversão total

    # -----------------------------------------------------------------------------
    numero_de_reunioes_total = f_reunioes["houve_venda"].count()
    numero_de_reunioes_convertidas = (f_reunioes["houve_venda"] == "Sim").sum()
    taxa_de_conversao = numero_de_reunioes_convertidas / numero_de_reunioes_total * 100
    st.metric("Taxa de conversão (All-time)", f"{taxa_de_conversao:.2f} %", border=True)

    # -----------------------------------------------------------------------------
    # 4. Cartão com a taxa de conversão mensal

    # -----------------------------------------------------------------------------
    # Data e dia atual
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day

    # ------------------------------
    # Filtrar dados do mês atual até o dia atual
    # ------------------------------
    df_mes_atual = f_reunioes[
        (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.year == current_year)
        & (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.month == current_month)
        & (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.day <= current_day)
    ]

    numero_de_reunioes_total_atual = df_mes_atual["houve_venda"].count()
    numero_de_reunioes_convertidas_atual = (df_mes_atual["houve_venda"] == "Sim").sum()
    taxa_de_conversao_atual = (
        numero_de_reunioes_convertidas_atual / numero_de_reunioes_total_atual * 100
    )

    # ------------------------------
    # Determinar o mês anterior
    # ------------------------------
    previous_year = current_year
    previous_month = current_month - 1
    if previous_month == 0:
        previous_month = 12
        previous_year -= 1

    # ------------------------------
    # Filtrar dados do mês anterior até o mesmo dia (current_day)
    # ------------------------------
    df_mes_anterior = f_reunioes[
        (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.year == previous_year)
        & (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.month == previous_month)
        & (f_reunioes["data_criacao_linha_tabela_reunioes"].dt.day <= current_day)
    ]

    numero_de_reunioes_total_anterior = df_mes_anterior["houve_venda"].count()
    numero_de_reunioes_convertidas_anterior = (
        df_mes_anterior["houve_venda"] == "Sim"
    ).sum()
    taxa_de_conversao_anterior = (
        numero_de_reunioes_convertidas_anterior
        / numero_de_reunioes_total_anterior
        * 100
    )

    # ------------------------------
    # Cálculo do Month-over-Month (MoM) para a taxa de conversão
    # ------------------------------
    if taxa_de_conversao_anterior != 0:
        delta_percent = (
            (taxa_de_conversao_atual - taxa_de_conversao_anterior)
            / taxa_de_conversao_anterior
            * 100
        )
    else:
        delta_percent = 0

    # Formatação dos nomes dos meses para exibição
    mes_atual_legivel = now.strftime("%B %Y")
    mes_anterior_legivel = datetime(previous_year, previous_month, 1).strftime("%B %Y")

    # Exibir a métrica no Streamlit
    st.metric(
        label=f"Taxa de Conversão {mes_atual_legivel}",
        value=f"{taxa_de_conversao_atual:.2f} %",
        delta=f"{delta_percent:.2f} % (MoM)",
        border=True,
    )

# -----------------------------------------------------------------------------
# 5. Taxa de conversão por distrito
#
#
# -----------------------------------------------------------------------------

# --------------------------------------------------------
# 1. Carregar dados e manipular
# --------------------------------------------------------
df_visitas = pd.DataFrame(
    get_taxa_de_conversao(),
    columns=["distrito", "numero_de_visitas", "numero_de_visitas_convertidas"],
)

# Cria a coluna de percentagem (com tratamento de divisão por zero)
df_visitas["percentagem"] = (
    df_visitas["numero_de_visitas_convertidas"] / df_visitas["numero_de_visitas"] * 100
)
df_visitas["percentagem"] = df_visitas["percentagem"].fillna(0).round(2)

# Renomeia as colunas para exibição (opcional)
df_visitas.rename(
    columns={
        "numero_de_visitas": "Visitas",
        "numero_de_visitas_convertidas": "Visitas Convertidas",
        "percentagem": "Taxa de Conversão (%)",
    },
    inplace=True,
)

# Cria uma versão "longa" do DataFrame para o gráfico de barras agrupadas
df_long = df_visitas.melt(
    id_vars="distrito",
    value_vars=["Visitas", "Visitas Convertidas"],
    var_name="tipo_visita",
    value_name="numero",
)

# --------------------------------------------------------
# 2. Layout no Streamlit (colunas)
# --------------------------------------------------------
st.title("Taxa de Conversão por Distrito")

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

df_conversoes = df_visitas[["distrito", "Taxa de Conversão (%)"]].copy()

# Cria N colunas, onde N é o número de distritos
cols = st.columns(len(df_conversoes))

for i, row in df_conversoes.iterrows():
    distrito = row["distrito"]
    taxa = row["Taxa de Conversão (%)"]
    with cols[i]:
        st.metric(label=distrito, value=f"{taxa:.0f} %", border=True)


# Gráfico de barras agrupadas com tooltip
chart = (
    alt.Chart(df_long)
    .mark_bar()
    .encode(
        x=alt.X("distrito:N", axis=alt.Axis(labelAngle=-45), title="Distrito"),
        y=alt.Y("numero:Q", title="Número de Visitas"),
        xOffset="tipo_visita:N",  # Agrupamento
        color=alt.Color("tipo_visita:N", title="Tipo de Visita"),
        tooltip=[
            alt.Tooltip("distrito:N", title="Distrito"),
            alt.Tooltip("tipo_visita:N", title="Tipo de Visita"),
            alt.Tooltip("numero:Q", title="Quantidade"),
        ],
    )
    .properties(width=600, height=400)
)

st.altair_chart(chart, use_container_width=True)
