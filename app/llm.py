import os
import json
import math
import requests
from dotenv import load_dotenv
from groq import Groq

# Replace with your actual DB connection utilities
from db import get_connection, release_connection

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


def call_groq(
    prompt: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """
    Send a completion request to the Groq API and return the generated text.
    """
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return chat_completion.choices[0].message.content.strip()


def fetch_reunioes():
    """Fetch all meetings joined with client & product info."""
    sql = """
    SELECT 
        c.id,
        cliente_id,
        name            AS client_name,
        data_reuniao,
        descricao,
        houve_venda,
        ref             AS product_name,
        quantidade_vendida,
        preco_vendido   AS preco_unitario,
        razao_nao_venda,
        distrito,
        cultura,
        area_culturas
    FROM reunioes r
    JOIN clientes c  ON c.id          = r.cliente_id
    JOIN produtos p  ON p.produto_id  = r.produto_id
    ORDER BY r.data_criacao_linha DESC;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return [dict(zip(cols, row)) for row in rows]
    finally:
        release_connection(conn)


def reunioes_to_json_chunks(data: list, n_chunks: int = 5) -> list[str]:
    """
    Split the list of meetings into `n_chunks` JSON-encoded strings.
    """
    total = len(data)
    chunk_size = math.ceil(total / n_chunks)
    chunks = []
    for i in range(n_chunks):
        start = i * chunk_size
        end = start + chunk_size
        subset = data[start:end]
        chunks.append(json.dumps(subset, default=str, ensure_ascii=False))
    return chunks


# Step 1: Load & chunk the data

# Step 2: Analyze each chunk independently


def get_segments_report(json_chunks):
    results_for_aggregation = []
    for idx, chunk in enumerate(json_chunks, start=1):
        prompt = f"""
                        Data Segment {idx}:

                        ```json
                        {chunk}
                        Analyze this segment and provide insights on:

                        Client Relationship Management (CRM):

                        High-potential clients and churn risk signals. Explain why you chose them. 

                        Strategic Product Insights:

                        Cross-selling opportunities and new market prospects.

                        Sales Team Performance:

                        Evaluation of meeting effectiveness and suggested improvements.
                        
                        Predictive Insights & Recommendations:

                        Forecasted client needs and proactive engagement measures.

                        Please mark key insights clearly for later aggregation. """

        print(f"Submitting Segment {idx} to Groq…")
        segment_insights = call_groq(prompt)
        print(f"--- Insights for Segment {idx} ---")
        print(segment_insights, "\n")
        results_for_aggregation.append(segment_insights)
        return results_for_aggregation


def aggregate_reports(results_for_aggregation):
    """
    Aggregate the insights from all segments into a comprehensive report."""

    aggregator_prompt = f"""
    Aggregator Prompt: Comprehensive Final Report

    You have the following individual segment insights (1-5):

    {json.dumps(results_for_aggregation, ensure_ascii=False, indent=2)}

    Please synthesize into a single, professional report structured as follows:

    Insight Consolidation: Merge overlapping findings.

    CRM Summary: Prioritized high-potential clients & churn risks.

    Strategic Product Insights: Top cross-sell targets and new markets.

    Sales Team Performance: Cohesive recommendations for meeting improvements.

    Competitive & Market Intelligence: Integrated competitor analysis.

    Predictive Insights: Actionable forecasts with specific client/product/district/crop references.

    Format the output with clear headings, bullet points, and prioritized action items for immediate implementation. """

    print("Submitting Aggregator Prompt to Groq…")
    final_report = call_groq(aggregator_prompt, max_tokens=4096)
    print("\n=== Final Consolidated Report ===\n")
    print(final_report)
    return final_report
