# Nexumics

Nexumics is an open-source data engineering project for ingesting, standardizing, and serving public omics metadata through a lakehouse-style architecture.

The goal is to build a production-minded portfolio project with traceable sources, reproducible transformations, explicit validation, observability, and an analysis-ready serving layer.

## What It Solves

- Integrates public metadata from GEO, SRA, ENA, BioProject, and BioSample.
- Normalizes heterogeneous records across raw, bronze, silver, and gold layers.
- Publishes analytical outputs to PostgreSQL for querying and exploration.
- Demonstrates orchestration, testing, data quality, and CI/CD practices.

## High-Level Architecture

```text
Source APIs -> Raw -> Bronze -> Silver -> Gold -> PostgreSQL -> Metabase
```

## Planned Stack

- Python
- Polars
- DuckDB
- PostgreSQL
- Dagster
- Docker
- Pandera
- pytest
- GitHub Actions
- Metabase

## Project Documentation

- [Agent Context](AGENTS.md)
- [Data Sources](docs/data-sources.md)
- [Multi-Source Architecture](docs/multi-source-architecture.md)
- [SRA Metadata Discovery](docs/sra-metadata-discovery.md)
- [SRA Data Model](docs/sra-data-model.md)
- [Local SRA Pipeline](docs/local-sra-pipeline.md)
- [PostgreSQL Serving Layer](docs/postgres-serving-layer.md)
- [Metabase Dashboarding](docs/metabase-dashboarding.md)
- [Project Brief](docs/project-brief.md)
- [Technical Design Document](docs/technical-design.md)

## Repository Structure

```text
pyproject.toml
src/
  nexumics/
    bronze_combine.py
    entrez.py
    postgres_gold_loader.py
    raw_storage.py
    metabase_dashboards.py
    sra_attribute_dictionary.py
    sra_attribute_profile.py
    sra_batch.py
    sra_gold.py
    sra_local_lake.py
    sra_parser.py
    sra_parquet.py
    sra_quality.py
    sra_silver.py
    sra_silver_summary.py
    taxonomy_reference.py
    cli/
      build_sra_local_lake.py
      build_sra_gold.py
      build_sra_silver.py
      combine_sra_bronze.py
      export_sra_silver_parquet.py
      load_sra_gold_postgres.py
      create_metabase_dashboards.py
      profile_sra_attributes.py
      summarize_sra_silver.py
      sra_batch_ingest.py
      sra_discovery.py
      update_ncbi_taxonomy_reference.py
      validate_sra_lake.py
sql/
  gold/
    sra/
      domain_summary.sql
      context_summary.sql
      domain_library_strategy_summary.sql
      top_organisms_by_domain.sql
      attribute_category_by_domain.sql
      quality_summary.sql
  sra/
    sample_domain_counts.sql
    sample_context_counts.sql
    sample_domain_context_counts.sql
    attribute_category_counts.sql
    library_strategy_counts.sql
    domain_library_strategy_counts.sql
tests/
docs/
  data-sources.md
  multi-source-architecture.md
  sra-metadata-discovery.md
  sra-data-model.md
  local-sra-pipeline.md
  postgres-serving-layer.md
  metabase-dashboarding.md
  project-brief.md
  technical-design.md
```

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Run tests:

```powershell
python -m unittest discover -s tests
```

Run a small SRA metadata discovery flow:

```powershell
$env:NCBI_EMAIL = "your-email@example.com"
nexumics-sra-discovery --retmax 3
```

The command writes raw Entrez responses and a bronze CSV preview under `data/`, which is intentionally ignored by Git.

Run a resumable SRA batch ingestion flow:

```powershell
$env:NCBI_EMAIL = "your-email@example.com"
nexumics-sra-batch-ingest --query "WGS[All Fields] AND bacteria[Organism]" --max-records 1000 --batch-size 200
```

For resumable reruns, pass the same job id:

```powershell
nexumics-sra-batch-ingest --query "WGS[All Fields] AND bacteria[Organism]" --max-records 1000 --batch-size 200 --job-id my-bacteria-test
```

The batch command uses Entrez History, writes one raw XML file per batch, writes per-batch bronze CSV files, and records batch status under `data/manifests/sra/`.

Current bronze batch outputs:

```text
data/bronze/sra/batches/<query-job-id>/sra-bronze-batch-<batch-number>.csv
data/bronze/sra/batches/<query-job-id>/sra-sample-attributes-batch-<batch-number>.csv
```

Combine local SRA bronze batches:

```powershell
nexumics-combine-sra-bronze
```

This writes deduplicated combined CSV files under:

```text
data/bronze/sra/combined/
```

Combined rows include `source_dataset` and `source_file` columns so overlapping queries can be traced back to the local batch folder that produced them. For sample attributes, the combine command recalculates normalized attribute names and categories with the current parser logic.

Build first-pass SRA Silver tables from the latest consolidated Bronze files:

```powershell
nexumics-build-sra-silver
```

This writes normalized CSV tables under:

```text
data/silver/sra/
```

The first Silver pass creates `sra_run.csv`, `sra_sample.csv`, `sra_sample_attribute.csv`, and `sra_sample_classification.csv`. These files are still local data artifacts and are intentionally ignored by Git.

Update the local NCBI Taxonomy reference from Silver SRA samples:

```powershell
$env:NCBI_EMAIL = "your-email@example.com"
nexumics-update-ncbi-taxonomy-reference
```

This reads unique `taxon_id` values from `data/silver/sra/sra_sample.csv`, fetches only missing IDs from NCBI Taxonomy, and writes:

```text
data/reference/ncbi_taxonomy/taxonomy_reference.csv
data/raw/ncbi_taxonomy/
data/manifests/ncbi_taxonomy/taxonomy-reference-updates.jsonl
```

The Silver classifier uses this local reference when it exists, then falls back to transparent heuristic rules for missing taxon IDs.

Summarize local SRA Silver tables:

```powershell
nexumics-summarize-sra-silver
```

This writes compact CSV summaries under:

```text
data/silver/sra/summary/
```

Current summaries include sample domains, organism groups, sample contexts, domain/context combinations, attribute categories, and library strategies.

Export SRA Silver tables to Parquet with DuckDB:

```powershell
nexumics-export-sra-silver-parquet
```

This writes optimized Parquet tables under:

```text
data/silver/sra/parquet/
```

The SQL files under `sql/sra/` query these Parquet outputs with DuckDB. For example:

```powershell
python -c "import duckdb, pathlib; con = duckdb.connect(':memory:'); print(con.execute(pathlib.Path('sql/sra/sample_domain_counts.sql').read_text()).fetchdf())"
```

Build first-pass SRA Gold analytical tables:

```powershell
nexumics-build-sra-gold
```

This reads Silver Parquet files and writes Gold Parquet tables under:

```text
data/gold/sra/parquet/
```

The first Gold pass creates domain, context, domain/library strategy, top-organism, attribute-category, and quality summary Parquet tables. Versioned SQL queries for these tables live under `sql/gold/sra/`.

Load SRA Gold tables into local PostgreSQL:

```powershell
docker compose up -d postgres
nexumics-load-sra-gold-postgres
```

This creates and reloads the `gold_sra` schema from `data/gold/sra/parquet/`. See `docs/postgres-serving-layer.md` for table details and verification SQL.

PostgreSQL-ready SQL examples live under:

```text
sql/postgres/gold_sra/
```

Start Metabase for local dashboard exploration:

```powershell
docker compose up -d postgres metabase
```

Then open:

```text
http://localhost:3001
```

Metabase should connect to PostgreSQL using host `postgres`, database `nexumics`, user `nexumics`, password `nexumics`, and schema `gold_sra`. See `docs/metabase-dashboarding.md`.

Create the first Metabase dashboard collection programmatically:

```powershell
$env:METABASE_EMAIL = "your-metabase-admin-email@example.com"
$env:METABASE_PASSWORD = "your-metabase-password"
nexumics-create-metabase-dashboards
```

If the shell does not recognize the command yet, reinstall the editable package with `python -m pip install -e .` or run:

```powershell
python -m nexumics.cli.create_metabase_dashboards
```

The command creates a `Nexumics SRA Gold` collection with overview, biological diversity, and sequencing strategy dashboards.

Run quality checks against local SRA lake outputs:

```powershell
nexumics-validate-sra-lake
```

This writes a CSV quality report under:

```text
data/quality/sra/
```

Build the full local SRA lake from existing batch Bronze files:

```powershell
nexumics-build-sra-local-lake
```

This runs Bronze consolidation, Silver CSV creation, Silver Parquet export, Gold Parquet creation, Silver summaries, and quality validation in one local pipeline.

Profile observed SRA sample attributes:

```powershell
nexumics-profile-sra-attributes
```

This writes a frequency profile under:

```text
data/profiles/sra/
```

Use this profile to decide which observed attributes should be added to the dictionary or promoted later into silver models.

## Current Status

The repository currently has a working local SRA metadata lake pipeline:

- resumable SRA batch ingestion;
- Bronze consolidation;
- Silver CSV modeling;
- local NCBI Taxonomy reference updates;
- Silver Parquet export;
- Gold Parquet analytical tables;
- quality validation;
- PostgreSQL Gold serving layer;
- Metabase local dashboarding.

The project is now ready to evolve from an SRA-first pipeline toward a modular multi-source architecture. GEO is the likely next pilot source because it can add study, sample, and platform metadata while linking back to SRA records.

The next natural milestones are:

1. Design the first GEO discovery flow without disrupting the working SRA pipeline.
2. Compare GEO and SRA ingestion needs before extracting shared abstractions.
3. Keep improving Gold tables and Metabase dashboards over the current SRA lake.
4. Introduce orchestration only after the manual local pipeline remains stable across more than one source.

## Repository Purpose

This repository is intended to show a complete, clear, and maintainable data engineering project. The priority is not only to move data, but also to create a well-documented foundation that can grow in an orderly way.
