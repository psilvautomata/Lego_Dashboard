import duckdb
import pytest

from pipeline import transformacao


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
    monkeypatch.setattr(transformacao.sys, "stdout", saida)
    monkeypatch.setattr(transformacao.sys, "stderr", erro)
    return saida, erro


def _criar_banco_raw(caminho):
    con = duckdb.connect(str(caminho))
    con.execute("CREATE SCHEMA raw")
    con.execute(
        "CREATE TABLE raw.sets ("
        "set_num VARCHAR, name VARCHAR, year VARCHAR, theme_name VARCHAR, "
        "parent_theme VARCHAR, num_parts VARCHAR, num_minifigs VARCHAR, "
        "num_unique_colors VARCHAR, has_minifigs VARCHAR, img_url VARCHAR)"
    )
    # O primeiro set tem 5000 peças, pai ausente e bonecos ausentes para cobrir regras distintas.
    linha_set_valida = (
        "001-A",
        "Set de teste",
        "2001",
        "Space",
        None,
        "5000",
        None,
        "5",
        "True",
        "url-set",
    )
    # A segunda linha usa um ID alfanumérico e valores inválidos para verificar coerção sem descarte.
    linha_set_irregular = (
        "75419-1",
        "Set histórico",
        "ano-x",
        "Space",
        "Classic",
        "peças-x",
        "bonecos-x",
        "2",
        "Talvez",
        "url-historica",
    )
    con.executemany(
        "INSERT INTO raw.sets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            linha_set_valida,
            linha_set_valida,  # A cópia idêntica prova a deduplicação mantendo a primeira.
            linha_set_irregular,
        ],
    )
    con.execute(
        "CREATE TABLE raw.minifiguras ("
        "fig_num VARCHAR, name VARCHAR, num_parts VARCHAR, img_url VARCHAR, "
        "total_sets_appeared VARCHAR)"
    )
    # O prefixo fig- demonstra que o identificador não vira número.
    con.execute(
        "INSERT INTO raw.minifiguras VALUES ('fig-002229', 'Figura teste', '2', 'url-fig', '1')"
    )
    con.execute(
        "CREATE TABLE raw.temas ("
        "id VARCHAR, theme_name VARCHAR, parent_theme VARCHAR, total_sets VARCHAR)"
    )
    # O tema raiz confirma o preenchimento específico de parent_theme.
    con.execute("INSERT INTO raw.temas VALUES ('101', 'Space', NULL, '2')")
    con.close()


def test_transforma_sem_deduplicar_ids_distintos_e_preserva_nulos_de_erro(
    monkeypatch, tmp_path
):
    caminho_banco = tmp_path / "transformacao.duckdb"
    _criar_banco_raw(caminho_banco)
    monkeypatch.setattr(
        transformacao,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    avisos = []
    monkeypatch.setattr(
        transformacao.LOGGER,
        "warning",
        lambda mensagem, *args: avisos.append(mensagem % args),
    )
    saida, _ = _capturar_terminal(monkeypatch)

    transformacao.main()

    con = duckdb.connect(str(caminho_banco), read_only=True)
    qtd_raw = con.execute("SELECT count(*) FROM raw.sets").fetchone()[0]
    qtd_refined = con.execute("SELECT count(*) FROM refined.sets").fetchone()[0]
    tipos = con.execute(
        "SELECT typeof(ano_lancamento), typeof(possui_minifiguras), typeof(id_set) "
        "FROM refined.sets WHERE id_set = '001-A'"
    ).fetchone()
    set_raiz = con.execute(
        "SELECT id_set, qtd_minifiguras, tema_pai, possui_minifiguras "
        "FROM refined.sets WHERE id_set = '001-A'"
    ).fetchone()
    set_irregular = con.execute(
        "SELECT id_set, ano_lancamento, qtd_pecas, qtd_minifiguras, possui_minifiguras "
        "FROM refined.sets WHERE id_set = '75419-1'"
    ).fetchone()
    pai_tema = con.execute("SELECT tema_pai FROM refined.temas").fetchone()[0]
    id_figura = con.execute("SELECT id_minifigura FROM refined.minifiguras").fetchone()[
        0
    ]
    con.close()

    assert qtd_raw == 3
    assert qtd_refined == 2
    assert tipos == ("BIGINT", "BOOLEAN", "VARCHAR")
    assert set_raiz == ("001-A", 0, "Sem Tema Pai", True)
    assert set_irregular == ("75419-1", None, None, None, None)
    assert pai_tema == "Sem Tema Pai"
    assert id_figura == "fig-002229"
    assert len(avisos) == 4
    assert "refined.sets: 2" in saida.texto
    assert "refined.minifiguras: 1" in saida.texto
    assert "refined.temas: 1" in saida.texto


def test_tabelas_raw_ausentes_interrompem_antes_de_gravar(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "sem_raw.duckdb"
    chamada_gravar = []
    monkeypatch.setattr(
        transformacao,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    monkeypatch.setattr(
        transformacao,
        "gravar",
        lambda *args: chamada_gravar.append(args),
    )
    _, erro = _capturar_terminal(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        transformacao.main()

    assert encerramento.value.code == 1
    assert "raw.sets" in erro.texto
    assert "pipeline.ingestao" in erro.texto
    assert chamada_gravar == []
