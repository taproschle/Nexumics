SELECT
    sample_domain,
    sample_count,
    run_count,
    attribute_count,
    host_present_sample_count,
    environment_present_sample_count,
    clinical_present_sample_count
FROM gold_sra.sra_domain_summary
ORDER BY sample_count DESC, sample_domain;
