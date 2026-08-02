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
APIs -> Raw JSON -> Bronze Parquet -> Silver Standardized -> Gold Analytics -> PostgreSQL -> Metabase
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
- [SRA Metadata Discovery](docs/sra-metadata-discovery.md)
- [SRA Data Model](docs/sra-data-model.md)
- [Project Brief](docs/project-brief.md)
- [Technical Design Document](docs/technical-design.md)

## Repository Structure

```text
pyproject.toml
src/
  nexumics/
    entrez.py
    raw_storage.py
    sra_parser.py
    cli/
      sra_discovery.py
tests/
docs/
  data-sources.md
  sra-metadata-discovery.md
  sra-data-model.md
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

Current bronze outputs:

```text
data/bronze/sra/sra-bronze-preview-<query>-<timestamp>.csv
data/bronze/sra/sra-sample-attributes-preview-<query>-<timestamp>.csv
```

## Current Status

The repository is in the first SRA metadata discovery stage. The next natural milestones are:

1. Exercise the SRA discovery flow on a small query.
2. Review the raw XML, run-level bronze CSV, and sample-attribute bronze CSV.
3. Decide which SRA fields should be promoted into a first silver schema.
4. Add stronger validation around parsed bronze records.
5. Introduce orchestration only after the manual flow is well understood.

## Repository Purpose

This repository is intended to show a complete, clear, and maintainable data engineering project. The priority is not only to move data, but also to create a well-documented foundation that can grow in an orderly way.
