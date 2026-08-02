SELECT
    sample_domain,
    library_strategy,
    run_count,
    sample_count,
    experiment_count,
    total_spots,
    total_bases
FROM 'data/gold/sra/parquet/sra_domain_library_strategy_summary.parquet'
ORDER BY run_count DESC, sample_domain, library_strategy;
