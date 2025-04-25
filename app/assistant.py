from llm import (
    fetch_reunioes,
    reunioes_to_json_chunks,
    get_segments_report,
    aggregate_reports,
)
import streamlit as st


def generate_report():
    results_for_aggregation = []
    all_data = fetch_reunioes()
    json_chunks = reunioes_to_json_chunks(all_data, n_chunks=5)
    results_for_aggregation = get_segments_report(json_chunks)
    final_report = aggregate_reports(results_for_aggregation)
    st.markdown(final_report)


st.button("Generate Report", on_click=generate_report)
