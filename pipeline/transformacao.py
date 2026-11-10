"""Transforma as tabelas ``raw`` para ``refined`` sem modificar a origem.

Regras desta etapa e seus motivos:
- São lidas as três tabelas raw (``sets``, ``minifiguras`` e ``temas``) e
  gravadas as três correspondentes em refined. Nenhuma fica de fora porque
  todas são essenciais para este domínio enxuto; raw permanece intacto para
  preservar a camada de dados recebidos.
- Os nomes de tabela permanecem em português e as colunas seguem os mapas
  abaixo para padronizar o vocabulário usado nas próximas consultas.
- Anos e contagens viram inteiros, pois são números discretos; o indicador de
  minifiguras vira BOOLEAN nativo. IDs e nomes relacionados a temas ficam como
  VARCHAR porque identificadores Lego podem conter letras e hífens.
- Valores não conversíveis viram nulos e geram aviso no log, sem interromper
  a execução nem descartar o registro histórico.
- Apenas linhas integralmente idênticas são deduplicadas, mantendo a primeira.
  Linhas com a mesma chave e outros valores diferentes permanecem para que
  anomalias sejam tratadas numa camada superior.
- Nulos de origem são mantidos, exceto ``tema_pai`` em sets/temas, preenchido com
  ``Sem Tema Pai`` para que temas raiz apareçam em agrupamentos, e
  ausências originais em ``qtd_minifiguras`` de sets, preenchidas com zero
  porque a ausência indica que o set não contém bonecos. Falhas de conversão
  permanecem nulas, pois são diferentes de uma ausência na origem.
- A existência das três tabelas de origem é conferida antes de qualquer
  gravação para impedir transformação parcial. Cada tabela refined é recriada
  pelo módulo db, tornando a reexecução idempotente.
- A saída mostra a contagem lida do banco e o stdout usa UTF-8 para que os
  acentos sejam exibidos corretamente no Prompt de Comando do Windows.
"""

import logging
import sys

import pandas as pd

from pipeline.db import conectar, criar_schema, gravar

LOGGER = logging.getLogger(__name__)

COLUNAS = {
    "sets": {
        "set_num": "id_set",
        "name": "nome_set",
        "year": "ano_lancamento",
        "theme_name": "nome_tema",
        "parent_theme": "tema_pai",
        "num_parts": "qtd_pecas",
        "num_minifigs": "qtd_minifiguras",
        "num_unique_colors": "qtd_cores_unicas",
        "has_minifigs": "possui_minifiguras",
        "img_url": "url_imagem",
    },
    "minifiguras": {
        "fig_num": "id_minifigura",
        "name": "nome_minifigura",
        "num_parts": "qtd_pecas",
        "img_url": "url_imagem",
        "total_sets_appeared": "qtd_sets_presente",
    },
    "temas": {
        "id": "id_tema",
        "theme_name": "nome_tema",
        "parent_theme": "tema_pai",
        "total_sets": "qtd_total_sets",
    },
}

COLUNAS_INTEIRAS = {
    "sets": (
        "ano_lancamento",
        "qtd_pecas",
        "qtd_minifiguras",
        "qtd_cores_unicas",
    ),
    "minifiguras": ("qtd_pecas", "qtd_sets_presente"),
    "temas": ("qtd_total_sets",),
}


def _converter_inteiro(df, tabela, coluna):
    original = df[coluna]
    ausente_na_origem = original.isna()
    numerico = pd.to_numeric(original, errors="coerce")
    fracionario = numerico.notna() & numerico.mod(1).ne(0)
    falhou = (original.notna() & numerico.isna()) | fracionario

    if falhou.any():
        LOGGER.warning(
            "%s.%s: %d valor(es) não conversível(is) para INTEGER viraram NULL",
            tabela,
            coluna,
            int(falhou.sum()),
        )

    df[coluna] = numerico.mask(fracionario).astype("Int64")
    if tabela == "sets" and coluna == "qtd_minifiguras":
        df.loc[ausente_na_origem, coluna] = 0


def _converter_booleano(df, tabela, coluna):
    original = df[coluna]
    convertido = original.map({"True": True, "False": False})
    falhou = original.notna() & convertido.isna()

    if falhou.any():
        LOGGER.warning(
            "%s.%s: %d valor(es) não conversível(is) para BOOLEAN viraram NULL",
            tabela,
            coluna,
            int(falhou.sum()),
        )

    df[coluna] = convertido.astype("boolean")


def _transformar(tabela, df):
    df = df.drop_duplicates(keep="first").rename(columns=COLUNAS[tabela])

    for coluna in COLUNAS_INTEIRAS[tabela]:
        _converter_inteiro(df, tabela, coluna)

    if tabela == "sets":
        _converter_booleano(df, tabela, "possui_minifiguras")
        df["tema_pai"] = df["tema_pai"].fillna("Sem Tema Pai")
    elif tabela == "temas":
        df["tema_pai"] = df["tema_pai"].fillna("Sem Tema Pai")

    return df


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    con = conectar()
    try:
        existentes = {
            linha[0]
            for linha in con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'raw' AND table_type = 'BASE TABLE'"
            ).fetchall()
        }
        faltantes = [tabela for tabela in COLUNAS if tabela not in existentes]
        if faltantes:
            nomes = ", ".join(f"raw.{tabela}" for tabela in faltantes)
            print(
                f"Tabelas ausentes: {nomes}. "
                "Execute 'python -m pipeline.ingestao' antes desta etapa.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        criar_schema(con, "refined")
        for tabela in COLUNAS:
            df_raw = con.execute(f"SELECT * FROM raw.{tabela}").fetchdf()
            df_refined = _transformar(tabela, df_raw)
            quantidade = gravar(con, df_refined, "refined", tabela)
            print(
                f"refined.{tabela}: {quantidade:,} registros transformados e gravados.".replace(
                    ",", "."
                )
            )
    finally:
        con.close()


if __name__ == "__main__":
    main()
