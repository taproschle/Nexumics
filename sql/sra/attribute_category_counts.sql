SELECT
    attribute_category,
    COUNT(*) AS attribute_count
FROM 'data/silver/sra/parquet/sra_sample_attribute.parquet'
GROUP BY attribute_category
ORDER BY attribute_count DESC, attribute_category;
