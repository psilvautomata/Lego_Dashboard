WITH temas_catalogo AS (
    SELECT
        nome_tema,
        tema_pai,
        COUNT(DISTINCT id_tema) AS qtd_ids_tema_catalogo
    FROM refined.temas
    GROUP BY nome_tema, tema_pai
),
perfil_sets AS (
    SELECT
        tema_pai,
        nome_tema,
        COUNT(DISTINCT id_set) AS total_sets_lancados,
        MIN(ano_lancamento) AS ano_primeiro_lancamento,
        MAX(ano_lancamento) AS ano_ultimo_lancamento,
        (MAX(ano_lancamento) - MIN(ano_lancamento)) + 1 AS anos_de_sobrevivencia,
        ROUND(AVG(qtd_pecas), 0) AS media_pecas_por_set,
        SUM(qtd_minifiguras) AS total_minifiguras_inclusas
    FROM refined.sets
    GROUP BY tema_pai, nome_tema
)
SELECT
    p.tema_pai,
    p.nome_tema,
    p.total_sets_lancados,
    p.ano_primeiro_lancamento,
    p.ano_ultimo_lancamento,
    p.anos_de_sobrevivencia,
    p.media_pecas_por_set,
    p.total_minifiguras_inclusas,
    COALESCE(t.qtd_ids_tema_catalogo, 0) AS qtd_ids_tema_catalogo
FROM perfil_sets p
LEFT JOIN temas_catalogo t
    ON p.nome_tema = t.nome_tema
   AND p.tema_pai = t.tema_pai
ORDER BY p.total_sets_lancados DESC
