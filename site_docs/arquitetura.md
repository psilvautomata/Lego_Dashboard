# Arquitetura

O pipeline separa os dados recebidos das transformações e das consultas analíticas. Cada etapa recria sua saída para permitir uma execução repetível.

## Fluxo de dados

```text
CSV em data/ → raw → refined → marts → dashboard ou relatório HTML
```

## Camadas

### Raw

Recebe os três CSVs em `data/` sem alterar os valores. As tabelas `sets`, `minifiguras` e `temas` são armazenadas no DuckDB como texto.

### Refined

Renomeia as colunas para português, converte anos e contagens para inteiros, converte `possui_minifiguras` para booleano e aplica as regras de valores ausentes e duplicatas.

### Marts

As consultas em `sql/marts/` leem a camada `refined` e produzem tabelas analíticas no schema `marts`. A regra de negócio fica nos arquivos SQL.

### Apresentação

`app.py` lê os marts para o dashboard Streamlit. `relatorio.py` gera um HTML estático com os mesmos gráficos e indicadores, para abrir no navegador ou publicar junto desta documentação.

## Banco de dados

O DuckDB fica em `lego.duckdb` na raiz do projeto. A localização é resolvida a partir dos arquivos Python, então os comandos podem ser executados a partir da raiz.
