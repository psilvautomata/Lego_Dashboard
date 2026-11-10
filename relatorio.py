"""Gera um relatório HTML estático com a apresentação do LEGO Analytics Hub.

Regras desta etapa e seus motivos:
- O relatório lê os cinco marts por ``painel.ler()``, formata valores com
  ``painel.numero``/``painel.pct`` quando aplicável e reutiliza as funções de
  gráfico de ``painel.py``. Recompõe os mesmos indicadores para o período
  completo de 1975 a 2025. Assim, não duplica a apresentação nem cria métricas
  fora da camada SQL; não importa Streamlit nem desenha gráficos novos.
- O HTML contém as mesmas três faixas do app, na mesma ordem: quatro cards,
  dois gráficos e, por fim, dois gráficos e uma tabela. Cards usam HTML/CSS
  simples para que o arquivo abra diretamente no navegador.
- Cada figura é serializada com ``full_html=False`` e um ``div_id`` fixo. O
  Plotly.js vem do CDN no primeiro gráfico apenas; os demais o reutilizam. Isso
  mantém o arquivo pequeno e evita mudanças aleatórias de IDs entre execuções.
- A evolução anual não recebe filtro e representa explicitamente o histórico
  completo de 1975 a 2025, para que o relatório não sugira um recorte variável.
- O rodapé registra a data e a hora de geração no fuso de São Paulo porque o
  HTML não consulta o banco depois de criado e precisa indicar quando os dados
  foram lidos.
- O caminho final e o tamanho do arquivo são impressos em UTF-8 para confirmar
  onde o relatório foi escrito e facilitar sua conferência no Windows.
"""

import sys
from datetime import datetime
from html import escape
from pathlib import Path
from string import Template
from zoneinfo import ZoneInfo

import painel

MARTS = (
    "kpis",
    "evolucao_anual",
    "inventario_cores",
    "top_temas",
    "ultimos_lancamentos",
)
RAIZ = Path(__file__).resolve().parent
ARQUIVO_HTML = RAIZ / "site_docs" / "relatorio.html"


def _cartoes_html(kpi):
    cartoes = (
        ("Sets Lançados", painel.numero(kpi["total_sets"]), "vermelho"),
        ("Volume de Peças", painel.numero(kpi["total_pecas"]), "amarelo"),
        ("Temas Ativos", painel.numero(kpi["total_temas"]), "azul"),
        ("Média Peças/Set", painel.numero(kpi["media_pecas"], casas=1), "verde"),
    )
    return "\n".join(
        (
            '<div class="cartao ' + cor + '">'
            '<div class="rotulo">' + escape(rotulo) + "</div>"
            '<div class="valor">' + escape(valor) + "</div>"
            "</div>"
        )
        for rotulo, valor, cor in cartoes
    )


def _tabela_feed_html(df):
    feed = df.sort_values(
        ["ano_lancamento", "qtd_pecas"],
        ascending=[False, False],
        kind="stable",
    ).head(10)
    feed_visivel = feed[["nome_set", "qtd_pecas"]].rename(
        columns={"nome_set": "Set", "qtd_pecas": "Peças"}
    )
    return feed_visivel.to_html(
        index=False,
        border=0,
        classes="activity-feed",
        escape=True,
    )


def _html_completo(dados):
    figuras = (
        painel.grafico_evolucao_anual(dados["evolucao_anual"]),
        painel.grafico_sets_por_cores_unicas(dados["inventario_cores"]),
        painel.grafico_media_pecas_por_cores_unicas(dados["inventario_cores"]),
        painel.grafico_top_temas(dados["top_temas"]),
    )
    figuras_html = []
    for indice, figura in enumerate(figuras, start=1):
        figuras_html.append(
            figura.to_html(
                full_html=False,
                include_plotlyjs="cdn" if indice == 1 else False,
                div_id=f"g{indice:02d}",
            )
        )

    kpi = dados["kpis"].iloc[0]
    gerado_em = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    template = Template(
        """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LEGO Analytics Hub</title>
  <style>
    :root { color-scheme: light; font-family: Arial, sans-serif; color: #202124; }
    body { margin: 0; padding: 24px; background: #f4f6f8; }
    h1 { margin: 0 0 8px; font-size: 2rem; }
    h2 { margin: 0 0 12px; font-size: 1.15rem; }
    .subtitulo { margin: 0 0 22px; color: #51565c; }
    .faixa { display: grid; gap: 18px; margin: 18px 0; }
    .cartoes { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .dupla { grid-template-columns: 3fr 2fr; }
    .tripla { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .cartao, .painel { background: #fff; border-radius: 10px; padding: 16px; }
    .cartao { min-height: 105px; border: 6px solid; background: #25282d; color: #fff; }
    .vermelho { border-color: #E3000B; }
    .amarelo { border-color: #FFD500; }
    .azul { border-color: #0055BF; }
    .verde { border-color: #00852B; }
    .rotulo { color: #fff; font-size: 1rem; font-weight: 700; margin-bottom: 10px; }
    .valor { color: #fff; font-size: clamp(1.5rem, 2.3vw, 2.3rem); font-weight: 800; }
    .painel { min-width: 0; overflow: hidden; }
    .periodo { color: #51565c; margin: 8px 0 16px; }
    .activity-feed { width: 100%; border-collapse: collapse; font-size: .92rem; }
    .activity-feed th, .activity-feed td { padding: 9px 7px; text-align: left; border-bottom: 1px solid #e4e7eb; }
    .activity-feed th { background: #f4f6f8; }
    footer { color: #5b6066; font-size: .88rem; padding-top: 12px; }
    @media (max-width: 900px) {
      .cartoes, .dupla, .tripla { grid-template-columns: 1fr; }
      body { padding: 14px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>LEGO ANALYTICS HUB</h1>
    <p class="subtitulo">Visão histórica do catálogo Lego.</p>
  </header>
  <section class="faixa cartoes">$cartoes</section>
  <p class="periodo">Evolução anual do período histórico completo, de 1975 a 2025. Os demais indicadores refletem o catálogo histórico total.</p>
  <section class="faixa dupla">
    <div class="painel">$grafico1</div>
    <div class="painel">$grafico2</div>
  </section>
  <section class="faixa tripla">
    <div class="painel">$grafico3</div>
    <div class="painel">$grafico4</div>
    <div class="painel">
      <h2>Activity Feed / Últimos Gigantes</h2>
      $tabela
    </div>
  </section>
  <footer>Dados de $gerado_em</footer>
</body>
</html>
"""
    )
    return template.substitute(
        cartoes=_cartoes_html(kpi),
        grafico1=figuras_html[0],
        grafico2=figuras_html[1],
        grafico3=figuras_html[2],
        grafico4=figuras_html[3],
        tabela=_tabela_feed_html(dados["ultimos_lancamentos"]),
        gerado_em=escape(gerado_em),
    )


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        dados = painel.ler(MARTS)
    except painel.MartsAusentes as erro:
        faltantes = ", ".join(erro.nomes)
        print(
            f"Marts ausentes: {faltantes}. "
            "Rode 'uv run python -m pipeline.marts' e tente novamente.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    dados = painel.aplicar_periodo(dados, 1975, 2025)
    ARQUIVO_HTML.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_HTML.write_text(_html_completo(dados), encoding="utf-8")
    tamanho_kb = ARQUIVO_HTML.stat().st_size / 1024
    print(f"Relatório gerado: {ARQUIVO_HTML} ({painel.numero(tamanho_kb, casas=1)} KB)")


if __name__ == "__main__":
    main()
