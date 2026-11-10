from pathlib import Path

import duckdb
import pytest

from pipeline import marts


class TerminalBuffer:
    def __init__(self):
        self.texto = ""

    def reconfigure(self, encoding=None):
        self.encoding = encoding

    def write(self, texto):
        self.texto += texto
        return len(texto)

    def flush(self):
        return None


def _capturar_terminal(monkeypatch):
    saida = TerminalBuffer()
    erro = TerminalBuffer()
    monkeypatch.setattr(marts.sys, "stdout", saida)
    monkeypatch.setattr(marts.sys, "stderr", erro)
    return saida, erro


def _preparar_banco(caminho, com_mart_antigo=False):
    con = duckdb.connect(str(caminho))
    con.execute("CREATE SCHEMA refined")
    con.execute("CREATE TABLE refined.sets (id_set VARCHAR)")
    con.execute("CREATE TABLE refined.minifiguras (id_minifigura VARCHAR)")
    con.execute("CREATE TABLE refined.temas (id_tema VARCHAR)")
    if com_mart_antigo:
        con.execute("CREATE SCHEMA marts")
        con.execute("CREATE TABLE marts.antigo AS SELECT 9 AS legado")
    con.close()


def _configurar(monkeypatch, tmp_path, caminho_banco, pasta_sql):
    pasta_sql.mkdir()
    _preparar_banco(caminho_banco)
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )


def test_arquivo_sem_prefixo_marts_interrompe_sem_executar_consulta(
    monkeypatch, tmp_path
):
    caminho_banco = tmp_path / "lego.duckdb"
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    _preparar_banco(caminho_banco, com_mart_antigo=True)
    (pasta_sql / "teste.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    _, erro = _capturar_terminal(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        marts.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    antigas = con.execute("SELECT legado FROM marts.antigo").fetchone()[0]
    novas = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'marts' AND table_name = 'teste'"
    ).fetchone()[0]
    con.close()

    assert encerramento.value.code == 1
    assert "teste.sql" in erro.texto
    assert antigas == 9
    assert novas == 0


def test_nomes_de_tabela_duplicados_sao_rejeitados_antes_da_transacao():
    arquivos = [Path("marts.temas.sql"), Path("marts.TEMAS.sql")]

    invalidos, duplicados = marts._validar_arquivos(arquivos)

    assert invalidos == []
    assert len(duplicados) == 1
    assert {item[0] for item in duplicados[0]} == {
        "marts.temas.sql",
        "marts.TEMAS.sql",
    }


def test_arquivos_que_criam_nome_duplicado_sao_listados_e_interrompem(
    monkeypatch, tmp_path
):
    caminho_banco = tmp_path / "lego.duckdb"
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    _preparar_banco(caminho_banco, com_mart_antigo=True)
    (pasta_sql / "marts.ß.sql").write_text("SELECT 1", encoding="utf-8")
    (pasta_sql / "marts.ss.sql").write_text("SELECT 2", encoding="utf-8")
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    _, erro = _capturar_terminal(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        marts.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    legado = con.execute("SELECT legado FROM marts.antigo").fetchone()[0]
    con.close()

    assert encerramento.value.code == 1
    assert "marts.ß.sql" in erro.texto
    assert "marts.ss.sql" in erro.texto
    assert legado == 9


def test_mart_vazio_reverte_o_schema_anterior(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "lego.duckdb"
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    _preparar_banco(caminho_banco, com_mart_antigo=True)
    (pasta_sql / "marts.vazio.sql").write_text(
        "SELECT id_set AS x FROM refined.sets WHERE 1 = 0",
        encoding="utf-8",
    )
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    _, erro = _capturar_terminal(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        marts.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    legado = con.execute("SELECT legado FROM marts.antigo").fetchone()[0]
    tabela_vazia = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'marts' AND table_name = 'vazio'"
    ).fetchone()[0]
    con.close()

    assert encerramento.value.code == 1
    assert "marts.vazio.sql" in erro.texto
    assert "zero linhas" in erro.texto
    assert legado == 9
    assert tabela_vazia == 0


def test_erro_sql_mostra_arquivo_e_nao_executa_os_seguintes(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "lego.duckdb"
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    _preparar_banco(caminho_banco, com_mart_antigo=True)
    (pasta_sql / "marts.a_erro.sql").write_text("SELECT FROM", encoding="utf-8")
    (pasta_sql / "marts.z_depois.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    _, erro = _capturar_terminal(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        marts.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    legado = con.execute("SELECT legado FROM marts.antigo").fetchone()[0]
    seguinte = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'marts' AND table_name = 'z_depois'"
    ).fetchone()[0]
    con.close()

    assert encerramento.value.code == 1
    assert "marts.a_erro.sql" in erro.texto
    assert legado == 9
    assert seguinte == 0


def test_arquivo_removido_faz_o_mart_desaparecer_na_proxima_execucao(
    monkeypatch, tmp_path
):
    caminho_banco = tmp_path / "lego.duckdb"
    pasta_sql = tmp_path / "sql"
    _configurar(monkeypatch, tmp_path, caminho_banco, pasta_sql)
    arquivo_removido = pasta_sql / "marts.removivel.sql"
    (pasta_sql / "marts.fica.sql").write_text("SELECT 1 AS x; \n", encoding="utf-8")
    arquivo_removido.write_text("SELECT 2 AS y", encoding="utf-8")
    _capturar_terminal(monkeypatch)

    marts.main()
    arquivo_removido.unlink()
    _capturar_terminal(monkeypatch)
    marts.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    tabelas = {
        linha[0]
        for linha in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'marts'"
        ).fetchall()
    }
    valor = con.execute("SELECT x FROM marts.fica").fetchone()[0]
    con.close()

    assert tabelas == {"fica"}
    assert valor == 1


def test_diretorio_sem_sql_encerra_com_erro(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "lego.duckdb"
    pasta_sql = tmp_path / "sql"
    _configurar(monkeypatch, tmp_path, caminho_banco, pasta_sql)
    _, erro = _capturar_terminal(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        marts.main()

    assert encerramento.value.code == 1
    assert "Nenhum arquivo .sql" in erro.texto


def test_tabelas_refined_ausentes_sao_listadas_antes_de_recriar_marts(
    monkeypatch, tmp_path
):
    caminho_banco = tmp_path / "lego.duckdb"
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    con = duckdb.connect(str(caminho_banco))
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.antigo AS SELECT 9 AS legado")
    con.close()
    (pasta_sql / "marts.teste.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    _, erro = _capturar_terminal(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        marts.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    legado = con.execute("SELECT legado FROM marts.antigo").fetchone()[0]
    con.close()

    assert encerramento.value.code == 1
    assert "refined.sets" in erro.texto
    assert "pipeline.transformacao" in erro.texto
    assert legado == 9


def test_consultas_dos_marts_agregam_dados_inventados(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "lego.duckdb"
    con = duckdb.connect(str(caminho_banco))
    con.execute("CREATE SCHEMA refined")
    con.execute(
        "CREATE TABLE refined.sets ("
        "id_set VARCHAR, nome_set VARCHAR, ano_lancamento INTEGER, "
        "nome_tema VARCHAR, tema_pai VARCHAR, qtd_pecas INTEGER, "
        "qtd_cores_unicas INTEGER, qtd_minifiguras INTEGER)"
    )
    con.execute(
        "CREATE TABLE refined.temas ("
        "id_tema VARCHAR, nome_tema VARCHAR, tema_pai VARCHAR, "
        "qtd_total_sets INTEGER)"
    )
    con.execute("CREATE TABLE refined.minifiguras (id_minifigura VARCHAR)")
    # Estes sets inventados permitem conferir volume anual, contagem por tema
    # e a seleção de lançamentos com pelo menos 1.000 peças.
    con.executemany(
        "INSERT INTO refined.sets VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                "set-a",
                "Set Alfa",
                2020,
                "Tema A",
                "Pai A",
                1000,
                2,
                0,
            ),  # Tema A e limite de 1.000 peças.
            (
                "set-b",
                "Set Beta",
                2020,
                "Tema A",
                "Pai A",
                400,
                4,
                1,
            ),  # Segundo set do tema no mesmo ano.
            (
                "set-c",
                "Set Gama",
                2021,
                "Tema B",
                "Pai B",
                2200,
                3,
                0,
            ),  # Outro ano e acima do limite.
        ],
    )
    # IDs de tema inventados validam os joins sem consultar dados reais.
    con.executemany(
        "INSERT INTO refined.temas VALUES (?, ?, ?, ?)",
        [
            (
                "tema-a",
                "Tema A",
                "Pai A",
                2,
            ),  # Correspondência para os dois sets do Tema A.
            (
                "tema-b",
                "Tema B",
                "Pai B",
                1,
            ),  # Correspondência para o set do ano seguinte.
        ],
    )
    con.execute("INSERT INTO refined.minifiguras VALUES ('fig-a')")
    con.close()

    monkeypatch.setattr(marts, "conectar", lambda: duckdb.connect(str(caminho_banco)))
    saida, _ = _capturar_terminal(monkeypatch)
    marts.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    kpis = con.execute(
        "SELECT SUM(total_sets), SUM(total_pecas), "
        "SUM(total_pecas) / SUM(total_sets) FROM marts.kpis "
        "WHERE ano_lancamento BETWEEN 2020 AND 2021"
    ).fetchone()
    evolucao = con.execute(
        "SELECT ano_lancamento, qtd_sets_lancados, volume_total_pecas, "
        "qtd_temas_representados FROM marts.evolucao_anual "
        "ORDER BY ano_lancamento"
    ).fetchall()
    temas = con.execute(
        "SELECT nome_tema, SUM(total_sets) FROM marts.top_temas "
        "GROUP BY nome_tema ORDER BY nome_tema"
    ).fetchall()
    gigantes = con.execute(
        "SELECT id_set FROM marts.ultimos_lancamentos ORDER BY id_set"
    ).fetchall()
    con.close()

    assert kpis == (3, 3600, 1200.0)
    assert evolucao == [(2020, 2, 1400, 1), (2021, 1, 2200, 1)]
    assert temas == [("Tema A", 2), ("Tema B", 1)]
    assert gigantes == [("set-a",), ("set-c",)]
    assert "Total: 5 marts" in saida.texto
