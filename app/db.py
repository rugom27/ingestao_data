import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
import time

# Carregar variáveis do .env
load_dotenv()

# Obter a URL da base de dados
DATABASE_URL = os.getenv("DATABASE_URL")


@st.cache_resource
def get_connection():
    """Retorna uma nova conexão com a base de dados."""
    return psycopg2.connect(DATABASE_URL)


def get_clientes():
    """Obtém a lista de clientes."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM clientes ORDER BY name;")
            return cur.fetchall()


def get_max_cliente():
    """Obtém o maior número de cliente."""
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


def get_produtos():
    """Obtém a lista de produtos."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT produto_id, ref FROM produtos ORDER BY ref;")
            return cur.fetchall()


def get_ultimas_reunioes(cliente_id):
    """Obtém as últimas reuniões de um cliente."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reunioes WHERE cliente_id = %s ORDER BY data_reuniao DESC LIMIT 5;",
                (cliente_id,),
            )
            return cur.fetchall() or []


def add_cliente(cliente_data):
    """Adiciona um novo cliente."""
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
            return cur.fetchone()[0]


def add_produto(ref):
    """Adiciona um novo produto."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO produtos (ref, data_criacao_linha) VALUES (%s, NOW()) RETURNING produto_id;",
                (ref,),
            )
            conn.commit()
            return cur.fetchone()[0]


def add_reuniao(reuniao):
    """Registra uma nova reunião."""
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
            st.success(f"Reunião registada com sucesso!", icon="✅")


def update_reuniao(
    reuniao_id, descricao, houve_venda, razao_nao_venda, produto_id, quantidade, preco
):
    """Atualiza os detalhes de uma reunião existente."""
    with get_connection() as conn:
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
                        int(produto_id) if pd.notna(produto_id) else None,
                        int(quantidade) if pd.notna(quantidade) else None,
                        float(preco) if pd.notna(preco) else None,
                        int(reuniao_id),
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
