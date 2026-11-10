import importlib

import duckdb
import pandas as pd

from pipeline import db


def test_importar_modulo_nao_abre_banco(monkeypatch, tmp_path):
    def falhar_se_conectar(*args, **kwargs):
        raise AssertionError("importar db.py não deve abrir uma conexão")

    monkeypatch.setattr(db.duckdb, "connect", falhar_se_conectar)
    monkeypatch.setattr(db, "__file__", str(tmp_path / "pipeline" / "db.py"))

    importlib.reload(db)

    assert not (tmp_path / "lego.duckdb").exists()


def test_conectar_usa_raiz_do_modulo_fora_do_diretorio_corrente(monkeypatch, tmp_path):
    raiz = tmp_path / "projeto"
    pasta_pipeline = raiz / "pipeline"
    pasta_pipeline.mkdir(parents=True)
    pasta_execucao = tmp_path / "outra_pasta"
    pasta_execucao.mkdir()
    monkeypatch.setattr(db, "__file__", str(pasta_pipeline / "db.py"))
    monkeypatch.chdir(pasta_execucao)

    con = db.conectar()
    con.close()

    assert (raiz / "lego.duckdb").is_file()
    assert not (pasta_execucao / "lego.duckdb").exists()


def test_gravar_recria_tabela_preserva_texto_nulo_e_conta_banco(tmp_path):
    con = duckdb.connect(str(tmp_path / "db.duckdb"))
    db.criar_schema(con, "refined")
    df = pd.DataFrame(
        {
            # IDs alfanuméricos e o nulo confirmam que gravar não transforma valores.
            "id": ["001-A", "fig-2", None],
            "nome": ["set", "figura", "tema"],
        }
    )

    primeira_contagem = db.gravar(con, df, "refined", "exemplo")
    segunda_contagem = db.gravar(con, df, "refined", "exemplo")
    tipos = con.execute(
        "SELECT typeof(id), typeof(nome) FROM refined.exemplo LIMIT 1"
    ).fetchone()
    nulos = con.execute(
        "SELECT count(*) FROM refined.exemplo WHERE id IS NULL"
    ).fetchone()[0]
    temporarias = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_name = '_pipeline_dataframe_gravar'"
    ).fetchone()[0]
    con.close()

    assert primeira_contagem == 3
    assert segunda_contagem == 3
    assert tipos == ("VARCHAR", "VARCHAR")
    assert nulos == 1
    assert temporarias == 0
