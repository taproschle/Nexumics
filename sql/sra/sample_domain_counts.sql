SELECT
    sample_domain,
    COUNT(*) AS sample_count
FROM 'data/silver/sra/parquet/sra_sample_classification.parquet'
GROUP BY sample_domain
ORDER BY sample_count DESC, sample_domain;
