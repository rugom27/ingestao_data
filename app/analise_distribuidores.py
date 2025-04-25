from db import (
    vendas_a_agricultores_para_distribuidores,
    vendas_a_distribuidores_2024_relatorio_vendas,
    vendas_a_distribuidores_relatorio_reunioes,
)
import streamlit as st
import pandas as pd
import numpy as np

# # Display vendas_a_distribuidores_2024_relatorio_vendas
# st.header("Vendas a Distribuidores em 2024 (Relatório Fiscal)")
# distribuidores_2024_data = vendas_a_distribuidores_2024_relatorio_vendas()
# st.table(distribuidores_2024_data)


# # Display vendas_a_agricultores_para_distribuidores
# st.header("Vendas a Agricultores para Distribuidores")
# agricultores_data = vendas_a_agricultores_para_distribuidores()
# st.table(agricultores_data)

# # Display vendas_a_distribuidores_relatorio_reunioes
# st.header("Vendas a Distribuidores (Reuniões)")
# distribuidores_reunioes_data = vendas_a_distribuidores_relatorio_reunioes()
# st.table(distribuidores_reunioes_data)


df_vendas_a_agricultores_para_distribuidores = (
    vendas_a_agricultores_para_distribuidores()
)
df_vendas_a_distribuidores_relatorio_reunioes = (
    vendas_a_distribuidores_relatorio_reunioes()
)


df_far = pd.DataFrame(
    df_vendas_a_agricultores_para_distribuidores,
    columns=["Distribuidor", "ID_Distribuidor", "Vendas_a_Agricultores"],
)

df_meet = pd.DataFrame(
    df_vendas_a_distribuidores_relatorio_reunioes,
    columns=["Distribuidor", "Vendas_a_Distribuidores"],
)


df = df_meet.merge(df_far, on="Distribuidor", how="outer").fillna(
    {"Vendas_a_Agricultores": 0}
)

# Calcular Métricas
df["Diferença"] = df["Vendas_a_Agricultores"] - df["Vendas_a_Distribuidores"]
df["Razão"] = df.apply(
    lambda x: (
        x.Vendas_a_Agricultores / x.Vendas_a_Distribuidores
        if x.Vendas_a_Distribuidores > 0
        else 0
    ),
    axis=1,
)

col1, col2 = st.columns([2, 2])
with col1:
    st.metric(
        "Total Vendido a Distribuidores (em Reuniões)",
        f"€ {df['Vendas_a_Distribuidores'].sum():,.1f}",
    )
with col2:
    st.metric(
        "Total vendido dos Distribuidores aos Agricultores",
        f"€ {df['Vendas_a_Agricultores'].sum():,.1f}",
        delta=f"€ {df['Diferença'].sum():,.1f}",
    )


# --------------------------- Gráfico comparativo (Altair)--------------------

import altair as alt

df_melt = df.melt(
    id_vars="Distribuidor",
    value_vars=["Vendas_a_Distribuidores", "Vendas_a_Agricultores"],
    var_name="Tipo",
    value_name="Valor",
)

# Garante que Valor é numérico
df_melt["Valor"] = pd.to_numeric(df_melt["Valor"], errors="coerce")

# 5) Cria o gráfico de barras horizontais
chart = (
    alt.Chart(df_melt)
    .mark_bar()
    .encode(
        # ordena pelas somas de Valor, do maior para o menor
        y=alt.Y(
            "Distribuidor:N",
            sort=alt.EncodingSortField(field="Valor", op="sum", order="descending"),
            title="Distribuidor",
        ),
        x=alt.X(
            "Valor:Q",
            title="€ Valor",
            axis=alt.Axis(format=",.2f"),  # separador de milhares + 2 casas
        ),
        color=alt.Color("Tipo:N", title="Tipo de Venda"),
        tooltip=[
            alt.Tooltip("Distribuidor:N"),
            alt.Tooltip("Tipo:N", title="Tipo"),
            alt.Tooltip("Valor:Q", title="€ Valor", format=",.2f"),
        ],
    )
    .properties(width=700, height=400)
)

st.altair_chart(chart, use_container_width=True)


# ---------------------------Tabela ordenada com diferença e razão---------------------------

df_display = df.drop(columns=["ID_Distribuidor"])

# Rename das colunas
df_display = df_display.rename(
    columns={
        "Vendas_a_Distribuidores": "Vendido a Distribuidores (€)",
        "Vendas_a_Agricultores": "Vendido a Agricultores por Distribuidores (€)",
    }
)


# função que pinta a célula de verde se >0, de vermelho se <0
def color_diff(val):
    if val > 0:
        return (
            "background-color: #1DB954; color:black; font-weight: bold"  # verde claro
        )
    elif val < 0:
        return "background-color: #FF0000; color:black; font-weight: bold"  # vermelho claro
    else:
        return ""  # sem cor se for zero


styled = df_display.style.format(
    {
        "Vendas em Reunião aos Distribuidores (€)": "€ {:,.2f}",
        "Vendas a Agricultores por Distribuidores (€)": "€ {:,.2f}",
        "Diferença": "€ {:,.2f}",
        "Razão": "{:.2f}x",
    }
).map(color_diff, subset=["Diferença"])

# 4) Exibe com Streamlit
st.dataframe(styled, hide_index=True, use_container_width=True)
