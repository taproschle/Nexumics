SELECT
    sample_count,
    run_count,
    attribute_count,
    unknown_sample_count,
    unknown_sample_pct
FROM 'data/gold/sra/parquet/sra_quality_summary.parquet';
