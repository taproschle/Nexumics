SELECT
    sample_domain,
    library_strategy,
    run_count,
    sample_count,
    experiment_count,
    total_bases
FROM gold_sra.sra_domain_library_strategy_summary
WHERE library_strategy IS NOT NULL
ORDER BY run_count DESC
LIMIT 25;
