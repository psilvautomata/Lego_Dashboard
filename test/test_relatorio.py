from datetime import datetime

import duckdb
import pytest

import relatorio


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


def _capturar_saida(monkeypatch):
    saida = TerminalBuffer()
    monkeypatch.setattr(relatorio.sys, "stdout", saida)
    return saida


def _criar_marts_temporarios(caminho_banco):
    con = duckdb.connect(str(caminho_banco))
    con.execute("CREATE SCHEMA marts")
    # Totais anuais inventados recompõem os cartões do período completo.
    con.execute(
        "CREATE TABLE marts.kpis AS "
        "SELECT * FROM (VALUES "
        "(2001, 123, 123, 20000, 162.6), (2002, 198, 198, 28321, 143.0)) "
        "AS dados(ano_lancamento, total_sets, qtd_sets_com_pecas, total_pecas, media_pecas)"
    )
    # Dois anos inventados permitem verificar a série histórica completa, sem filtro.
    con.execute(
        "CREATE TABLE marts.evolucao_anual AS "
        "SELECT * FROM (VALUES (2001, 2), (2002, 3)) "
        "AS dados(ano_lancamento, qtd_sets_lancados)"
    )
    # Dois níveis de cores únicas fornecem barras pequenas e determinísticas.
    con.execute(
        "CREATE TABLE marts.inventario_cores AS "
        "SELECT * FROM (VALUES "
        "(2001, 2, 2, 2, 24, 12.0), (2002, 2, 3, 3, 36, 12.0), "
        "(2002, 4, 3, 3, 60, 20.0)) "
        "AS dados(ano_lancamento, qtd_cores_unicas, qtd_sets, "
        "qtd_sets_com_pecas, total_pecas, media_pecas)"
    )
    # Dois temas inventados permitem confirmar a figura horizontal e o HTML.
    con.execute(
        "CREATE TABLE marts.top_temas AS "
        "SELECT * FROM (VALUES "
        "(2001, 'Pai A', 'Tema A', 'Tema A - Pai A', 9, 1), "
        "(2002, 'Pai B', 'Tema B', 'Tema B - Pai B', 5, 1)) "
        "AS dados(ano_lancamento, tema_pai, nome_tema, tema, total_sets, qtd_ids_tema_catalogo)"
    )
    # Dois lançamentos grandes fictícios alimentam a tabela de atividade.
    con.execute(
        "CREATE TABLE marts.ultimos_lancamentos AS "
        "SELECT * FROM (VALUES "
        "('Set recente', 2002, 5000), ('Set anterior', 2001, 3000)) "
        "AS dados(nome_set, ano_lancamento, qtd_pecas)"
    )
    con.close()


def test_relatorio_html_tem_cards_graficos_tabela_e_diff_estavel(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "lego.duckdb"
    caminho_html = tmp_path / "relatorio.html"
    _criar_marts_temporarios(caminho_banco)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(relatorio, "ARQUIVO_HTML", caminho_html)
    horarios = iter(
        [
            datetime(2025, 1, 2, 3, 4),
            datetime(2025, 1, 2, 3, 5),
        ]
    )

    class RelogioFixo:
        @staticmethod
        def now(fuso):
            return next(horarios).replace(tzinfo=fuso)

    monkeypatch.setattr(relatorio, "datetime", RelogioFixo)
    saida = _capturar_saida(monkeypatch)

    relatorio.main()
    html_primeiro = caminho_html.read_text(encoding="utf-8")
    relatorio.main()
    html_segundo = caminho_html.read_text(encoding="utf-8")

    assert ">321</div>" in html_primeiro
    assert "48.321" in html_primeiro
    assert ">2</div>" in html_primeiro
    assert "150,5" in html_primeiro
    assert "Dados de 02/01/2025 03:04" in html_primeiro
    assert "Dados de 02/01/2025 03:05" in html_segundo
    assert all(f'id="g{indice:02d}"' in html_primeiro for indice in range(1, 5))
    assert html_primeiro.count("cdn.plot.ly") == 1
    assert '<table class="dataframe activity-feed">' in html_primeiro
    assert "Set recente" in html_primeiro
    assert caminho_html.stat().st_size < 200 * 1024
    assert "KB" in saida.texto

    normalizado_primeiro = html_primeiro.replace(
        "Dados de 02/01/2025 03:04", "Dados de <DATA_HORA>"
    )
    normalizado_segundo = html_segundo.replace(
        "Dados de 02/01/2025 03:05", "Dados de <DATA_HORA>"
    )
    assert normalizado_primeiro == normalizado_segundo


def test_relatorio_encerra_com_marts_ausentes(monkeypatch, tmp_path):
    caminho_banco = tmp_path / "lego.duckdb"
    con = duckdb.connect(str(caminho_banco))
    con.execute("CREATE SCHEMA marts")
    con.close()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(relatorio, "ARQUIVO_HTML", tmp_path / "relatorio.html")
    _capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as encerramento:
        relatorio.main()

    assert encerramento.value.code == 1
    assert not (tmp_path / "relatorio.html").exists()
