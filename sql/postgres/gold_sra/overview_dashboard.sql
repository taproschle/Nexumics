SELECT
    d.sample_domain,
    d.sample_count,
    d.run_count,
    d.attribute_count,
    ROUND((d.sample_count::numeric / NULLIF(q.sample_count, 0)) * 100, 2) AS sample_pct,
    d.host_present_sample_count,
    d.environment_present_sample_count,
    d.clinical_present_sample_count,
    d.metagenome_present_sample_count
FROM gold_sra.sra_domain_summary AS d
CROSS JOIN gold_sra.sra_quality_summary AS q
ORDER BY d.sample_count DESC, d.sample_domain;
