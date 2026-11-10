"""Ingestão dos três CSVs sem transformar os dados para o schema ``raw``.

Regras desta etapa e seus motivos:
- O mapa literal arquivo/tabela abaixo fixa o schema ``raw`` e os nomes
  ``sets``, ``minifiguras`` e ``temas``; esses nomes formam o vocabulário dos
  JOINs que serão escritos de memória nas próximas aulas.
- Não há conversão de tipos, descarte ou deduplicação de linhas, alteração de
  colunas, nem correção, preenchimento ou normalização de valores. Preservar
  texto e nulos mantém a fronteira entre o dado recebido e o dado tratado em
  ``refined``, na etapa 2.
- A leitura declara UTF-8, usa os CSVs diretamente sem descompactar e força
  ``dtype=str``. Campo vazio continua nulo. Isso evita que inferência leia IDs
  ou códigos de sets como números, perca zeros/letras ou cause erros de parse;
  conversões ficam registradas como decisões da etapa 2.
- Os três arquivos são verificados antes de abrir o banco para que um arquivo
  ausente não produza uma ingestão parcial que pareça válida.
- Cada execução recria as tabelas, nunca acrescenta linhas. Isso permite
  reexecutar a ingestão sem acumular resultados.
- Cada linha de saída usa a contagem consultada no banco, com milhar separado
  por ponto, e a linha final mostra o total. Essa saída é o instrumento de
  conferência desta etapa.
- O stdout usa UTF-8 porque o Prompt de Comando do Windows pode embaralhar
  acentos. Se faltarem arquivos, a mensagem lista os nomes e a pasta
  pesquisada e o processo encerra com código 1 antes de gravar qualquer tabela.
"""

import sys

import pandas as pd

from pipeline.db import PASTA_RAW, conectar, criar_schema, gravar

ARQUIVOS = (
    ("lego_sets_1975_2025.csv", "sets"),
    ("lego_minifigures_1975_2025.csv", "minifiguras"),
    ("lego_themes_1975_2025.csv", "temas"),
)


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    faltantes = [nome for nome, _ in ARQUIVOS if not (PASTA_RAW / nome).is_file()]
    if faltantes:
        print(
            f"Arquivos ausentes em {PASTA_RAW}: " + ", ".join(faltantes),
            file=sys.stderr,
        )
        raise SystemExit(1)

    con = conectar()
    try:
        criar_schema(con, "raw")
        total = 0

        for nome_arquivo, tabela in ARQUIVOS:
            df = pd.read_csv(
                PASTA_RAW / nome_arquivo,
                encoding="utf-8",
                dtype=str,
            )
            quantidade = gravar(con, df, "raw", tabela)
            total += quantidade
            print(f"raw.{tabela}: {quantidade:,}".replace(",", "."))

        print(f"Total: {total:,}".replace(",", "."))
    finally:
        con.close()


if __name__ == "__main__":
    main()
