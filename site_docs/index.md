# LEGO Analytics Hub

Explore a evolução histórica do catálogo LEGO entre **1975 e 2025**. O relatório reúne indicadores do catálogo, lançamentos por ano, distribuição de sets por cores únicas, média de peças e temas com mais lançamentos.

## Relatório estático

[Abrir o relatório completo](relatorio.html){ .md-button .md-button--primary }

O relatório é gerado a partir dos marts locais pelo comando `uv run python relatorio.py`. Ele é uma captura dos dados disponíveis no momento da geração; os gráficos carregam Plotly pelo CDN e precisam de acesso à internet.

## Dashboard interativo

O dashboard interativo com filtro de período pode ser executado localmente com:

```powershell
uv run streamlit run app.py
```

O GitHub Pages hospeda o site estático e não executa o aplicativo Streamlit.
