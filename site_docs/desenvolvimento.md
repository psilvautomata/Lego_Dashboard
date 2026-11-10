# Desenvolvimento

## Requisitos

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Os três arquivos CSV listados em [Configuração](configuracao.md)

## Instalação

Na raiz do repositório, instale as dependências:

```powershell
uv sync
```

## Executar o pipeline

Execute as etapas na ordem abaixo para popular o banco local:

```powershell
uv run python -m pipeline.ingestao
uv run python -m pipeline.transformacao
uv run python -m pipeline.marts
```

## Verificações

Os testes usam bancos temporários e dados sintéticos. Rode os testes e as verificações de estilo com:

```powershell
uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
```

## Pré-commit

O repositório tem hooks de Ruff e pytest configurados em `.pre-commit-config.yaml`:

```powershell
uv tool install pre-commit
pre-commit install
pre-commit run --all-files
```
