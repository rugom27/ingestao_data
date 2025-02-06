import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
import re
import time

# Carregar variáveis do .env
load_dotenv()

# Obter a URL da base de dados do arquivo .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Criar conexão global ao iniciar a aplicação
conn = None  # Variável global para armazenar a conexão


# -----------------------CONEXÃO BASE DE DADOS-------------------------------
@st.cache_resource
def get_connection():
    """Abre a conexão e mantém em cache."""
    return psycopg2.connect(DATABASE_URL)


def open_connection():
    """Força a abertura de uma nova conexão e atualiza a variável global."""
    global conn
    try:
        conn = get_connection()  # Obtém a conexão do cache
        st.sidebar.success("🟢 Ligação realizada com sucesso! 🟢")
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao ligar à base de dados: {e}")


def close_connection():
    """Fecha a conexão e reseta a variável global."""
    global conn
    if conn is not None:
        conn.close()
        conn = None
        st.sidebar.success("🔴 Conexão com a base de dados fechada com sucesso! 🔴")
    else:
        st.sidebar.warning("⚠️ Nenhuma ligação ativa para fechar.")


# -----------------------FUNÇÕES DA BASE DE DADOS-------------------------------
# Função para obter clientes
@st.cache_data  # caching decorator
def get_clientes():
    global conn
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM clientes ORDER BY name;")
        return cur.fetchall()


# Função para obter o maior número de cliente numérico
@st.cache_data
def get_max_cliente():
    global conn
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT numero_cliente FROM clientes;")
            return cur.fetchall()
    except psycopg2.InterfaceError:
        st.error("Erro: Conexão com a base de dados foi fechada inesperadamente.")
        return "Erro"
    except Exception as e:
        st.error(f"Erro ao obter número máximo de cliente: {e}")
        return "Erro"


# Função para obter produtos
def get_produtos():
    global conn
    with conn.cursor() as cur:
        cur.execute("SELECT produto_id, ref FROM produtos ORDER BY ref;")
        return cur.fetchall()


# Função para obter últimas reuniões de um determinado cliente
def get_ultimas_reunioes(cliente_id):
    global conn
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM reunioes WHERE cliente_id = %s ORDER BY data_reuniao DESC LIMIT 5;",
            (cliente_id,),
        )
        reunioes = cur.fetchall()
        return reunioes if reunioes else []


# Função para adicionar cliente
def add_cliente(cliente_data):
    global conn
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO clientes (name, numero_cliente, cod_postal, tipo_cliente, distrito, latitude, longitude, data_criacao_linha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id;
            """,
            (
                cliente_data["name"],
                cliente_data["numero_cliente"],
                cliente_data["cod_postal"],
                cliente_data["tipo_cliente"],
                cliente_data["distrito"],
                cliente_data["latitude"],
                cliente_data["longitude"],
            ),
        )
        conn.commit()
        return cur.fetchone()["id"]


# Função para adicionar produto
def add_produto(ref):
    global conn
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO produtos (ref,data_criacao_linha) VALUES (%s, NOW()) RETURNING produto_id;",
            (ref,),
        )
        conn.commit()
        return cur.fetchone()[0]


# Função para registar reunião
def add_reuniao(reuniao):
    global conn
    with conn.cursor() as cur:
        cur.execute(
            """
        INSERT INTO reunioes (cliente_id, data_reuniao, descricao, houve_venda, produto_id, quantidade_vendida, preco_vendido, razao_nao_venda, data_criacao_linha, ultima_atualizacao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """,
            (
                reuniao["cliente_id"],
                reuniao["data_reuniao"],
                reuniao["descricao"],
                reuniao["houve_venda"],
                reuniao["produto_id"],
                reuniao["quantidade_vendida"],
                reuniao["preco_vendido"],
                reuniao["razao_nao_venda"],
            ),
        )
        conn.commit()
        st.success(
            f"Venda produto: {reuniao["produto_id"]} registada com sucesso!",
            icon="✅",
        )


# Função para obter reuniões de um cliente
def get_ultimas_reunioes(cliente_id):
    global conn
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reunioes WHERE cliente_id = %s ORDER BY data_reuniao DESC;",
                (cliente_id,),
            )
            reunioes = cur.fetchall()
            return reunioes if reunioes else []
    except Exception as e:
        st.error(f"Erro ao buscar reuniões: {e}")
        return []


# Função para atualizar reuniões
def update_reuniao(
    reuniao_id, descricao, houve_venda, razao_nao_venda, produto_id, quantidade, preco
):
    global conn
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE reunioes
                SET descricao = %s, houve_venda = %s, razao_nao_venda = %s,
                    produto_id = %s, quantidade_vendida = %s, preco_vendido = %s,
                    ultima_atualizacao = NOW()
                WHERE id = %s
                """,
                (
                    descricao,
                    houve_venda,
                    razao_nao_venda,
                    (
                        int(produto_id) if pd.notna(produto_id) else None
                    ),  # Conversão segura
                    (
                        int(quantidade) if pd.notna(quantidade) else None
                    ),  # Conversão segura
                    float(preco) if pd.notna(preco) else None,  # Conversão segura
                    int(reuniao_id),  # ID da reunião convertido para inteiro
                ),
            )
            conn.commit()
            with st.status("A modificar os dados...", expanded=True) as status:
                st.write("A verificar alterações...")
                time.sleep(1)
                st.write("Alterações identificadas.")
                time.sleep(1)
                st.write("A processar modificações...")
                time.sleep(1)
                status.update(
                    label="Modificações concluídas com sucesso!",
                    state="complete",
                    expanded=False,
                )
    except Exception as e:
        st.error(f"Erro ao atualizar reunião: {e}")
