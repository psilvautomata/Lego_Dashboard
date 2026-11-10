# Dashboard

Inicie a aplicação interativa na raiz do projeto:

```powershell
uv run streamlit run app.py
```

O seletor de período filtra os cartões e os gráficos. O Activity Feed usa o ano final como limite superior; o ano inicial não restringe a lista.

## Cartões

- **Sets Lançados:** quantidade de IDs de sets distintos lançados no período.
- **Volume de Peças:** soma das peças dos sets no período.
- **Temas Ativos:** quantidade de temas distintos com sets no período.
- **Média Peças/Set:** média de peças dos sets com essa contagem preenchida.

## Gráficos

- **Evolução de Lançamentos:** quantidade de sets por ano dentro do período.
- **Sets por Quantidade de Cores Únicas:** número de sets para cada quantidade de cores.
- **Média de Peças por Quantidade de Cores Únicas:** média de peças por grupo de cores.
- **Top Temas por Sets Lançados:** até dez temas com mais sets no período.

## Activity Feed / Últimos Gigantes

Lista até dez sets com pelo menos 1.000 peças, ordenados pelo ano mais recente e, dentro do ano, pela maior quantidade de peças. O limite superior do período filtra a lista; o limite inferior não se aplica.

## Atualização dos dados

Depois de executar novamente o pipeline, use **Recarregar Dados** na barra lateral para limpar o cache e ler os marts atualizados.
