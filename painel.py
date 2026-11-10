"""Leitura, formatação e figuras puras usadas pelo painel Lego.

Regras desta etapa e seus motivos:
- ler() recebe os nomes dos marts, executa somente um SELECT * por tabela em
  uma conexão DuckDB read-only e fecha a conexão antes de devolver os dados.
  Assim, abrir o painel não mantém o arquivo bloqueado para o pipeline.
- Os marts de KPIs, inventário e temas guardam medidas por ano. aplicar_periodo()
  recompõe esses indicadores no intervalo selecionado; temas ativos são
  contados uma única vez. O Activity Feed usa só o limite superior para listar
  os gigantes mais recentes até o ano escolhido.
- As funções de formatação e de gráficos não acessam banco nem interface web.
  O HTML reaproveita as mesmas figuras e os mesmos formatos sem duplicar
  regras de apresentação.
- As métricas são definidas nos SQLs. Este módulo apenas recompõe as medidas
  anuais no intervalo selecionado e prepara os dados para apresentação; assim,
  o mesmo recorte temporal pode ser aplicado a todos os elementos do painel.
- Milhares e decimais são formatados explicitamente, sem depender do locale da
  máquina, para que os mesmos dados tenham a mesma apresentação em qualquer
  ambiente.
- A distribuição de cores usa ``qtd_cores_unicas`` por set porque a base Lego
  disponível informa quantas cores cada set contém, mas não identifica cores
  individuais. A média de peças por essa contagem mantém a análise no escopo
  das colunas que realmente existem.
"""

import duckdb
import pandas as pd
import plotly.express as px


class MartsAusentes(Exception):
    """Indica quais tabelas do dashboard não foram encontradas."""

    def __init__(self, nomes):
        self.nomes = nomes
        super().__init__(", ".join(nomes))


def ler(marts):
    """Retorna um DataFrame por mart e fecha a conexão após as leituras."""
    con = duckdb.connect("lego.duckdb", read_only=True)
    dados = {}
    faltantes = []
    try:
        for nome in marts:
            try:
                dados[nome] = con.execute(f"SELECT * FROM marts.{nome}").fetchdf()
            except duckdb.CatalogException:
                faltantes.append(f"marts.{nome}")

        if faltantes:
            raise MartsAusentes(faltantes)
        return dados
    finally:
        con.close()


def aplicar_periodo(dados, ano_inicial, ano_final):
    """Filtra todos os marts pelo intervalo e recalcula seus agregados."""
    periodo = {}
    for nome in ("kpis", "evolucao_anual", "inventario_cores", "top_temas"):
        df = dados[nome]
        periodo[nome] = df[df["ano_lancamento"].between(ano_inicial, ano_final)].copy()
    periodo["ultimos_lancamentos"] = dados["ultimos_lancamentos"][
        dados["ultimos_lancamentos"]["ano_lancamento"] <= ano_final
    ].copy()

    kpis_anuais = periodo["kpis"]
    total_sets = int(kpis_anuais["total_sets"].sum())
    sets_com_pecas = int(kpis_anuais["qtd_sets_com_pecas"].sum())
    total_pecas = kpis_anuais["total_pecas"].sum()
    temas_ativos = periodo["top_temas"].drop_duplicates(
        subset=["tema_pai", "nome_tema"]
    )
    periodo["kpis"] = pd.DataFrame(
        [
            {
                "total_sets": total_sets,
                "total_pecas": total_pecas,
                "total_temas": len(temas_ativos),
                "media_pecas": total_pecas / sets_com_pecas if sets_com_pecas else 0,
            }
        ]
    )

    inventario = periodo["inventario_cores"]
    inventario = inventario.groupby("qtd_cores_unicas", as_index=False).agg(
        qtd_sets=("qtd_sets", "sum"),
        qtd_sets_com_pecas=("qtd_sets_com_pecas", "sum"),
        total_pecas=("total_pecas", "sum"),
    )
    inventario["media_pecas"] = (
        inventario["total_pecas"] / inventario["qtd_sets_com_pecas"]
    ).round(1)
    periodo["inventario_cores"] = inventario

    temas = (
        periodo["top_temas"]
        .groupby(["tema_pai", "nome_tema"], as_index=False, dropna=False)
        .agg(
            total_sets=("total_sets", "sum"),
            qtd_ids_tema_catalogo=("qtd_ids_tema_catalogo", "max"),
        )
    )
    temas["tema"] = temas["nome_tema"] + " - " + temas["tema_pai"]
    periodo["top_temas"] = temas.sort_values(
        "total_sets", ascending=False, kind="stable"
    )
    return periodo


def numero(valor, casas=0):
    """Formata milhar com ponto e casas decimais com vírgula."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def pct(valor, casas=1):
    """Acrescenta o símbolo de porcentagem a um valor já expresso em %."""
    return f"{numero(valor, casas)}%"


def grafico_evolucao_anual(df):
    """Cria a série temporal de sets lançados por ano."""
    ordenado = df.sort_values("ano_lancamento", kind="stable")
    figura = px.line(
        ordenado,
        x="ano_lancamento",
        y="qtd_sets_lancados",
        markers=True,
        title="Evolução de Lançamentos",
        labels={
            "ano_lancamento": "Ano",
            "qtd_sets_lancados": "Sets lançados (unidades)",
        },
        color_discrete_sequence=["#0055BF"],
    )
    figura.update_layout(margin={"l": 12, "r": 12, "t": 52, "b": 12})
    return figura


def grafico_sets_por_cores_unicas(df):
    """Compara quantos sets há para cada quantidade de cores únicas."""
    ordenado = df.sort_values("qtd_cores_unicas", kind="stable")
    figura = px.bar(
        ordenado,
        x="qtd_cores_unicas",
        y="qtd_sets",
        title="Sets por Quantidade de Cores Únicas",
        labels={
            "qtd_cores_unicas": "Cores únicas por set",
            "qtd_sets": "Sets (unidades)",
        },
        color_discrete_sequence=["#FFD500"],
    )
    figura.update_layout(margin={"l": 12, "r": 12, "t": 52, "b": 12})
    return figura


def grafico_media_pecas_por_cores_unicas(df):
    """Compara a média de peças pela quantidade de cores únicas do set."""
    ordenado = df.sort_values("qtd_cores_unicas", kind="stable")
    figura = px.bar(
        ordenado,
        x="qtd_cores_unicas",
        y="media_pecas",
        title="Média de Peças por Quantidade de Cores Únicas",
        labels={
            "qtd_cores_unicas": "Cores únicas por set",
            "media_pecas": "Peças médias por set",
        },
        color_discrete_sequence=["#E3000B"],
    )
    figura.update_layout(margin={"l": 12, "r": 12, "t": 52, "b": 12})
    return figura


def grafico_top_temas(df):
    """Mostra os dez temas com mais sets, com o maior no topo."""
    top_dez = df.sort_values("total_sets", ascending=False, kind="stable").head(10)
    figura = px.bar(
        top_dez,
        x="total_sets",
        y="tema",
        orientation="h",
        title="Top Temas por Sets Lançados",
        labels={
            "tema": "Tema",
            "total_sets": "Sets lançados (unidades)",
        },
        color_discrete_sequence=["#0055BF"],
    )
    figura.update_yaxes(categoryorder="total ascending")
    figura.update_layout(margin={"l": 12, "r": 12, "t": 52, "b": 12})
    return figura
