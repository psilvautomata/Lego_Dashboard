# Configuração

## Arquivos de origem

Coloque estes CSVs na pasta `data/`:

| Arquivo | Tabela raw |
| --- | --- |
| `lego_sets_1975_2025.csv` | `raw.sets` |
| `lego_minifigures_1975_2025.csv` | `raw.minifiguras` |
| `lego_themes_1975_2025.csv` | `raw.temas` |

A ingestão espera UTF-8 e mantém as colunas como texto. Arquivo ausente interrompe a etapa antes de gravar as tabelas.

## Banco local

O banco DuckDB é criado como `lego.duckdb` na raiz. O repositório ignora o banco e seu arquivo WAL; os dados de origem em `data/` são entradas do pipeline.

## Ambiente

As dependências e as versões resolvidas ficam declaradas em `pyproject.toml` e `uv.lock`. Reproduza o ambiente com `uv sync`.
