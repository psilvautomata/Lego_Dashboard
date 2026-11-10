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
    s.tema_pai,
    s.ano_lancamento,
    s.qtd_pecas,
    s.qtd_cores_unicas,
    s.qtd_minifiguras,
    s.url_imagem,
    t.id_tema,
    COALESCE(t.qtd_ids_tema_catalogo, 0) AS qtd_ids_tema_catalogo,
    CASE
        WHEN s.qtd_pecas >= 5000 THEN 'Gigante (5k+ pe?as)'
        WHEN s.qtd_pecas >= 2000 THEN 'Grande (2k-5k pe?as)'
        ELSE 'M?dio-Grande (1k-2k pe?as)'
    END AS categoria_tamanho
FROM refined.sets s
LEFT JOIN temas_catalogo t
    ON s.nome_tema = t.nome_tema
   AND s.tema_pai = t.tema_pai
WHERE s.qtd_pecas >= 1000
ORDER BY s.qtd_pecas DESC
