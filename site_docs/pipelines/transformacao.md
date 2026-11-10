# Pipeline de transformação

A transformação lê `raw.sets`, `raw.minifiguras` e `raw.temas` e grava as tabelas correspondentes no schema `refined`.

## Executar

```powershell
uv run python -m pipeline.transformacao
```

## Regras principais

- As colunas são renomeadas para português, seguindo os mapas em `pipeline/transformacao.py`.
- Anos e contagens viram inteiros; `possui_minifiguras` vira booleano.
- Falhas de conversão viram `NULL` e são registradas no log.
- Duplicatas integralmente idênticas são removidas; chaves repetidas com conteúdo diferente permanecem.
- Nulos de `tema_pai` viram `Sem Tema Pai`; valores ausentes de `qtd_minifiguras` em sets viram zero.
- `raw` é preservado; as tabelas de saída são recriadas em `refined`.

A etapa verifica se as três tabelas de origem existem antes de gravar.
