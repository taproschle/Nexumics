SELECT
    sample_domain,
    sample_count,
    run_count,
    attribute_count,
    host_present_sample_count,
    environment_present_sample_count,
    clinical_present_sample_count
FROM 'data/gold/sra/parquet/sra_domain_summary.parquet'
ORDER BY sample_count DESC, sample_domain;
