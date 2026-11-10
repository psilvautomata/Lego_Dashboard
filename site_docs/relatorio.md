# Relatório estático

O relatório HTML mostra a visão histórica completa do catálogo, de 1975 a 2025. Ele não depende de um filtro de período e é gerado a partir dos marts atuais.

Para regenerá-lo na raiz do projeto:

```powershell
uv run python relatorio.py
```

[Abrir o relatório LEGO Analytics Hub](relatorio.html)

Os gráficos carregam o Plotly pelo CDN e precisam de acesso à internet. O HTML registra a data e a hora em que foi gerado.
