SELECT
    sample_context,
    sample_count,
    run_count,
    attribute_count,
    sample_domain_count
FROM 'data/gold/sra/parquet/sra_context_summary.parquet'
ORDER BY sample_count DESC, sample_context;
