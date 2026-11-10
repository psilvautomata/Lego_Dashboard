import duckdb
import pandas as pd
import pytest

import painel


def test_numero_e_pct_usam_separadores_portugueses():
    assert painel.numero(2345) == "2.345"
    assert painel.numero(98765.4, casas=1) == "98.765,4"
    assert painel.pct(94.2) == "94,2%"


def test_aplicar_periodo_atualiza_kpis_graficos_e_activity_feed():
    dados = {
        "kpis": pd.DataFrame(
            {
                "ano_lancamento": [2020, 2021],
                "total_sets": [2, 1],
                "qtd_sets_com_pecas": [2, 1],
                "total_pecas": [1400, 2200],
                "media_pecas": [700.0, 2200.0],
            }
        ),
        "evolucao_anual": pd.DataFrame(
            {
                "ano_lancamento": [2020, 2021],
                "qtd_sets_lancados": [2, 1],
                "volume_total_pecas": [1400, 2200],
                "qtd_temas_representados": [1, 1],
            }
        ),
        "inventario_cores": pd.DataFrame(
            {
                "ano_lancamento": [2020, 2020, 2021],
                "qtd_cores_unicas": [2, 4, 2],
                "qtd_sets": [1, 1, 1],
                "qtd_sets_com_pecas": [1, 1, 1],
                "total_pecas": [1000, 400, 2200],
                "media_pecas": [1000.0, 400.0, 2200.0],
            }
        ),
        "top_temas": pd.DataFrame(
            {
                "ano_lancamento": [2020, 2021],
                "tema_pai": ["Pai A", "Pai B"],
                "nome_tema": ["Tema A", "Tema B"],
                "tema": ["Tema A - Pai A", "Tema B - Pai B"],
                "total_sets": [2, 1],
                "qtd_ids_tema_catalogo": [1, 1],
            }
        ),
        "ultimos_lancamentos": pd.DataFrame(
            {
                "ano_lancamento": [2020, 2021],
                "nome_set": ["Set Alfa", "Set Beta"],
                "qtd_pecas": [1000, 2200],
            }
        ),
    }

    periodo = painel.aplicar_periodo(dados, 2020, 2020)

    assert periodo["kpis"].iloc[0].to_dict() == {
        "total_sets": 2,
        "total_pecas": 1400,
        "total_temas": 1,
        "media_pecas": 700.0,
    }
    assert periodo["evolucao_anual"]["ano_lancamento"].tolist() == [2020]
    assert periodo["inventario_cores"][
        ["qtd_cores_unicas", "qtd_sets", "total_pecas", "media_pecas"]
    ].values.tolist() == [[2, 1, 1000, 1000.0], [4, 1, 400, 400.0]]
    assert periodo["top_temas"]["nome_tema"].tolist() == ["Tema A"]
    assert periodo["ultimos_lancamentos"]["nome_set"].tolist() == ["Set Alfa"]

    periodo_com_limite_superior = painel.aplicar_periodo(dados, 2021, 2021)

    assert periodo_com_limite_superior["ultimos_lancamentos"][
        "ano_lancamento"
    ].tolist() == [2020, 2021]


def test_funcoes_de_grafico_devolvem_pontos_para_as_linhas_inventadas():
    # Três anos inventados permitem confirmar que a linha usa todo o DataFrame.
    evolucao = pd.DataFrame(
        {
            "ano_lancamento": [2001, 2002, 2003],
            "qtd_sets_lancados": [2, 3, 1],
        }
    )
    # Cada quantidade de cores é um grupo inventado com uma barra correspondente.
    cores = pd.DataFrame(
        {
            "qtd_cores_unicas": [2, 4, 6],
            "qtd_sets": [5, 3, 2],
            "media_pecas": [12.0, 20.0, 32.0],
        }
    )
    # Os temas de teste têm nomes diferentes para cada linha e não dependem do catálogo real.
    temas = pd.DataFrame(
        {
            "tema": ["Tema A - Pai A", "Tema B - Pai B", "Tema C - Pai C"],
            "total_sets": [9, 5, 2],
        }
    )

    figura_evolucao = painel.grafico_evolucao_anual(evolucao)
    figura_sets_cores = painel.grafico_sets_por_cores_unicas(cores)
    figura_media_cores = painel.grafico_media_pecas_por_cores_unicas(cores)
    figura_temas = painel.grafico_top_temas(temas)

    assert len(figura_evolucao.data[0].x) == len(evolucao)
    assert len(figura_sets_cores.data[0].x) == len(cores)
    assert len(figura_media_cores.data[0].x) == len(cores)
    assert len(figura_temas.data[0].y) == len(temas)


def test_ler_usa_apenas_database_temporario_e_fecha_conexao(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "lego.duckdb"
    con = duckdb.connect(str(caminho_banco))
    con.execute("CREATE SCHEMA marts")
    # A linha inventada verifica a leitura por nome sem recorrer ao banco do projeto.
    con.execute("CREATE TABLE marts.teste AS SELECT 7 AS valor")
    con.close()
    monkeypatch.chdir(tmp_path)

    dados = painel.ler(("teste",))

    assert dados["teste"]["valor"].tolist() == [7]
    gravacao = duckdb.connect(str(caminho_banco))
    gravacao.execute("CREATE TABLE marts.pos_leitura AS SELECT 1 AS valor")
    gravacao.close()
    assert (tmp_path / "lego.duckdb").is_file()


def test_ler_lista_tabelas_marts_ausentes(tmp_path, monkeypatch):
    caminho_banco = tmp_path / "lego.duckdb"
    con = duckdb.connect(str(caminho_banco))
    con.execute("CREATE SCHEMA marts")
    con.close()
    monkeypatch.chdir(tmp_path)

    with pytest.raises(painel.MartsAusentes) as faltas:
        painel.ler(("kpis", "inventario_cores"))

    assert faltas.value.nomes == ["marts.kpis", "marts.inventario_cores"]
