# Pipeline de marts

Esta etapa executa os arquivos `sql/marts/marts.*.sql` em ordem alfabética e cria uma tabela no schema `marts` para cada arquivo.

## Executar

```powershell
uv run python -m pipeline.marts
```

## Consultas atuais

| Arquivo SQL | Tabela criada |
| --- | --- |
| `marts.kpis.sql` | `marts.kpis` |
| `marts.evolucao_anual.sql` | `marts.evolucao_anual` |
| `marts.inventario_cores.sql` | `marts.inventario_cores` |
| `marts.top_temas.sql` | `marts.top_temas` |
| `marts.ultimos_lancamentos.sql` | `marts.ultimos_lancamentos` |

## Reexecução e falhas

O schema `marts` é substituído dentro de uma transação. Se uma consulta falhar ou criar uma tabela vazia, a transação é revertida e os marts da última execução válida são mantidos.
