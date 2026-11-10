from pathlib import Path

import duckdb
import streamlit as st

import painel

MARTS = (
    "kpis",
    "evolucao_anual",
    "inventario_cores",
    "top_temas",
    "ultimos_lancamentos",
)
BANCO = Path(__file__).resolve().parent / "lego.duckdb"


@st.cache_data
def carregar_marts(versao_banco):
    return painel.ler(MARTS)


st.set_page_config(page_title="LEGO Analytics Hub", layout="wide")

st.sidebar.title("Dados")
if st.sidebar.button("Recarregar Dados"):
    st.cache_data.clear()
    st.rerun()

if not BANCO.is_file():
    st.error(
        f"Banco lego.duckdb não encontrado em {BANCO}. "
        "Crie as camadas anteriores e rode `uv run python -m pipeline.marts`."
    )
    st.stop()

try:
    estado_banco = BANCO.stat()
    dados = carregar_marts((estado_banco.st_mtime_ns, estado_banco.st_size))
except painel.MartsAusentes as erro:
    faltantes = ", ".join(erro.nomes)
    st.error(
        f"Marts ausentes: {faltantes}. "
        "Rode `uv run python -m pipeline.marts` e clique em Recarregar Dados."
    )
    st.stop()
except duckdb.Error as erro:
    st.error(f"Não foi possível ler os marts do banco: {erro}")
    st.stop()

st.markdown(
    """
    <style>
    .lego-card {
        background: #25282d;
        border: 6px solid;
        border-radius: 10px;
        min-height: 118px;
        padding: 16px 18px;
    }
    .lego-card-label {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .lego-card-value {
        color: #ffffff;
        font-size: clamp(1.6rem, 2.4vw, 2.4rem);
        font-weight: 800;
        line-height: 1.1;
    }
    .lego-red { border-color: #E3000B; }
    .lego-yellow { border-color: #FFD500; }
    .lego-blue { border-color: #0055BF; }
    .lego-green { border-color: #00852B; }
    </style>
    """,
    unsafe_allow_html=True,
)

anos = sorted(dados["evolucao_anual"]["ano_lancamento"].dropna().tolist())
cabecalho_titulo, cabecalho_filtro = st.columns([3, 2])
with cabecalho_titulo:
    st.title("LEGO ANALYTICS HUB")
with cabecalho_filtro:
    periodo = st.select_slider(
        "Período (anos)",
        options=anos,
        value=(anos[0], anos[-1]),
        format_func=str,
    )
    st.caption(f"Todos os indicadores mostram o período de {periodo[0]} a {periodo[1]}")

dados_periodo = painel.aplicar_periodo(dados, periodo[0], periodo[1])
kpi = dados_periodo["kpis"].iloc[0]
colunas_cards = st.columns(4)
cartoes = (
    ("Sets Lançados", painel.numero(kpi["total_sets"]), "lego-red"),
    ("Volume de Peças", painel.numero(kpi["total_pecas"]), "lego-yellow"),
    ("Temas Ativos", painel.numero(kpi["total_temas"]), "lego-blue"),
    ("Média Peças/Set", painel.numero(kpi["media_pecas"], casas=1), "lego-green"),
)
for coluna, (rotulo, valor, cor) in zip(colunas_cards, cartoes):
    coluna.markdown(
        f"""
        <div class="lego-card {cor}">
            <div class="lego-card-label">{rotulo}</div>
            <div class="lego-card-value">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

coluna_evolucao, coluna_cores = st.columns([3, 2])
with coluna_evolucao:
    st.plotly_chart(
        painel.grafico_evolucao_anual(dados_periodo["evolucao_anual"]),
        width="stretch",
    )
with coluna_cores:
    st.plotly_chart(
        painel.grafico_sets_por_cores_unicas(dados_periodo["inventario_cores"]),
        width="stretch",
    )

coluna_media_cores, coluna_temas, coluna_feed = st.columns(3)
with coluna_media_cores:
    st.plotly_chart(
        painel.grafico_media_pecas_por_cores_unicas(dados_periodo["inventario_cores"]),
        width="stretch",
    )
with coluna_temas:
    st.plotly_chart(
        painel.grafico_top_temas(dados_periodo["top_temas"]),
        width="stretch",
    )
with coluna_feed:
    st.subheader("Activity Feed / Últimos Gigantes")
    df_ultimos_lancamentos = dados["ultimos_lancamentos"]
    df_gigantes_filtrado = df_ultimos_lancamentos[
        df_ultimos_lancamentos["ano_lancamento"] <= periodo[1]
    ]
    st.caption(
        f"Gigantes lançados até {periodo[1]}; o ano inicial não limita esta lista."
    )
    feed = df_gigantes_filtrado.sort_values(
        ["ano_lancamento", "qtd_pecas"],
        ascending=[False, False],
        kind="stable",
    ).head(10)
    feed_visivel = feed[["ano_lancamento", "nome_set", "qtd_pecas"]].rename(
        columns={
            "ano_lancamento": "Ano",
            "nome_set": "Set",
            "qtd_pecas": "Peças",
        }
    )
    st.dataframe(feed_visivel, hide_index=True, width="stretch")
