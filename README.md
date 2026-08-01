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
- [Project Brief](docs/project-brief.md)
- [Technical Design Document](docs/technical-design.md)
- [Project Brief DOCX](./_render_project_brief/Nexumics_Project_Brief.docx)
- [Technical Design DOCX](./_render_technical_design/Nexumics_Technical_Design_Document.docx)

## Repository Structure

```text
docs/
  project-brief.md
  technical-design.md
_render_project_brief/
  Nexumics_Project_Brief.docx
_render_technical_design/
  Nexumics_Technical_Design_Document.docx
```

## Current Status

The repository is in the initial documentation stage. The next natural milestones are:

1. Define the source code folder structure.
2. Establish the ingestion pipeline and raw storage layer.
3. Create the first bronze and silver transformations.
4. Add tests, validation, and observability.
5. Publish the first queryable gold layer.

## Repository Purpose

This repository is intended to show a complete, clear, and maintainable data engineering project. The priority is not only to move data, but also to create a well-documented foundation that can grow in an orderly way.
