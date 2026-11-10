WITH temas_catalogo AS (
    SELECT
        nome_tema,
        tema_pai,
        COUNT(DISTINCT id_tema) AS qtd_ids_tema_catalogo
    FROM refined.temas
    GROUP BY nome_tema, tema_pai
),
sets_por_tema AS (
    SELECT
        ano_lancamento,
        tema_pai,
        nome_tema,
        COUNT(DISTINCT id_set) AS total_sets
    FROM refined.sets
    GROUP BY ano_lancamento, tema_pai, nome_tema
)
SELECT
    s.ano_lancamento,
    s.tema_pai,
    s.nome_tema,
    s.nome_tema || ' - ' || s.tema_pai AS tema,
    s.total_sets,
    COALESCE(t.qtd_ids_tema_catalogo, 0) AS qtd_ids_tema_catalogo
FROM sets_por_tema s
LEFT JOIN temas_catalogo t
    ON s.nome_tema = t.nome_tema
   AND s.tema_pai = t.tema_pai
ORDER BY s.total_sets DESC
