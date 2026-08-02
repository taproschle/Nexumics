SELECT
    sample_domain,
    attribute_category,
    attribute_count,
    sample_count
FROM 'data/gold/sra/parquet/sra_attribute_category_by_domain.parquet'
ORDER BY sample_domain, attribute_count DESC, attribute_category;
