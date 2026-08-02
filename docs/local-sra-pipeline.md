# Local SRA Pipeline

This document describes the local SRA pipeline currently implemented in Nexumics. It focuses on the reproducible path from already-downloaded SRA batch metadata to validated Silver and Gold analytical outputs.

## Scope

The local pipeline does not download new records from NCBI. It rebuilds the local data lake from batch files already present under:

```text
data/bronze/sra/batches/
```

The `data/` directory is intentionally ignored by Git. Code, tests, documentation, and SQL are versioned; raw, Bronze, Silver, Gold, summary, and quality outputs are local runtime artifacts.

## End-To-End Command

Run the full local lake build with:

```powershell
nexumics-build-sra-local-lake
```

This runs:

```text
Bronze batches
-> Bronze combined CSV
-> existing optional NCBI Taxonomy reference
-> Silver CSV
-> Silver Parquet
-> Gold Parquet
-> Silver summary CSV
-> Quality report
```

The command is intended to be the main local rebuild entrypoint once SRA batch data has already been downloaded.

## Implemented Flow

```text
data/bronze/sra/batches/
  -> data/bronze/sra/combined/
  -> data/reference/ncbi_taxonomy/
  -> data/silver/sra/
  -> data/silver/sra/parquet/
  -> data/gold/sra/parquet/
  -> data/silver/sra/summary/
  -> data/quality/sra/
```

## Stage Commands

Each stage can also be run independently.

### 1. Consolidate Bronze

```powershell
nexumics-combine-sra-bronze
```

Inputs:

```text
data/bronze/sra/batches/<query-job-id>/sra-bronze-batch-<batch-number>.csv
data/bronze/sra/batches/<query-job-id>/sra-sample-attributes-batch-<batch-number>.csv
```

Outputs:

```text
data/bronze/sra/combined/sra-bronze-combined-<timestamp>.csv
data/bronze/sra/combined/sra-sample-attributes-combined-<timestamp>.csv
```

Purpose:

- Combine per-query batch files.
- Deduplicate overlapping query results.
- Preserve lineage with `source_dataset` and `source_file`.
- Recompute sample attribute categories with the current dictionary.

Current latest consolidated output:

| Output | Rows |
| --- | ---: |
| Bronze runs | 89,840 |
| Bronze sample attributes | 914,148 |

### 2. Build Silver CSV

```powershell
nexumics-build-sra-silver
```

Inputs:

```text
data/bronze/sra/combined/
```

Outputs:

```text
data/silver/sra/sra_run.csv
data/silver/sra/sra_sample.csv
data/silver/sra/sra_sample_attribute.csv
data/silver/sra/sra_sample_classification.csv
```

Purpose:

- Create normalized entity-style tables.
- Keep one row per run in `sra_run`.
- Keep one row per sample in `sra_sample`.
- Preserve flexible BioSample/SRA attributes in `sra_sample_attribute`.
- Derive sample-level domain and context in `sra_sample_classification`.

Current Silver row counts:

| Table | Rows |
| --- | ---: |
| `sra_run.csv` | 89,840 |
| `sra_sample.csv` | 75,792 |
| `sra_sample_attribute.csv` | 914,148 |
| `sra_sample_classification.csv` | 75,792 |

### 3. Update NCBI Taxonomy Reference

```powershell
nexumics-update-ncbi-taxonomy-reference
```

This is a networked enrichment command, not part of the local-only rebuild command. Run it after Silver samples exist and before rebuilding Silver classifications when new `taxon_id` values have been downloaded.

Inputs:

```text
data/silver/sra/sra_sample.csv
```

Outputs:

```text
data/reference/ncbi_taxonomy/taxonomy_reference.csv
```

Purpose:

- Read unique SRA `taxon_id` values from Silver samples.
- Fetch only missing taxon IDs from NCBI Taxonomy.
- Preserve a local incremental taxonomy reference table.
- Improve `sra_sample_classification` by using lineage-derived domains before falling back to heuristics.

Current local reference:

| Output | Rows |
| --- | ---: |
| `taxonomy_reference.csv` | 2,714 |

### 4. Export Silver Parquet

```powershell
nexumics-export-sra-silver-parquet
```

Inputs:

```text
data/silver/sra/*.csv
```

Outputs:

```text
data/silver/sra/parquet/sra_run.parquet
data/silver/sra/parquet/sra_sample.parquet
data/silver/sra/parquet/sra_sample_attribute.parquet
data/silver/sra/parquet/sra_sample_classification.parquet
```

Purpose:

- Convert Silver CSV tables into compact analytical Parquet files.
- Enable DuckDB SQL queries over local lake files.
- Keep CSV as a readable development artifact while using Parquet for analytics.

Current Silver Parquet outputs:

| Table | Rows | Size |
| --- | ---: | ---: |
| `sra_run.parquet` | 89,840 | 3.00 MB |
| `sra_sample.parquet` | 75,792 | 0.81 MB |
| `sra_sample_attribute.parquet` | 914,148 | 3.74 MB |
| `sra_sample_classification.parquet` | 75,792 | 0.92 MB |

### 5. Build Gold Parquet

```powershell
nexumics-build-sra-gold
```

Inputs:

```text
data/silver/sra/parquet/
```

Outputs:

```text
data/gold/sra/parquet/sra_domain_summary.parquet
data/gold/sra/parquet/sra_context_summary.parquet
data/gold/sra/parquet/sra_domain_library_strategy_summary.parquet
data/gold/sra/parquet/sra_top_organisms_by_domain.parquet
data/gold/sra/parquet/sra_attribute_category_by_domain.parquet
data/gold/sra/parquet/sra_quality_summary.parquet
```

Purpose:

- Produce analysis-ready tables from Silver Parquet.
- Answer portfolio-level questions without repeatedly writing joins.
- Prepare outputs that can later feed PostgreSQL, Metabase, or dashboards.

Current Gold outputs:

| Table | Rows | Size |
| --- | ---: | ---: |
| `sra_domain_summary.parquet` | 9 | 1.85 KB |
| `sra_context_summary.parquet` | 7 | 1.02 KB |
| `sra_domain_library_strategy_summary.parquet` | 73 | 3.33 KB |
| `sra_top_organisms_by_domain.parquet` | 75 | 3.30 KB |
| `sra_attribute_category_by_domain.parquet` | 210 | 3.31 KB |
| `sra_quality_summary.parquet` | 1 | 0.80 KB |

### 6. Summarize Silver

```powershell
nexumics-summarize-sra-silver
```

Outputs:

```text
data/silver/sra/summary/
```

Purpose:

- Provide compact CSV summaries for quick inspection.
- Mirror common analytical questions before or alongside DuckDB SQL.

Current summary files:

| Summary | Rows |
| --- | ---: |
| `sample_domain_counts.csv` | 9 |
| `organism_group_counts.csv` | 9 |
| `sample_context_counts.csv` | 7 |
| `sample_domain_context_counts.csv` | 39 |
| `attribute_category_counts.csv` | 39 |
| `library_strategy_counts.csv` | 21 |

### 7. Validate Quality

```powershell
nexumics-validate-sra-lake
```

Output:

```text
data/quality/sra/sra-local-lake-quality-report.csv
```

Current result:

| Metric | Count |
| --- | ---: |
| Quality checks | 17 |
| Passed | 17 |
| Failed | 0 |

## Current Quality Checks

The current quality report verifies:

| Check | Purpose |
| --- | --- |
| `silver_sra_run_exists` | Ensure `sra_run.csv` exists. |
| `silver_sra_sample_exists` | Ensure `sra_sample.csv` exists. |
| `silver_sra_sample_attribute_exists` | Ensure `sra_sample_attribute.csv` exists. |
| `silver_sra_sample_classification_exists` | Ensure `sra_sample_classification.csv` exists. |
| `sra_run_run_accession_unique` | Ensure `run_accession` is non-empty and unique. |
| `sra_sample_sample_accession_unique` | Ensure `sample_accession` is non-empty and unique. |
| `sra_classification_sample_accession_unique` | Ensure each sample has one classification row. |
| `sra_sample_classification_matches_samples` | Ensure sample count matches classification count. |
| `sra_sample_attribute_required_fields_present` | Ensure required sample attribute fields are present. |
| `sra_sample_domain_allowed_values` | Ensure domains are controlled vocabulary values. |
| `sra_unknown_sample_count_below_threshold` | Ensure unknown samples stay below either the absolute threshold or the proportional threshold. |
| `gold_sra_domain_summary_exists` | Ensure Gold domain summary exists. |
| `gold_sra_context_summary_exists` | Ensure Gold context summary exists. |
| `gold_sra_domain_library_strategy_summary_exists` | Ensure Gold domain/library summary exists. |
| `gold_sra_top_organisms_by_domain_exists` | Ensure Gold top organisms summary exists. |
| `gold_sra_attribute_category_by_domain_exists` | Ensure Gold attribute category summary exists. |
| `gold_sra_quality_summary_exists` | Ensure Gold quality summary exists. |

The current unknown sample count is 56, or 0.074% of classified samples. This passes because the quality gate now allows either a small absolute count or a low proportional rate for larger local lakes.

## Current Gold Snapshot

The current `sra_domain_summary` result is:

| Domain | Samples | Runs | Attributes |
| --- | ---: | ---: | ---: |
| `metagenome` | 16,665 | 17,899 | 273,614 |
| `animal` | 15,934 | 21,911 | 153,037 |
| `microorganism` | 14,081 | 14,867 | 179,407 |
| `human` | 10,897 | 14,288 | 118,845 |
| `virus` | 4,954 | 5,094 | 46,702 |
| `plant` | 4,947 | 5,139 | 63,816 |
| `protist` | 4,512 | 5,105 | 46,072 |
| `fungi` | 3,746 | 5,475 | 31,941 |
| `unknown` | 56 | 62 | 714 |

## Querying With DuckDB

Versioned SQL queries are available under:

```text
sql/sra/
sql/gold/sra/
```

Example:

```powershell
python -c "import duckdb, pathlib; con = duckdb.connect(':memory:'); print(con.execute(pathlib.Path('sql/gold/sra/domain_summary.sql').read_text()).fetchdf())"
```

## Design Notes

- Bronze is traceable and close to parsed SRA XML.
- Silver is normalized, deduplicated, and classification-aware.
- Silver Parquet is the optimized analytical representation of Silver.
- Gold contains analysis-ready aggregate tables.
- Quality checks are intentionally simple and local-first.
- DuckDB is the local query engine; PostgreSQL and Metabase can come later.

## Next Steps

1. Add more Gold tables, such as top organisms by domain and top attribute categories by domain.
2. Add stricter quality checks for row-count consistency between Bronze, Silver, and Gold.
3. Add taxonomy enrichment from NCBI Taxonomy instead of expanding taxon allowlists manually.
4. Add orchestration with Dagster after the local command remains stable.
5. Expand data coverage only after quality checks and Gold outputs are ready to absorb new batches.
