SELECT
    library_strategy,
    COUNT(*) AS run_count
FROM 'data/silver/sra/parquet/sra_run.parquet'
GROUP BY library_strategy
ORDER BY run_count DESC, library_strategy;
