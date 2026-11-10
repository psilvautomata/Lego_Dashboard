# LEGO Analytics Hub

O projeto apresenta o catálogo público de LEGO de **1975 a 2025** por meio de um pipeline de dados local, um dashboard interativo e um relatório estático.

O objetivo é transformar os arquivos CSV em camadas analíticas reproduzíveis e deixar as regras de negócio nas consultas SQL.

## Preparar os dados

Na raiz do projeto, instale as dependências e execute as três etapas em ordem:

```powershell
uv sync
uv run python -m pipeline.ingestao
uv run python -m pipeline.transformacao
uv run python -m pipeline.marts
```

## Conteúdo

- [Arquitetura](arquitetura.md)
- [Desenvolvimento](desenvolvimento.md)
- [Configuração](configuracao.md)
- [Dashboard](dashboard.md)
- [Pipeline de ingestão](pipelines/ingestao.md)
- [Relatório estático](relatorio.md)

O GitHub Pages publica esta documentação e o relatório HTML. O dashboard interativo Streamlit é executado localmente; GitHub Pages não executa aplicações Python.
