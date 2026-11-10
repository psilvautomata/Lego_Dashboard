# Pipeline de ingestão

A ingestão lê os três CSVs de `data/` e grava as tabelas correspondentes no schema `raw` do banco `lego.duckdb`.

## Executar

```powershell
uv run python -m pipeline.ingestao
```

## Arquivos e tabelas

| CSV | Tabela criada |
| --- | --- |
| `lego_sets_1975_2025.csv` | `raw.sets` |
| `lego_minifigures_1975_2025.csv` | `raw.minifiguras` |
| `lego_themes_1975_2025.csv` | `raw.temas` |

## O que a etapa faz

- Verifica os três arquivos antes de gravar para evitar uma ingestão parcial.
- Lê os dados como texto em UTF-8; não converte, renomeia ou deduplica colunas.
- Recria as tabelas em cada execução em vez de acrescentar linhas.
- Exibe a contagem persistida no DuckDB para cada tabela.

As regras de tipos, nulos e nomes pertencem à [transformação](transformacao.md).
