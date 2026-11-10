WITH temas_catalogo AS (
    SELECT
        nome_tema,
        tema_pai,
        CASE WHEN COUNT(DISTINCT id_tema) = 1 THEN MIN(id_tema) END AS id_tema,
        COUNT(DISTINCT id_tema) AS qtd_ids_tema_catalogo
    FROM refined.temas
    GROUP BY nome_tema, tema_pai
)
SELECT
    s.id_set,
    s.nome_set,
    s.ano_lancamento,
    s.qtd_pecas,
    s.tema_pai,
    t.id_tema,
    COALESCE(t.qtd_ids_tema_catalogo, 0) AS qtd_ids_tema_catalogo
FROM refined.sets s
LEFT JOIN temas_catalogo t
    ON s.nome_tema = t.nome_tema
   AND s.tema_pai = t.tema_pai
WHERE s.qtd_pecas >= 1000
ORDER BY s.ano_lancamento DESC, s.qtd_pecas DESC, s.id_set
