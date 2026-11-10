SELECT
    ano_lancamento,
    qtd_cores_unicas,
    COUNT(DISTINCT id_set) AS qtd_sets,
    COUNT(qtd_pecas) AS qtd_sets_com_pecas,
    SUM(qtd_pecas) AS total_pecas,
    ROUND(AVG(qtd_pecas), 1) AS media_pecas
FROM refined.sets
WHERE qtd_cores_unicas IS NOT NULL
GROUP BY ano_lancamento, qtd_cores_unicas
ORDER BY ano_lancamento, qtd_cores_unicas
