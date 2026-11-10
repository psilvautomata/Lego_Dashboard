WITH temas_catalogo AS (
    -- Colapsa pares repetidos para o JOIN n?o multiplicar sets hist?ricos.
    SELECT DISTINCT nome_tema, tema_pai
    FROM refined.temas
)
SELECT
    s.ano_lancamento,
    COUNT(DISTINCT s.id_set) AS qtd_sets_lancados,
    SUM(s.qtd_pecas) AS volume_total_pecas_produzidas,
    ROUND(AVG(s.qtd_pecas), 1) AS media_pecas_por_set,
    MAX(s.qtd_pecas) AS max_pecas_em_um_unico_set,
    ROUND(AVG(s.qtd_minifiguras), 1) AS media_minifiguras_por_set,
    ROUND(AVG(s.qtd_cores_unicas), 1) AS media_cores_unicas,
    SUM(CASE WHEN s.possui_minifiguras THEN 1 ELSE 0 END) AS qtd_sets_com_minifiguras,
    COUNT(DISTINCT (t.tema_pai, t.nome_tema))
        FILTER (WHERE t.nome_tema IS NOT NULL) AS qtd_temas_representados
FROM refined.sets s
LEFT JOIN temas_catalogo t
    ON s.nome_tema = t.nome_tema
   AND s.tema_pai = t.tema_pai
GROUP BY s.ano_lancamento
ORDER BY s.ano_lancamento
