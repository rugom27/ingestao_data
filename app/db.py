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
# Conexão com a base de dados
@st.cache_resource  # caching decorator para evitar a repetição de conexão
def get_connection():
    global conn  # Usa a variável global
    if (
        conn is None or conn.closed != 0
    ):  # Se não existir ou estiver fechada, cria nova conexão
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn


# Fechar conexão à base de dados
def close_connection():
    global conn
    if conn and conn.closed == 0:
        conn.close()
        conn = None  # Reinicia a conexão global
        st.success("🔴 Conexão com a base de dados fechada com sucesso! 🔴")
        st.rerun()  # Atualiza a página imediatamente
    else:
        st.sidebar.warning("⚠️ Nenhuma ligação ativa para fechar.")


def get_connection_back():
    """Abre uma conexão à db"""
    global conn
    if conn is None or conn.closed != 0:
        try:
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            st.sidebar.success("🟢 Ligação estabelecida com sucesso!")
            st.rerun()  # Atualiza a página imediatamente
        except Exception as e:
            st.sidebar.error(f"❌ Erro ao ligar à base de dados: {e}")
    else:
        st.sidebar.warning("⚠️ A conexão já está aberta.")


# -----------------------FUNÇÕES DA BASE DE DADOS-------------------------------
# Função para obter clientes
@st.cache_data  # caching decorator
def get_clientes():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM clientes ORDER BY name;")
            return cur.fetchall()


# Função para obter o maior número de cliente numérico
@st.cache_data
def get_max_cliente():
    try:
        with get_connection() as conn:
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
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT produto_id, ref FROM produtos ORDER BY ref;")
            return cur.fetchall()


# Função para obter últimas reuniões de um determinado cliente
def get_ultimas_reunioes(cliente_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reunioes WHERE cliente_id = %s ORDER BY data_reuniao DESC LIMIT 5;",
                (cliente_id,),
            )
            reunioes = cur.fetchall()
            return reunioes if reunioes else []


# Função para adicionar cliente
def add_cliente(cliente_data):
    with get_connection() as conn:
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
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO produtos (ref,data_criacao_linha) VALUES (%s, NOW()) RETURNING produto_id;",
                (ref,),
            )
            conn.commit()
            return cur.fetchone()[0]


# Função para registar reunião
def add_reuniao(reuniao):
    with get_connection() as conn:
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
    conn = get_connection()
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
    conn = get_connection()
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
