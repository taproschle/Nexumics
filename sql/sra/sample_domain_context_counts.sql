SELECT
    sample_domain,
    sample_context,
    COUNT(*) AS sample_count
FROM 'data/silver/sra/parquet/sra_sample_classification.parquet'
GROUP BY sample_domain, sample_context
ORDER BY sample_count DESC, sample_domain, sample_context;
