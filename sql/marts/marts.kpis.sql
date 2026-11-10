SELECT
    ano_lancamento,
    COUNT(DISTINCT id_set) AS total_sets,
    COUNT(qtd_pecas) AS qtd_sets_com_pecas,
    SUM(qtd_pecas) AS total_pecas,
    AVG(qtd_pecas) AS media_pecas
FROM refined.sets
GROUP BY ano_lancamento
ORDER BY ano_lancamento
