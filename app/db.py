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

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME")

DSN = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"


# Criar um pool de conexões (min=1, max=10)
@st.cache_resource
def get_connection_pool():
    """Cria um pool de conexões reutilizáveis."""
    return pool.SimpleConnectionPool(1, 10, dsn=DSN)


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


def get_all_produtos():
    """Obtém todos os produtos."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM produtos ORDER BY ref;")
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


def get_all_reunioes():
    """Obtém todas as reuniões de todos os clientes por ordem de criação"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT 
                        c.name, 
                        r.data_reuniao,  
                        r.houve_venda
                    FROM reunioes r
                    JOIN clientes c ON c.id = r.cliente_id
                    group by c.name,r.houve_venda,r.data_reuniao
                """
            )
            return cur.fetchall() or []
    finally:
        release_connection(conn)


def get_all_reunioes_para_vizualizacao():
    """Obtém todas as reuniões de todos os clientes"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT *
                    FROM reunioes r
                    JOIN clientes c ON c.id = r.cliente_id
                """
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
                INSERT INTO clientes (name, numero_cliente, cod_postal, tipo_cliente, distrito, latitude, longitude, data_criacao_linha,supplier_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
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
                    cliente_data["distribuidor"],
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


# ---------------------------- Funções para Métricas ---------------------------------
def get_taxa_de_conversao():
    """Obtém as taxas de conversão de todas as vendas por distrito"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """ with cte1 as (
                    SELECT c.distrito, count(*) as numero_de_visitas_convertidas
                    FROM reunioes r
                    JOIN clientes c ON c.id = r.cliente_id
                    where houve_venda = 'Sim'
                    group by c.distrito
                ), cte2 as (
                SELECT c.distrito, count(*) as numero_de_visitas
                FROM reunioes r
                JOIN clientes c ON c.id = r.cliente_id
                group by c.distrito
                )

            SELECT cte1.distrito, cte2.numero_de_visitas, cte1.numero_de_visitas_convertidas
            from cte1
            join cte2 on cte1.distrito = cte2.distrito
                """
            )
            return cur.fetchall() or []
    finally:
        release_connection(conn)


# ---------------------------- Funções para leitura de métricas para fornecedores ---------------------------------


def vendas_a_agricultores_para_distribuidores():
    """Quanto é que foi vendido a agricultores e que foi parar a estes distribuidores"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    distribuidor,
                    d.distribuidor_id,
                    COALESCE(SUM((quantidade_vendida*preco_vendido)),0) AS total_vendas
                FROM reunioes r
                full JOIN distribuidores d ON r.supplier_id = d.distribuidor_id
                where distribuidor is not null
                GROUP BY distribuidor_id, distribuidor;
                """
            )
            return cur.fetchall() or []
    finally:
        release_connection(conn)


def vendas_a_distribuidores_2024_relatorio_vendas():
    """Quanto é que foi vendido a distribuidores em 2024. Informação vai ser proveniente do relatório fiscal de vendas a distribuidores"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                with cte_1 as (
                    SELECT nome, EXTRACT(YEAR FROM data) AS ano, SUM(eur) AS total_vendido
                    FROM vendas v
                    GROUP BY nome, EXTRACT(YEAR FROM data))

                    select d.distribuidor,total_vendido 
                    from distribuidores d 
                    join cte_1 on upper(d.distribuidor) = upper(cte_1.nome)
                    where ano = 2024;
                """
            )
            return cur.fetchall() or []
    finally:
        release_connection(conn)


def vendas_a_distribuidores_relatorio_reunioes():
    """Quanto é que foi vendido a distribuidores. Informação vai ser proveniente doa tabela de registo de reuniões"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH lista (name) AS (
                                        VALUES
                                            ('Fertidouro, Lda'),
                                            ('Pereiras & Almeida, Lda.'),
                                            ('Nobre E Azevedo Unipessoal, Lda'),
                                            ('GREMIORITA, PRODUTOS PARA AGRICULTURA, LDA'),
                                            ('Joaquim Domingos Duarte Comba Ribeiro'),
                                            ('Prorural-Produtos Agricolas, Lda'),
                                            ('MANUEL GOMES LOURENÇO, LDA'),
                                            ('ANTÓNIO AUGUSTO LAJA'),
                                            ('NITRILON - AGRÍCOLA, UNIPESSOAL,LDA.'),
                                            ('UFCB - UNIÃO DOS FRUTICULTORES DA COVA DA BEIRA, LDA'),
                                            ('MONCORVAGRI')
                                        ),
                                        vendas_por_cliente AS (
                                        SELECT
                                            c.name,
                                            SUM(r.quantidade_vendida * r.preco_vendido) AS total_vendas
                                        FROM reunioes r
                                        JOIN clientes c 
                                            ON c.id = r.cliente_id
                                        WHERE r.houve_venda = 'Sim'
                                        GROUP BY c.name
                                        )
                                        SELECT
                                        l.name,
                                        COALESCE(v.total_vendas, 0) AS total_vendas
                                        FROM lista l
                                        LEFT JOIN vendas_por_cliente v
                                        ON v.name = l.name
                                        ORDER BY l.name;
                """
            )
            return cur.fetchall() or []
    finally:
        release_connection(conn)
