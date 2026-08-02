SELECT
    sample_context,
    sample_count,
    run_count,
    attribute_count,
    sample_domain_count
FROM gold_sra.sra_context_summary
ORDER BY sample_count DESC, sample_context;
