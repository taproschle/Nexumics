SELECT
    sample_domain,
    attribute_category,
    attribute_count,
    sample_count
FROM gold_sra.sra_attribute_category_by_domain
ORDER BY sample_domain, attribute_count DESC, attribute_category;
