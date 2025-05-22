import streamlit as st
from db import (
    get_all_reunioes_para_vizualizacao,
    get_taxa_de_conversao,
    get_all_produtos,
)
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
        "supplier_id_tabela_reunioes",
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
        "supplier_id",
    ],
)

f_reunioes["preco_vendido"] = f_reunioes["preco_vendido"].astype(float)
f_reunioes["quantidade_vendida"] = f_reunioes["quantidade_vendida"].astype(float)

f_reunioes["total_vendido"] = (
    f_reunioes["quantidade_vendida"] * f_reunioes["preco_vendido"]
)

# convert data reuniao to datetime
f_reunioes["data_reuniao"] = pd.to_datetime(f_reunioes["data_reuniao"])

st.title("Dashboard de Vendas")
col1, col2 = st.columns([2, 2])

with col1:
    # -----------------------------------------------------------------------------
    # 1. Cartão com o total de vendas total

    # -----------------------------------------------------------------------------
    valor_total_de_vendas = f_reunioes["total_vendido"].sum()
    st.metric(
        f"Total de Vendas {current_year}",
        f"{valor_total_de_vendas:.2f} €",
        border=True,
    )
    # -----------------------------------------------------------------------------
    # 2. Cartão com Month over Month Sales

    # -----------------------------------------------------------------------------
    # Vendas do Mês Atual
    df_mes_atual = f_reunioes[
        (f_reunioes["data_reuniao"].dt.year == current_year)
        & (f_reunioes["data_reuniao"].dt.month == current_month)
    ]
    valor_vendas_mes_atual = df_mes_atual["total_vendido"].sum()

    # Vendas do Mês Anterior
    previous_year = current_year
    previous_month = current_month - 1
    if previous_month == 0:
        previous_month = 12
        previous_year -= 1

    df_mes_anterior = f_reunioes[
        (f_reunioes["data_reuniao"].dt.year == previous_year)
        & (f_reunioes["data_reuniao"].dt.month == previous_month)
    ]
    valor_vendas_mes_anterior = df_mes_anterior["total_vendido"].sum()

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
        (f_reunioes["data_reuniao"].dt.year == current_year)
        & (f_reunioes["data_reuniao"].dt.month == current_month)
        & (f_reunioes["data_reuniao"].dt.day <= current_day)
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
        (f_reunioes["data_reuniao"].dt.year == previous_year)
        & (f_reunioes["data_reuniao"].dt.month == previous_month)
        & (f_reunioes["data_reuniao"].dt.day <= current_day)
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


# Vendas por agricultor por mês
# --------------------------------------------------------
#
# --------------------------------------------------------
df_histograma = f_reunioes.copy()
df_histograma["data_reuniao"] = pd.to_datetime(
    df_histograma["data_reuniao"], errors="coerce"
)

df_histograma["mes"] = df_histograma["data_reuniao"].dt.strftime("%B")
df_histograma["mes_numero"] = df_histograma["data_reuniao"].dt.month
df_histograma["ano"] = df_histograma["data_reuniao"].dt.year

top_agricultor_by_month = (
    df_histograma.groupby(["ano", "mes", "mes_numero", "name"])
    .agg({"total_vendido": "sum"})
    .reset_index()
)
# Agrupa por ano e mês, e soma as vendas


# Find the agricultor with the most total vendido for each month
top_agricultor = top_agricultor_by_month.loc[
    top_agricultor_by_month.groupby(["ano", "mes_numero"])["total_vendido"].idxmax()
]

# Sort by year and month
top_agricultor = top_agricultor.sort_values(by=["ano", "mes_numero"])

st.title("Top Clientes por Mês")

for index, row in top_agricultor.iterrows():
    st.metric(
        label=f"Year: {row['ano']} - Month: {row['mes']}",
        value=f"{row['name']}",
        delta=f"Total Vendido: {row['total_vendido']:.2f} €",
    )
    st.write("---")
    # Adiciona uma linha separadora entre os meses
    # st.markdown("---")

#
# --------------------------------------------------------
#  Vendas por Produto por mês
# --------------------------------------------------------

# Supondo que f_reunioes é o DataFrame original
df_histograma = f_reunioes.copy()
df_histograma["data_reuniao"] = pd.to_datetime(
    df_histograma["data_reuniao"], errors="coerce"
)

df_histograma["mes"] = df_histograma["data_reuniao"].dt.strftime("%B")
df_histograma["mes_numero"] = df_histograma["data_reuniao"].dt.month
df_histograma["ano"] = df_histograma["data_reuniao"].dt.year

# importar dados do produto
produtos = get_all_produtos()

df_produtos = pd.DataFrame(
    produtos, columns=["produto_id", "ref", "data_criacao_linha"]
)


# Juntar nome do produto ao dataframe pós histograma
df_histograma = df_histograma.merge(
    df_produtos[["produto_id", "ref"]],
    how="left",
    left_on="produto_id",
    right_on="produto_id",
)


top_produto_by_month = (
    df_histograma.groupby(["ano", "mes", "mes_numero", "ref"])
    .agg({"total_vendido": "sum"})
    .reset_index()
)
# Agrupa por ano, mês e produto, e soma as vendas

# Encontra o produto com o maior total vendido para cada mês
top_produto = top_produto_by_month.loc[
    top_produto_by_month.groupby(["ano", "mes_numero"])["total_vendido"].idxmax()
]

# Ordena por ano e mês
top_produto = top_produto.sort_values(by=["ano", "mes_numero"])

st.title("Top Produtos por Mês")

for index, row in top_produto.iterrows():
    st.metric(
        label=f"Year: {row['ano']} - Month: {row['mes']}",
        value=f"{row['ref']}",
        delta=f"Total Vendido: {row['total_vendido']:.2f} €",
    )
    st.write("---")
    # Adiciona uma linha separadora entre os meses
    # st.markdown("---")


# ------------------------------------------------------------------
# Revenue & Conversion by Crop Type
# ------------------------------------------------------------------
crop_stats = (
    f_reunioes.groupby("cultura")
    .agg(
        visitas=("houve_venda", "count"),
        vendas=("houve_venda", lambda x: (x == "Sim").sum()),
        receita=("total_vendido", "sum"),
    )
    .reset_index()
)
crop_stats["taxa_conv_%"] = (crop_stats["vendas"] / crop_stats["visitas"] * 100).round(
    1
)

st.header("Receita e Taxa de Conversão por Cultura (Norte)")
st.dataframe(crop_stats.sort_values("receita", ascending=False))

chart = (
    alt.Chart(crop_stats)
    .mark_bar()
    .encode(
        x=alt.X("cultura:N", sort="-y", title="Cultura"),
        y=alt.Y("receita:Q", title="Receita (€)"),
        tooltip=["receita:Q", "taxa_conv_%:Q"],
        color=alt.value("steelblue"),
    )
    .properties(width=600, height=400)
)
st.altair_chart(chart, use_container_width=True)


# ------------------------------------------------------------------
# Funnel per Sales Rep  –  now with "zero‑sales" aggregation
# ------------------------------------------------------------------
rep_stats = (
    f_reunioes.groupby("responsavel_principal")
    .agg(
        visitas=("houve_venda", "count"),
        vendas=("houve_venda", lambda x: (x == "Sim").sum()),
        receita=("total_vendido", "sum"),
    )
    .reset_index()
)
rep_stats["taxa_conv_%"] = (rep_stats["vendas"] / rep_stats["visitas"] * 100).round(1)


# 1. Split reps into "has revenue" vs "no revenue"

mask_zero = rep_stats["receita"] == 0
rep_no_sales = rep_stats[mask_zero]
rep_sales = rep_stats[~mask_zero]

# 2. Aggregate the zero‑revenue reps

if not rep_no_sales.empty:
    agg_row = {
        "responsavel_principal": f"{len(rep_no_sales)} vendedor(es) sem vendas",
        "visitas": rep_no_sales["visitas"].sum(),
        "vendas": rep_no_sales["vendas"].sum(),
        "receita": 0.0,
    }
    agg_row["taxa_conv_%"] = (
        agg_row["vendas"] / agg_row["visitas"] * 100 if agg_row["visitas"] else 0
    )
    rep_display = pd.concat([rep_sales, pd.DataFrame([agg_row])], ignore_index=True)
else:
    rep_display = rep_stats.copy()

# 3. Display metric cards (best revenue first)

st.header("Desempenho por Vendedor (Norte)")
for _, row in rep_display.sort_values("receita", ascending=False).iterrows():
    st.metric(
        label=row["responsavel_principal"],
        value=f"{row['receita']:.0f} €",
        delta=f"Conv.: {row['taxa_conv_%']:.1f} %",
    )


# ------------------------------------------------------------------
# ASP & Margin per Product
# ------------------------------------------------------------------
# (Requires a `custo_unitario` column; replace or drop if not available)
if "custo_unitario" in f_reunioes.columns:
    prod_margin = (
        f_reunioes.groupby("ref")
        .agg(
            receita=("total_vendido", "sum"),
            qty=("quantidade_vendida", "sum"),
            custo_total=(
                "custo_unitario",
                lambda x: (x * f_reunioes.loc[x.index, "quantidade_vendida"]).sum(),
            ),
        )
        .reset_index()
    )
    prod_margin["ASP"] = prod_margin["receita"] / prod_margin["qty"]
    prod_margin["margem_%"] = (
        (prod_margin["receita"] - prod_margin["custo_total"])
        / prod_margin["receita"]
        * 100
    ).round(1)

    st.header("ASP e Margem por Produto (Norte)")
    st.dataframe(
        prod_margin.sort_values("margem_%", ascending=False)[["ref", "ASP", "margem_%"]]
    )
