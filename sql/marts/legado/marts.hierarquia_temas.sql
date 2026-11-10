WITH temas_por_pai AS (
    SELECT
        tema_pai,
        COUNT(DISTINCT id_tema) AS qtd_subtemas_diferentes,
        SUM(qtd_total_sets) AS volume_historico_catalogo
    FROM refined.temas
    GROUP BY tema_pai
),
sets_por_pai AS (
    SELECT
        tema_pai,
        COUNT(DISTINCT id_set) AS qtd_sets_observados,
        SUM(qtd_pecas) AS volume_pecas_observado
    FROM refined.sets
    GROUP BY tema_pai
),
hierarquia AS (
    SELECT
        t.tema_pai,
        t.qtd_subtemas_diferentes,
        t.volume_historico_catalogo,
        COALESCE(s.qtd_sets_observados, 0) AS qtd_sets_observados,
        COALESCE(s.volume_pecas_observado, 0) AS volume_pecas_observado
    FROM temas_por_pai t
    LEFT JOIN sets_por_pai s USING (tema_pai)
)
SELECT
    tema_pai,
    qtd_subtemas_diferentes,
    volume_historico_catalogo,
    qtd_sets_observados,
    volume_pecas_observado,
    ROUND(
        volume_historico_catalogo * 100.0
        / NULLIF(SUM(volume_historico_catalogo) OVER (), 0),
        2
    ) AS share_do_portfolio_total_pct
FROM hierarquia
ORDER BY volume_historico_catalogo DESC
