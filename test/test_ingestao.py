import duckdb
import pytest

from pipeline import ingestao


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
    monkeypatch.setattr(ingestao.sys, "stdout", saida)
    monkeypatch.setattr(ingestao.sys, "stderr", erro)
    return saida, erro


def _criar_csvs(pasta):
    # Este set inclui um ID com hífen e parent_theme vazio para conferir a ingestão literal.
    (pasta / "lego_sets_1975_2025.csv").write_text(
        "set_num,name,year,theme_name,parent_theme,num_parts,num_minifigs,"
        "num_unique_colors,has_minifigs,img_url\n"
        "001-A,Space Set,2001,Space,,20,1,3,True,url-set\n",
        encoding="utf-8",
    )
    # Esta figura pequena é suficiente para confirmar o mapeamento da segunda tabela.
    (pasta / "lego_minifigures_1975_2025.csv").write_text(
        "fig_num,name,num_parts,img_url,total_sets_appeared\n"
        "fig-002,Space Figure,2,url-fig,1\n",
        encoding="utf-8",
    )
    # Este tema sem pai verifica que o CSV é lido sem preenchimento na camada raw.
    (pasta / "lego_themes_1975_2025.csv").write_text(
        "id,theme_name,parent_theme,total_sets\n101,Space,,1\n",
        encoding="utf-8",
    )


def test_ingestao_grava_todas_as_linhas_como_varchar_e_reexecuta(monkeypatch, tmp_path):
    _criar_csvs(tmp_path)
    caminho_banco = tmp_path / "teste.duckdb"
    monkeypatch.setattr(ingestao, "PASTA_RAW", tmp_path)
    monkeypatch.setattr(
        ingestao,
        "conectar",
        lambda: duckdb.connect(str(caminho_banco)),
    )
    saida_um, _ = _capturar_terminal(monkeypatch)

    ingestao.main()
    texto_primeira = saida_um.texto
    saida_dois, _ = _capturar_terminal(monkeypatch)
    ingestao.main()
    texto_segunda = saida_dois.texto

    con = duckdb.connect(str(caminho_banco), read_only=True)
    total = con.execute("SELECT count(*) FROM raw.sets").fetchone()[0]
    id_set, tipo_id, parent_vazio = con.execute(
        "SELECT set_num, typeof(set_num), parent_theme FROM raw.sets"
    ).fetchone()
    con.close()

    assert texto_primeira == texto_segunda
    assert "raw.sets: 1" in texto_primeira
    assert "raw.minifiguras: 1" in texto_primeira
    assert "raw.temas: 1" in texto_primeira
    assert "Total: 3" in texto_primeira
    assert total == 1
    assert (id_set, tipo_id, parent_vazio) == ("001-A", "VARCHAR", None)


def test_arquivo_ausente_interrompe_antes_de_conectar(monkeypatch, tmp_path):
    (tmp_path / "lego_sets_1975_2025.csv").write_text(
        "set_num\n001\n", encoding="utf-8"
    )
    chamada_conectar = []
    saida, erro = _capturar_terminal(monkeypatch)

    def conectar_nao_deve_ser_chamado():
        chamada_conectar.append(True)
        raise AssertionError("a validação dos CSVs deve preceder a conexão")

    monkeypatch.setattr(ingestao, "PASTA_RAW", tmp_path)
    monkeypatch.setattr(ingestao, "conectar", conectar_nao_deve_ser_chamado)

    with pytest.raises(SystemExit) as encerramento:
        ingestao.main()

    assert encerramento.value.code == 1
    assert "lego_minifigures_1975_2025.csv" in erro.texto
    assert str(tmp_path) in erro.texto
    assert chamada_conectar == []
    assert saida.encoding == "utf-8"
