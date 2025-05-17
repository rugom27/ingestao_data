from llm import (
    fetch_reunioes,
    reunioes_to_json_chunks,
    get_segments_report,
    aggregate_reports,
)
import streamlit as st
import pandas as pd
from llm import preprocess_sentiment,fetch_reunioes_por_distrito,analyze_districts

import streamlit as st
import pandas as pd

# Main layout
st.title("Análise de Reuniões com Clientes")

# Create tabs
tab1, tab2 = st.tabs(["Relatório Geral", "Relatório por Região"])

# --- Tab 1: General Report ---
with tab1:
    if st.button("Gerar Relatório Geral"):
        with st.spinner("A analisar os dados..."):
            data = fetch_reunioes()
            df = pd.DataFrame(data)
            df = preprocess_sentiment(df)

            json_chunks = reunioes_to_json_chunks(df.to_dict(orient='records'))
            segment_reports = get_segments_report(json_chunks)
            final_report = aggregate_reports(segment_reports)

            st.success("Relatório gerado com sucesso!")
            st.markdown(final_report)

# --- Tab 2: Regional Report ---
with tab2:
    if st.button("Gerar Relatório por Região"):
        with st.spinner("A analisar os dados por distrito..."):
            district_data = fetch_reunioes_por_distrito()
            district_reports = analyze_districts(district_data)

            for district, report in district_reports.items():
                st.subheader(f"Relatório da região: {district}")
                st.markdown(report)
                st.divider()  # <- adds a visual break for scroll/readability

