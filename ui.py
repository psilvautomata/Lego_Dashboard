"""Abre no navegador o banco do projeto usando a extensão ``ui`` do DuckDB.

Regras desta etapa e seus motivos:
- O banco é localizado a partir deste arquivo para que o comando funcione
  mesmo quando iniciado de outro diretório.
- O script exige que ``lego.duckdb`` já exista e encerra com código 1 se não
  existir. Isso evita criar e mostrar um banco vazio que pareça uma ingestão
  quebrada; a mensagem orienta rodar a ingestão primeiro.
- A extensão ``ui`` é instalada e carregada, e ``CALL start_ui()`` sobe o
  servidor em ``http://localhost:4213`` e abre o navegador para explorar as
  tabelas do banco.
- O processo permanece vivo para manter a conexão e o servidor disponíveis.
  Ctrl+C fecha a conexão e encerra sem traceback, liberando o lock do arquivo
  para que a ingestão possa rodar logo depois.
- O stdout usa UTF-8 porque o Prompt de Comando do Windows pode embaralhar
  acentos nas mensagens.
- A ingestão não é importada por este módulo, mantendo o servidor e a carga
  separados: a ingestão não sobe navegador nem depende da extensão ``ui``.
"""

import sys
import time
from pathlib import Path

import duckdb


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    caminho_banco = Path(__file__).resolve().parent / "lego.duckdb"

    if not caminho_banco.is_file():
        print(
            f"Banco não encontrado em {caminho_banco}. "
            "Execute a ingestão antes de abrir a interface.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    con = duckdb.connect(str(caminho_banco))
    try:
        con.execute("INSTALL ui;")
        con.execute("LOAD ui;")
        con.execute("CALL start_ui();")
        print("Interface disponível em http://localhost:4213")
        print("Ctrl+C para encerrar")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        con.close()


if __name__ == "__main__":
    main()
