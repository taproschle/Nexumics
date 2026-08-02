SELECT
    sample_domain,
    organism_rank,
    organism,
    taxon_id,
    sample_count
FROM gold_sra.sra_top_organisms_by_domain
ORDER BY sample_domain, organism_rank;
