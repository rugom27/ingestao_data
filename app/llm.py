import os
import json
import math
import requests
from dotenv import load_dotenv
from groq import Groq, GroqError
import concurrent.futures
import streamlit as st
from textblob import TextBlob
import tiktoken

import os, time
from threading import Lock
from typing import Optional


# Replace with your actual DB connection utilities
from db import get_connection, release_connection

load_dotenv()


client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

MODEL_TOKEN_LIMIT = {
    "llama3-70b-8192": 8192,
    "llama3-8b-8192": 8192,
    "llama-3.1-8b-instant": 131072,
    "llama-3.3-70b-versatile": 131072,
    "gemma2-9b-it": 8192,
    "deepseek-r1-distill-llama-70b": 131072,
    "meta-llama/llama-4-maverick-17b-128e-instruct": 131072,
    "meta-llama/llama-4-scout-17b-16e-instruct": 131072,
    "meta-llama/Llama-Guard-4-12B": 128,
}

MODEL_ENCODINGS = {"deepseek-r1-distill-llama-70b": "cl100k_base"}


# DeepSeek limits
TOKENS_PER_MIN = 6_000
REQS_PER_MIN = 30

# Internal state for throttling
_token_lock = Lock()
_window_start_ts = time.time()
_tokens_in_window: int = 0
_reqs_in_window: int = 0

# One encoder, reused
ENC = tiktoken.get_encoding("cl100k_base")


def _renew_window() -> None:
    """Resets counters if 60s have elapsed since window start."""
    global _window_start_ts, _tokens_in_window, _reqs_in_window
    if time.time() - _window_start_ts >= 60:
        _window_start_ts = time.time()
        _tokens_in_window = 0
        _reqs_in_window = 0


def call_groq(
    prompt: str,
    *,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    retries: int = 3,
) -> str:
    """
    DeepSeek-specific Groq wrapper.
    • Guarantees ≤30 calls/min  AND  ≤6 000 tokens/min
    • Retries with exponential back-off.
    """
    global _tokens_in_window, _reqs_in_window

    request_tokens = len(ENC.encode(prompt)) + max_tokens

    for attempt in range(retries):
        with _token_lock:
            _renew_window()

            # If this request would exceed either limit, calculate wait
            excess_tokens = max(0, _tokens_in_window + request_tokens - TOKENS_PER_MIN)
            excess_reqs = max(0, _reqs_in_window + 1 - REQS_PER_MIN)

            # time needed to clear excess (in seconds)
            wait_secs = 0.0
            if excess_tokens > 0:
                wait_secs = max(wait_secs, 60 * excess_tokens / TOKENS_PER_MIN)
            if excess_reqs > 0:
                wait_secs = max(wait_secs, 60 * excess_reqs / REQS_PER_MIN)

            if wait_secs:
                time.sleep(wait_secs)
                _renew_window()  # window may have rolled over while we slept

            # book-keep
            _tokens_in_window += request_tokens
            _reqs_in_window += 1

        # ---- make the call --------------------------------------------------
        try:
            r = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="deepseek-r1-distill-llama-70b",
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return r.choices[0].message.content.strip()

        except GroqError as e:
            if attempt == retries - 1:
                raise
            backoff = 2**attempt
            time.sleep(backoff)


def fetch_reunioes():
    sql = """
    SELECT c.id, cliente_id, name AS client_name, data_reuniao, descricao, houve_venda,
           ref AS product_name, quantidade_vendida, preco_vendido AS preco_unitario,
           razao_nao_venda, distrito, cultura, area_culturas
    FROM reunioes r
    JOIN clientes c ON c.id = r.cliente_id
    JOIN produtos p ON p.produto_id = r.produto_id
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


def preprocess_sentiment(df):
    df["sentiment"] = df["descricao"].apply(
        lambda x: (
            "Positive"
            if TextBlob(x).sentiment.polarity > 0.2
            else "Negative" if TextBlob(x).sentiment.polarity < -0.2 else "Neutral"
        )
    )
    return df


def get_segments_report(json_chunks):
    segment_reports = []
    try:
        for idx, chunk in enumerate(json_chunks, 1):
            prompt = f"""
            You are a business insights assistant for an agricultural sales team (specializing in crop protection/fertilizers).

            Given the following data segment - number {idx}:
            ```json
            {chunk}
            ```
            Analyze this regional meeting data to help a field sales representative understand their client base and optimize their sales strategy. Structure your analysis into the following sections:

            1. **Client Relationship (CRM) Analysis**
            - Identify high-potential clients (e.g., multiple meetings, product interest, recent purchases).
            - Detect churn-risk clients (e.g., frequent “no sale”, negative tone, objections).
            - Quantify: number of clients per category with justification (include `cliente_id`).

            2. **Strategic Product Opportunities**
            - Identify cross-selling opportunities based on product patterns and client needs.
            - Spot emerging demands or unaddressed problems from meeting descriptions.
            - Highlight potential new markets or crops.

            3. **Sales Team Effectiveness**
            - Evaluate meeting productivity (e.g., % with successful sales).
            - Identify effective behaviors (phrases, tone, product combos).
            - Recommend areas of improvement.

            4. **NLP & Sentiment Insights**
            - Perform sentiment analysis on `descricao` fields (Positive, Neutral, Negative).
            - Extract most common topics (e.g., pests, crop types, treatment concerns).
            - Detect competitor mentions or rival product references.
            - Summarize frequency metrics and patterns.

            5. **Predictive Signals**
            - Based on descriptions and behavior, infer next steps for top clients.
            - Suggest personalized engagement strategies and timing.
            - Highlight clients that may require urgent follow-up.

            > Use markdown formatting with clear bullet points, tables, and subtitles. Write in professional, fluent English. Make results suitable for dashboards or client strategy reports.

            """

            answer = call_groq(prompt)
            segment_reports.append(answer)
        return segment_reports
    except Exception as e:
        st.error(f"Error fetching insights for segment {idx}: {e}")


def aggregate_reports(results_for_aggregation):
    prompt = f"""
    Comprehensive Final Report:

    ```json
    {json.dumps(results_for_aggregation, ensure_ascii=False, indent=2)}
    ```

    Produce a comprehensive and executive-level report that will be used by commercial managers. Organize the content as follows:

    1. **Insight Consolidation**
    - Deduplicate and merge overlapping findings.
    - Highlight the strongest and most consistent signals across regions.

    2. **Client Relationship Summary**
    - Total and % of high-potential clients vs churn-risk clients.
    - Regional client behavior patterns, if visible.
    - Actionable follow-ups with `cliente_id`.

    3. **Strategic Product Opportunities**
    - Top cross-sell matches by product or crop.
    - New product opportunities by client type or culture.
    - Quantify top 3 opportunities.

    4. **Sales Team Performance**
    - Overall meeting success rate (% of "houve_venda").
    - Patterns in high/low performing reps or regions (if visible).
    - Training or behavior-based recommendations.

    5. **NLP & Sentiment Overview**
    - Sentiment distribution (Positive/Neutral/Negative %).
    - Most frequent pain points or keywords.
    - Competitor references (frequency and tone).

    6. **Forecasting & Engagement Actions**
    - Predict client behavior (seasonality, needs).
    - List next steps by client tier (high-potential vs churn-risk).
    - Suggested talking points or timing for engagement.

    > Write concisely in bullet points and section headers. Use markdown formatting. Avoid redundancy. Deliver actionable insights ready to inform sales strategy. Write in professional, fluent Portuguese (PT-PT).

    """
    return call_groq(prompt, max_tokens=4096)


# ---------------------------------------------------------------------------------------------------------------------------------


def fetch_reunioes_por_distrito():
    sql = """
    SELECT distrito, json_agg(json_build_object(
        'cliente_id', cliente_id,
        'client_name', name,
        'data_reuniao', data_reuniao,
        'descricao', descricao,
        'houve_venda', houve_venda,
        'product_name', ref,
        'quantidade_vendida', quantidade_vendida,
        'preco_unitario', preco_vendido,
        'razao_nao_venda', razao_nao_venda,
        'cultura', cultura,
        'area_culturas', area_culturas
    )) AS reunioes
    FROM reunioes r
    JOIN clientes c ON c.id = r.cliente_id
    JOIN produtos p ON p.produto_id = r.produto_id
    GROUP BY distrito;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return {row[0]: row[1] for row in rows}
    finally:
        release_connection(conn)


def fetch_reunioes_por_cliente(cliente_id):
    sql = f"""
    SELECT distrito, json_agg(json_build_object(
        'cliente_id', cliente_id,
        'client_name', name,
        'data_reuniao', data_reuniao,
        'descricao', descricao,
        'houve_venda', houve_venda,
        'product_name', ref,
        'quantidade_vendida', quantidade_vendida,
        'preco_unitario', preco_vendido,
        'razao_nao_venda', razao_nao_venda,
        'cultura', cultura,
        'area_culturas', area_culturas
    )) AS reunioes
    FROM reunioes r
    JOIN clientes c ON c.id = r.cliente_id
    JOIN produtos p ON p.produto_id = r.produto_id
    WHERE cliente_id = {cliente_id}
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return {row[0]: row[1] for row in rows}
    finally:
        release_connection(conn)


# Gerar relatórios segmentados por distrito


def analyze_districts(district_data):
    def analyze_district(district, data):
        prompt = f"""
        Region: {district}
        ```json
        {json.dumps(data, ensure_ascii=False)}
        ```
        Act as a strategic assistant for a sales representative in the agrochemical sector, analyzing CRM data for a specific region. The data includes meeting descriptions, sales outcomes, product details, timestamps, and customer IDs.

        Provide a structured and quantified analysis for the selected region, focusing on the following:

        1. **Customer Profile:** Identify customers with high purchasing potential (e.g., frequent interactions, past purchases, positive interest) and those at high risk of churn (e.g., multiple “no sale” entries, absence of recent purchases, or recurring objections). Quantify how many customers fall into each category and briefly explain why.

        2. **Product Strategy Insights:** Highlight cross-selling opportunities based on patterns in product discussions and customer needs. Identify promising new market areas from topics found in the meeting descriptions. Quantify key opportunities and match them to customer IDs.

        3. **Sales Team Performance:** Evaluate the frequency and quality of meetings. Identify high-performing interactions (e.g., those that result in sales or show positive sentiment) and suggest areas of improvement. Include metrics such as the percentage of meetings that led to sales.

        4. **Sentiment & NLP Analysis:** Conduct a sentiment analysis of the meeting descriptions. Identify recurring topics (e.g., crops, pests, concerns), sentiment trends (positive/neutral/negative), and specific mentions of competitors or rival brands. Provide a concise breakdown of frequency and tone.

        5. **Predictive Insights:** Forecast future customer needs or risks based on description patterns, seasonality, and frequently mentioned challenges. Recommend actionable engagement strategies for each insight.

        Format the output clearly using markdown with sections, bullet points, and tables where helpful. Use professional, concise English. Structure your writing in a way that makes the results ready to be integrated into dashboards or shared in business updates.

        **My Communication Style Summary:**

        * Analytical, structured, and action-oriented.
        * Prefers clear, quantifiable insights over vague summaries.
        * Uses natural but professional language.
        * Prioritizes practical outputs for commercial use in sales planning.
        > Write concisely in bullet points and section headers. Use markdown formatting. Avoid redundancy. Deliver actionable insights ready to inform sales strategy. Write in professional, fluent Portuguese (PT-PT).
        """
        return call_groq(prompt)

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(analyze_district, district, data): district
            for district, data in district_data.items()
        }
        for future in concurrent.futures.as_completed(futures):
            district = futures[future]
            try:
                insights = future.result()
                results[district] = insights
            except Exception as e:
                st.error(f"Erro na análise do distrito {district}: {e}")
    return results
