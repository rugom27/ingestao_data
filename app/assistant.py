import json
import streamlit as st
import pandas as pd

from llm import (
    fetch_reunioes,
    reunioes_to_json_chunks,
    get_segments_report,
    aggregate_reports,
    fetch_reunioes_por_distrito,
    analyze_districts,
    preprocess_sentiment,
)
from db import (
    insert_llm_general_report,
    insert_llm_regional_report,
    get_last_general_report,
    get_last_regional_report,
)

# ─── Configuration ─────────────────────────────────────────────────────────────

MODEL_OPTIONS = {
    "LLaMA 3 - 70B (8K)": "llama3-70b-8192",
    "LLaMA 3 - 8B (8K)": "llama3-8b-8192",
    "LLaMA 3.1 - 8B Instant (128K)": "llama-3.1-8b-instant",
    "LLaMA 3.3 - 70B Versatile (128K)": "llama-3.3-70b-versatile",
    "Gemma 2 - 9B (8K)": "gemma2-9b-it",
    "DeepSeek - 70B (128K)": "deepseek-r1-distill-llama-70b",
    "LLaMA 4 - Maverick 17B (128K)": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "LLaMA 4 - Scout 17B (16K)": "meta-llama/llama-4-scout-17b-16e-instruct",
    "LLaMA 4 - Guard 12B": "meta-llama/Llama-Guard-4-12B",
}

# ─── Caching DB calls ──────────────────────────────────────────────────────────


@st.cache_data(show_spinner=False)
def load_general_data():
    return fetch_reunioes()


@st.cache_data(show_spinner=False)
def load_regional_data():
    return fetch_reunioes_por_distrito()


# ─── Shared UI helpers ─────────────────────────────────────────────────────────


def show_last_report(getter_fn, empty_msg: str):
    records = getter_fn()
    df = pd.DataFrame(records, columns=["id", "created_at", "type", "report"])
    if df.empty:
        st.error(empty_msg)
    else:
        st.markdown(df.loc[0, "report"])


# ─── App entrypoint ────────────────────────────────────────────────────────────
st.title("🔎 Análise de Reuniões com Clientes")

# — Model selector —
model_name = st.selectbox(
    "Escolha o modelo LLM",
    options=list(MODEL_OPTIONS.keys()),
    index=0,
    help="Selecione o LLM que melhor se adapta ao seu caso de uso.",
)
model_id = MODEL_OPTIONS[model_name]

tab1, tab2 = st.tabs(["📝 Relatório Geral", "🌐 Relatório por Região"])

# ── Tab 1: General Report ────────────────────────────────────────────────
with tab1:
    with st.form("general_report_form"):
        generate = st.form_submit_button("Gerar Relatório Geral")
        fetch_last = st.form_submit_button("Obter Último Relatório Geral")

    if generate:
        with st.spinner("🔄 Gerando relatório geral…"):
            try:
                # 1) Load & preprocess
                data = load_general_data()
                df = pd.DataFrame(data)
                df = preprocess_sentiment(df)

                # 2) Chunk & LLM
                chunks = reunioes_to_json_chunks(df.to_dict(orient="records"))
                segment_reports = get_segments_report(chunks, model_id)

                # 3) Aggregate & persist
                final_report = aggregate_reports(segment_reports)
                insert_llm_general_report(final_report)

                st.success("✅ Relatório gerado com sucesso!")
                st.markdown(final_report)

            except Exception as e:
                st.error(f"❗ Erro ao gerar relatório geral: {e}")

    if fetch_last:
        with st.spinner("⏳ Carregando último relatório…"):
            show_last_report(
                get_last_general_report, "Nenhum relatório geral disponível."
            )

# ── Tab 2: Regional Report ───────────────────────────────────────────────
with tab2:
    with st.form("regional_report_form"):
        generate_r = st.form_submit_button("Gerar Relatório por Região")
        fetch_last_r = st.form_submit_button("Obter Último Relatório Regional")

    if generate_r:
        with st.spinner("🔄 Gerando relatório regional…"):
            try:
                # 1) Load per-district data
                reg_data = load_regional_data()

                # 2) Analyze & persist
                district_reports = analyze_districts(reg_data, model_id)
                insert_llm_regional_report(district_reports)

                # 3) Display each district
                for district, report in district_reports.items():
                    st.subheader(f"📍 Região: {district}")
                    st.markdown(report)
                    st.divider()

            except Exception as e:
                st.error(f"❗ Erro ao gerar relatório regional: {e}")

    if fetch_last_r:
        with st.spinner("⏳ Carregando último relatório regional…"):
            show_last_report(
                get_last_regional_report, "Nenhum relatório regional disponível."
            )
