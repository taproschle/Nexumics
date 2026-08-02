SELECT
    sample_domain,
    library_strategy,
    run_count,
    sample_count,
    experiment_count,
    total_spots,
    total_bases
FROM gold_sra.sra_domain_library_strategy_summary
ORDER BY run_count DESC, sample_domain, library_strategy;
