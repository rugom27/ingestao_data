import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

# Carregar variáveis do .env
load_dotenv()

# Obter a URL da base de dados do arquivo .env
DATABASE_URL = os.getenv("DATABASE_URL")


# Conexão com a base de dados
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# Função para obter clientes
def get_clientes():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM clientes ORDER BY name;")
            return cur.fetchall()


# Função para obter produtos
def get_produtos():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT produto_id, ref FROM produtos ORDER BY ref;")
            return cur.fetchall()


# Função para obter últimas reuniões
def get_ultimas_reunioes(cliente_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reunioes WHERE cliente_id = %s",
                (cliente_id,),
                "ORDER BY data_reuniao DESC LIMIT 5;",
            )
            reunioes = cur.fetchall()
            if not reunioes:
                return {"message": "Não existem reuniões para este cliente."}


# Função para adicionar cliente
def add_cliente(cliente_data):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clientes (name, numero_cliente, cod_postal, tipo_cliente, distrito, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
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
                "INSERT INTO produtos (ref) VALUES (%s) RETURNING produto_id;", (ref,)
            )
            conn.commit()
            return cur.fetchone()[0]


# Função para registar reunião
def add_reuniao(reuniao):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            INSERT INTO reunioes (cliente_id, data_reuniao, descricao, houve_venda, produto_id, quantidade_vendida, preco_vendido, razao_nao_venda)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
            cur.close()
            conn.close()
