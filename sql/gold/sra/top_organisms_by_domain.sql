SELECT
    sample_domain,
    organism_rank,
    organism,
    taxon_id,
    sample_count
FROM 'data/gold/sra/parquet/sra_top_organisms_by_domain.parquet'
ORDER BY sample_domain, organism_rank;
