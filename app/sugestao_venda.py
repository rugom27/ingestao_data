import streamlit as st
import pandas as pd
from db import get_sugestao_de_vendas


# 1️⃣ Sidebar filters
st.sidebar.header("🔍 Filtros")
sugestoes = get_sugestao_de_vendas()
df = pd.DataFrame(
    sugestoes,
    columns=["ID", "Timestamp", "Cliente", "Local", "Cultura", "Área", "Sugestão"],
)

clients = df["Cliente"].unique().tolist()
selected_client = st.sidebar.multiselect("Cliente", options=clients, default=clients)

districts = df["Local"].unique().tolist()
selected_district = st.sidebar.multiselect(
    "Local", options=districts, default=districts
)

filtered = df[df["Cliente"].isin(selected_client) & df["Local"].isin(selected_district)]

# 2️⃣ Main title
st.title("📊 Sugestões de Vendas por Cliente")
st.write(f"Mostrando **{len(filtered)}** sugestões")

# 3️⃣ Render each suggestion in an expander
for idx, row in filtered.iterrows():
    with st.expander(
        f"🧾 Sugestão {idx + 1} • Cliente: {row['Cliente']} • Local: {row['Local']}"
    ):
        col1, col2 = st.columns(2)
        col1.markdown(f"**ID:** {row['ID']}")
        col2.markdown(f"**Data:** {row['Timestamp']}")
        col1.markdown(f"**Cultura:** {row['Cultura']}")
        col2.markdown(f"**Área Cultivada:** {row['Área'] or 'Não especificada'}")
        st.markdown("> **Sugestão:**")
        st.write(row["Sugestão"])
        st.markdown("---")

# 4️⃣ Optional: show raw table
with st.expander("📋 Ver todas as sugestões (tabela bruta)"):
    st.dataframe(filtered.reset_index(drop=True))

# 5️⃣ Graceful empty state
if filtered.empty:
    st.info("Nenhuma sugestão disponível para os filtros selecionados.")
