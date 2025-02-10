import streamlit as st
import psycopg2
from psycopg2 import pool
import pandas as pd
from dotenv import load_dotenv
import os
import time

# Carregar variáveis do .env
load_dotenv()

# Obter a URL da base de dados
DATABASE_URL = os.getenv("DATABASE_URL")


# Criar um pool de conexões (min=1, max=10)
@st.cache_resource
def get_connection_pool():
    """Cria um pool de conexões reutilizáveis."""
    return pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL)


def get_connection():
    """Obtém uma conexão do pool."""
    connection_pool = get_connection_pool()
    return connection_pool.getconn()


def release_connection(conn):
    """Devolve a conexão de volta ao pool."""
    connection_pool = get_connection_pool()
    connection_pool.putconn(conn)


# ---------------------------- Funções de leitura ---------------------------------
def get_clientes():
    """Obtém a lista de clientes."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM clientes ORDER BY name;")
            return cur.fetchall()
    finally:
        release_connection(conn)


def get_max_cliente():
    """Obtém o maior número de cliente."""
    conn = get_connection()
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
    finally:
        release_connection(conn)


def get_produtos():
    """Obtém a lista de produtos."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT produto_id, ref FROM produtos ORDER BY ref;")
            return cur.fetchall()
    finally:
        release_connection(conn)


def get_ultimas_reunioes(cliente_id):
    """Obtém as últimas reuniões de um cliente."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reunioes WHERE cliente_id = %s ORDER BY data_reuniao DESC LIMIT 5;",
                (cliente_id,),
            )
            return cur.fetchall() or []
    finally:
        release_connection(conn)


def get_ultimas_reunioes_geral():
    """Obtém as últimas reuniões de todos os clientes por ordem de criação"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reunioes ORDER BY data_criacao_linha DESC LIMIT 20;"
            )
            return cur.fetchall() or []
    finally:
        release_connection(conn)


# ---------------------------- Funções de escrita ---------------------------------


def add_cliente(cliente_data):
    """Adiciona um novo cliente com transação."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")  # Iniciar transação
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
            cliente_id = cur.fetchone()[0]
            conn.commit()  # Confirmar transação
            return cliente_id
    except Exception as e:
        conn.rollback()  # Reverter em caso de erro
        st.error(f"Erro ao adicionar cliente: {e}")
    finally:
        release_connection(conn)


def add_produto(ref):
    """Adiciona um novo produto com transação."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")
            cur.execute(
                "INSERT INTO produtos (ref, data_criacao_linha) VALUES (%s, NOW()) RETURNING produto_id;",
                (ref,),
            )
            produto_id = cur.fetchone()[0]
            conn.commit()
            return produto_id
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao adicionar produto: {e}")
    finally:
        release_connection(conn)


def add_reuniao(reuniao):
    """Registra uma nova reunião com transação."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")
            cur.execute(
                """
                INSERT INTO reunioes (cliente_id, data_reuniao, descricao, houve_venda, produto_id, 
                quantidade_vendida, preco_vendido, razao_nao_venda, data_criacao_linha, ultima_atualizacao)
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
            st.success("Reunião registada com sucesso!", icon="✅")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao registrar reunião: {e}")
    finally:
        release_connection(conn)


def update_reuniao(
    reuniao_id, descricao, houve_venda, razao_nao_venda, produto_id, quantidade, preco
):
    """Atualiza os detalhes de uma reunião existente com transação."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")
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
                    int(produto_id) if pd.notna(produto_id) else None,
                    int(quantidade) if pd.notna(quantidade) else None,
                    float(preco) if pd.notna(preco) else None,
                    int(reuniao_id),
                ),
            )
            conn.commit()
            st.success("Reunião atualizada com sucesso!", icon="✅")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao atualizar reunião: {e}")
    finally:
        release_connection(conn)
