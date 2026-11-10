"""Módulo de conexão compartilhado pelas quatro etapas do curso.

Regras desta etapa e seus motivos:
- PASTA_RAW aponta para ``data/`` (a pasta confirmada neste projeto) e tanto
  ela quanto ``lego.duckdb`` são resolvidos pela localização deste arquivo,
  nunca pelo diretório corrente. Assim executar um script de outra pasta não
  cria um banco vazio no lugar errado nem perde os CSVs.
- A interface pública contém apenas PASTA_RAW, conectar(), criar_schema() e
  gravar(). O módulo não lê CSV, escolhe tabelas, imprime nem converte tipos,
  porque regras escondidas aqui afetariam todas as etapas que o importam.
- gravar() recria a tabela com colunas e tipos do DataFrame, sem alterar valores
  ou nulos, e remove o registro temporário usado na escrita. A contagem vem de
  SELECT count(*) no banco para refletir o que foi persistido.
- conectar() devolve a conexão aberta para quem chamou fechar; não há conexão
  global, para que cada etapa controle seu próprio ciclo de vida.
"""

from pathlib import Path

import duckdb

PASTA_RAW = Path(__file__).resolve().parent.parent / "data"


def conectar():
    """Abre o banco DuckDB na raiz do projeto, criando-o se necessário."""
    caminho_banco = Path(__file__).resolve().parent.parent / "lego.duckdb"
    return duckdb.connect(str(caminho_banco))


def criar_schema(con, nome):
    """Cria o schema se ele ainda não existir."""
    identificador = '"' + nome.replace('"', '""') + '"'
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {identificador}")


def gravar(con, df, schema, tabela):
    """Substitui uma tabela pelo DataFrame e retorna a contagem persistida."""
    schema_sql = '"' + schema.replace('"', '""') + '"'
    tabela_sql = '"' + tabela.replace('"', '""') + '"'
    referencia = f"{schema_sql}.{tabela_sql}"
    nome_temporario = "_pipeline_dataframe_gravar"
    nome_temporario_sql = '"' + nome_temporario + '"'

    con.register(nome_temporario, df)
    try:
        con.execute(
            f"CREATE OR REPLACE TABLE {referencia} AS "
            f"SELECT * FROM {nome_temporario_sql}"
        )
    finally:
        con.unregister(nome_temporario)

    resultado = con.execute(f"SELECT count(*) FROM {referencia}").fetchall()
    return resultado[0][0]
