WITH temas_catalogo AS (
    -- Colapsa pares repetidos para o JOIN n?o multiplicar sets hist?ricos.
    SELECT DISTINCT nome_tema, tema_pai
    FROM refined.temas
)
SELECT
    s.ano_lancamento,
    COUNT(DISTINCT s.id_set) AS qtd_sets_lancados,
    SUM(s.qtd_pecas) AS volume_total_pecas,
    COUNT(DISTINCT (t.tema_pai, t.nome_tema))
        FILTER (WHERE t.nome_tema IS NOT NULL) AS qtd_temas_representados
FROM refined.sets s
LEFT JOIN temas_catalogo t
    ON s.nome_tema = t.nome_tema
   AND s.tema_pai = t.tema_pai
GROUP BY s.ano_lancamento
ORDER BY s.ano_lancamento
