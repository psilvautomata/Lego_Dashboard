"""Constrói o schema ``marts`` a partir das consultas em ``sql/marts``.

Regras desta etapa e seus motivos:
- As consultas leem apenas ``refined`` e criam tabelas apenas em ``marts``;
  as camadas raw e refined continuam sendo fontes imutáveis para que as regras
  de negócio permaneçam nos arquivos SQL.
- O schema marts é apagado e recriado dentro de uma única transação. Assim,
  marts removidos do diretório também desaparecem do banco, e uma falha
  restaura integralmente o schema da última execução bem-sucedida.
- Cada arquivo ``marts.<nome>.sql`` corresponde a uma tabela ``marts.<nome>``.
  Os arquivos são executados em ordem alfabética e o Python somente remove
  espaços externos e um ponto e vírgula final antes de envolver a consulta em
  ``CREATE TABLE AS``; a lógica de negócio permanece no SQL.
- Todos os arquivos e nomes de tabela são validados antes de executar as
  consultas. Isso evita execução parcial por nomes inválidos ou duplicados.
- A presença das três tabelas refined é conferida antes de substituir marts,
  para indicar a etapa correta de recuperação sem destruir resultados válidos.
- A contagem de cada tabela vem do banco. Um mart vazio interrompe e reverte
  toda a transação, pois resultado vazio pode parecer um dashboard sem dados.
- Erros de consulta identificam o arquivo responsável e encerram sem executar
  as consultas seguintes. O stdout usa UTF-8 para exibir mensagens no Windows.
"""

import sys
from pathlib import Path

from pipeline.db import conectar, criar_schema

PASTA_SQL = Path(__file__).resolve().parent.parent / "sql" / "marts"
TABELAS_REFINED = ("sets", "minifiguras", "temas")
PREFIXO_ARQUIVO = "marts."


def _validar_arquivos(arquivos):
    invalidos = []
    nomes = {}

    for arquivo in arquivos:
        if not arquivo.stem.startswith(PREFIXO_ARQUIVO):
            invalidos.append(arquivo.name)
            continue

        nome_tabela = arquivo.stem[len(PREFIXO_ARQUIVO) :]
        if not nome_tabela:
            invalidos.append(arquivo.name)
            continue

        chave = nome_tabela.casefold()
        nomes.setdefault(chave, []).append((arquivo.name, nome_tabela))

    duplicados = [entradas for entradas in nomes.values() if len(entradas) > 1]
    return invalidos, duplicados


def _sql_da_consulta(arquivo):
    conteudo = arquivo.read_text(encoding="utf-8").strip()
    if conteudo.endswith(";"):
        conteudo = conteudo[:-1].rstrip()
    return conteudo


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    con = conectar()
    try:
        existentes = {
            linha[0]
            for linha in con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'refined' AND table_type = 'BASE TABLE'"
            ).fetchall()
        }
        faltantes = [tabela for tabela in TABELAS_REFINED if tabela not in existentes]
        if faltantes:
            nomes = ", ".join(f"refined.{tabela}" for tabela in faltantes)
            print(
                f"Tabelas ausentes: {nomes}. "
                "Execute 'uv run python -m pipeline.transformacao' antes desta etapa.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        arquivos = sorted(
            PASTA_SQL.glob("*.sql"), key=lambda arquivo: arquivo.name.casefold()
        )
        if not arquivos:
            print(f"Nenhum arquivo .sql encontrado em {PASTA_SQL}.", file=sys.stderr)
            raise SystemExit(1)

        invalidos, duplicados = _validar_arquivos(arquivos)
        if invalidos or duplicados:
            if invalidos:
                print(
                    "Arquivos devem seguir o padrão marts.<nome>.sql: "
                    + ", ".join(invalidos),
                    file=sys.stderr,
                )
            if duplicados:
                lista = "; ".join(
                    ", ".join(item[0] for item in grupo) for grupo in duplicados
                )
                print(
                    f"Arquivos geram nomes de tabela duplicados: {lista}.",
                    file=sys.stderr,
                )
            raise SystemExit(1)

        con.execute("BEGIN TRANSACTION")
        try:
            con.execute("DROP SCHEMA IF EXISTS marts CASCADE")
            criar_schema(con, "marts")
            total_linhas = 0

            for arquivo in arquivos:
                nome_tabela = arquivo.stem[len(PREFIXO_ARQUIVO) :]
                nome_sql = '"' + nome_tabela.replace('"', '""') + '"'
                try:
                    consulta = _sql_da_consulta(arquivo)
                    con.execute(f"CREATE TABLE marts.{nome_sql} AS {consulta}")
                    quantidade = con.execute(
                        f"SELECT count(*) FROM marts.{nome_sql}"
                    ).fetchall()[0][0]
                    if quantidade == 0:
                        raise ValueError("o mart retornou zero linhas")
                except Exception as erro:  # noqa: BLE001 - qualquer falha SQL precisa reverter a transação.
                    print(f"Erro em {arquivo.name}: {erro}", file=sys.stderr)
                    raise SystemExit(1)

                total_linhas += quantidade
                print(f"✓ marts.{nome_tabela} {quantidade:,} linhas".replace(",", "."))

            con.execute("COMMIT")
            print(
                f"Total: {len(arquivos)} marts, {total_linhas:,} linhas.".replace(
                    ",", "."
                )
            )
        except BaseException:
            con.execute("ROLLBACK")
            raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
