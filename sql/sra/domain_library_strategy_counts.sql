SELECT
    c.sample_domain,
    r.library_strategy,
    COUNT(*) AS run_count
FROM 'data/silver/sra/parquet/sra_run.parquet' AS r
JOIN 'data/silver/sra/parquet/sra_sample_classification.parquet' AS c
    ON r.sample_accession = c.sample_accession
GROUP BY c.sample_domain, r.library_strategy
ORDER BY run_count DESC, c.sample_domain, r.library_strategy;
