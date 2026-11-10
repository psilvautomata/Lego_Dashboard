# LEGO Analytics Hub

Pipeline de dados e dashboard para explorar o catálogo público de LEGO de 1975 a 2025. O projeto usa Python, pandas e DuckDB; as regras analíticas ficam em consultas SQL, e Streamlit e Plotly apresentam os resultados. Disponível originalmente em: https://www.kaggle.com/code/sumedh1507/lego-game-analytics?select=lego_themes_1975_2025.csv

## Fluxo de dados

```text
CSV em data/ → raw → refined → marts → painel ou relatório HTML
```

- **raw:** cópia dos CSVs de origem, sem transformação.
- **refined:** nomes em português, tipos apropriados e regras de nulos e duplicatas.
- **marts:** tabelas analíticas criadas pelos arquivos SQL em `sql/marts/`.
- `sql/marts/legado/` guarda consultas antigas e não é executada pelo pipeline.

O DuckDB fica em `lego.duckdb` na raiz. As etapas recriam as tabelas de destino para permitir reexecução sem acumular linhas.

## Requisitos

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Os três CSVs de origem na pasta `data/`:
  - `lego_sets_1975_2025.csv`
  - `lego_minifigures_1975_2025.csv`
  - `lego_themes_1975_2025.csv`

Instale as dependências do projeto, incluindo as ferramentas de desenvolvimento:

```powershell
uv sync
```

## Executar o pipeline

Rode as etapas na ordem abaixo, a partir da raiz do projeto:

```powershell
uv run python -m pipeline.ingestao
uv run python -m pipeline.transformacao
uv run python -m pipeline.marts
```

A etapa de marts lê os arquivos `sql/marts/marts.*.sql` em ordem alfabética e recria o schema `marts` em uma transação. Se uma consulta falhar ou produzir uma tabela vazia, a execução é revertida.

## Abrir o dashboard e gerar o relatório

Inicie o dashboard interativo:

```powershell
uv run streamlit run app.py
```

O seletor de período aplica o intervalo escolhido aos cartões e aos gráficos. O Activity Feed segue uma regra própria: usa apenas o ano final como limite, pois lista os gigantes mais recentes até aquele ano. O cartão de temas conta os temas distintos com sets no período escolhido.

### Como ler o painel

O seletor define um ano inicial e um ano final. A evolução mostra os sets lançados em cada ano dentro desse intervalo. Os cartões e os gráficos de cores e temas resumem o mesmo período:

**Cartões**

- **Sets Lançados:** quantidade de IDs de sets distintos lançados no período.
- **Volume de Peças:** soma das peças dos sets do período.
- **Temas Ativos:** quantidade de temas distintos que aparecem em sets lançados no período.
- **Média Peças/Set:** média de peças por set que tem essa contagem preenchida.

**Gráficos**

- **Evolução de Lançamentos:** sets lançados por ano, sem incluir anos fora do intervalo selecionado.
- **Sets por Quantidade de Cores Únicas:** número de sets para cada quantidade de cores únicas no período.
- **Média de Peças por Quantidade de Cores Únicas:** média de peças dos sets agrupados pela quantidade de cores únicas.
- **Top Temas por Sets Lançados:** temas com mais sets no período; mostra até dez temas.

**Activity Feed / Últimos Gigantes**

Lista até dez sets com pelo menos 1.000 peças, ordenados pelo ano mais recente e, dentro do ano, pela maior quantidade de peças. A tabela mostra ano, nome do set e peças. O limite superior do seletor define o ano máximo da lista; o limite inferior não se aplica ao feed. Assim, ao escolher 2020–2025, por exemplo, o feed pode incluir gigantes anteriores a 2020, desde que tenham sido lançados até 2025.

O relatório HTML não usa o seletor do dashboard: sempre apresenta o histórico de 1975 a 2025.

Gere a versão estática para abrir no navegador:

```powershell
uv run python relatorio.py
```

O relatório é salvo em `site_docs/relatorio.html`, a pasta fonte do site MkDocs. Para visualizar o site localmente, incluindo a página inicial e o relatório:

```powershell
uv run mkdocs serve
```

Para gerar os arquivos estáticos sem publicar:

```powershell
uv run mkdocs build
```

O workflow do GitHub Actions publica automaticamente o site na branch `gh-pages` quando há push para `main`. Configure uma vez em **Settings → Pages → Build and deployment** a origem **Deploy from a branch**, branch `gh-pages` e pasta `/(root)`. Os gráficos Plotly carregam a biblioteca pelo CDN, portanto o navegador precisa de acesso à internet para exibi-los.

Para explorar o banco pela interface do DuckDB:

```powershell
uv run python ui.py
```

## Testes e qualidade

Os testes usam bancos e arquivos CSV temporários com dados inventados; não dependem do banco nem dos dados locais do projeto.

```powershell
uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
```

A meta configurada é cobertura mínima de 60% no código Python incluído no relatório. O pytest usa `.pytest_tmp/` dentro do projeto para seus arquivos temporários; essa pasta é ignorada pelo Git.

O `.pre-commit-config.yaml` contém hooks para Ruff e pytest. Para ativá-los, instale o pre-commit e registre o hook no repositório:

```powershell
uv tool install pre-commit
pre-commit install
pre-commit run --all-files
```

## Arquivos gerados e dados

`lego.duckdb`, seu arquivo WAL, o relatório antigo na raiz, o site compilado em `site/` e caches de ferramentas são saídas locais e ficam fora do Git. `site_docs/` contém as fontes do MkDocs e o relatório estático destinado à publicação; esses arquivos devem ser versionados. Os CSVs em `data/` são entradas necessárias do pipeline e não são ignorados pelo `.gitignore`.
