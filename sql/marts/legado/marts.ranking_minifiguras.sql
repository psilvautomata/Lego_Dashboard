SELECT
    id_minifigura,
    nome_minifigura,
    qtd_pecas AS complexidade_montagem,
    qtd_sets_presente AS qtd_aparicoes_em_sets,
    CASE
        WHEN qtd_sets_presente = 1 THEN 'Exclusiva (1 set)'
        WHEN qtd_sets_presente BETWEEN 2 AND 5 THEN 'Rara (2 a 5 sets)'
        WHEN qtd_sets_presente BETWEEN 6 AND 20 THEN 'Comum (6 a 20 sets)'
        ELSE 'Curinga de F?brica (> 20 sets)'
    END AS classificacao_raridade,
    url_imagem
FROM refined.minifiguras
WHERE qtd_sets_presente > 0
ORDER BY qtd_sets_presente DESC
