# Nexumics Technical Design Document

Living technical specification for the Nexumics platform.

## Document Metadata

| Field | Details |
| --- | --- |
| Document status | Working draft |
| Purpose | Define the architecture, data flow, and engineering decisions that shape Nexumics. |
| Primary stack | Python, Polars, DuckDB, PostgreSQL, Dagster, Docker, Pandera, pytest, GitHub Actions, Metabase |
| Data sources | GEO, SRA, ENA, BioProject, and BioSample |
| Delivery style | Local-first, reproducible, and portfolio-ready |

## System Overview

Nexumics follows a layered lakehouse pattern. Public API and metadata responses land in a raw zone, are refined into bronze and silver representations, and then are curated into gold analytics tables that can be loaded into PostgreSQL for downstream consumption.

The main design goal is to keep each stage accountable for one type of transformation so the pipeline remains explainable and easy to test.

```text
APIs -> Raw JSON -> Bronze Parquet -> Silver Standardized -> Gold Analytics -> PostgreSQL -> Metabase
```

## Design Principles

- Reproducibility comes first: every transformation should be rerunnable from the documented source inputs.
- Quality is explicit: contracts, validations, and tests are part of the design rather than an afterthought.
- Observability matters: logs and metrics should make it obvious where a failure occurred and why.

## Data Sources

| Source | Role In The Platform | Primary Entities | Notes |
| --- | --- | --- | --- |
| GEO | Study and sample metadata entry point. | Series, samples, platforms | Useful for high-level experimental context and study grouping. |
| SRA | Sequencing run and experiment detail. | Experiments, runs, submissions | Provides deeper execution metadata and provenance. |
| ENA | Cross-reference and accession enrichment. | Accessions, sample links, run metadata | Helps align identifiers across repositories. |
| BioProject | Project-level aggregation. | Projects, linked studies, organism references | Supports broader experiment grouping. |
| BioSample | Sample-level normalization anchor. | Samples, attributes, organism context | Critical for consistent sample identity. |

## Lakehouse Layers

### Raw

Store source payloads as close to the original API response as possible so lineage and reprocessing remain available.

### Bronze

Parse raw responses into well-shaped records, preserve source identifiers, and standardize the basic file layout.

### Silver

Apply canonical naming, deduplication, cross-source linking, and data contracts that make the records trustworthy.

### Gold

Build analysis-ready tables and aggregates that are optimized for reporting, exploration, and downstream dashboards.

## Pipeline Flow

| Stage | Function | Implementation Notes |
| --- | --- | --- |
| Ingestion | Fetch public metadata and land it in raw storage. | Use source-specific adapters and capture timestamps, source identifiers, and error details. |
| Validation | Check payload shape and key fields. | Pandera or equivalent checks fail fast on malformed records. |
| Normalization | Convert source-specific records into shared schemas. | Polars transforms should be deterministic and easy to unit test. |
| Loading | Persist bronze, silver, and gold outputs. | DuckDB and Parquet support local development; PostgreSQL serves the curated layer. |
| Serving | Expose curated data to users and tools. | Metabase or an equivalent BI layer consumes the final warehouse tables. |

## Data Model

The operational model should preserve one record per source entity at the appropriate layer, while the analytics model should favor conformed dimensions and a small number of clean fact-like tables.

| Model Area | Representative Entities | Design Intent |
| --- | --- | --- |
| Operational | Raw payloads, source records, ingestion logs | Track exactly what arrived from each source and when. |
| Conformed dimensions | Study, sample, project, accession, organism | Provide consistent lookup keys across the platform. |
| Analytics outputs | Coverage summaries, counts, cross-source joins | Make the platform useful for exploration and reporting. |

## Technology Decisions

| Component | Choice And Rationale |
| --- | --- |
| Python | Primary implementation language for orchestration, adapters, and tests because it offers a broad ecosystem and readable code. |
| Polars | Fast dataframe layer for transformation work with a clean API and good performance on local development hardware. |
| DuckDB | Local analytical engine for fast iteration on Parquet and exploratory SQL without a heavy setup burden. |
| PostgreSQL | Curated serving store for stable query access and a familiar production-like data warehouse interface. |
| Dagster | Pipeline orchestration layer that makes asset lineage and job execution easier to understand. |
| Docker | Containerization so the environment can be reproduced consistently across machines. |
| Pandera and pytest | Validation and testing stack that keeps source contracts and transformations under control. |
| GitHub Actions | CI/CD automation for tests, linting, and repeatable release checks. |
| Metabase | Simple BI and exploration layer for an accessible end-user view of the curated data. |

## Quality And Observability

| Area | Approach |
| --- | --- |
| Validation | Schema and rule checks should run at ingestion and again after normalization so bad data is caught early. |
| Testing | Unit tests should cover adapters and transforms, while integration tests should prove that the pipeline can run end to end. |
| Logging | Logs should identify the source, stage, and accession or record set that triggered an issue. |
| Metrics | Record counts, failure counts, and freshness checks should make pipeline health visible. |
| Lineage | The project should preserve enough metadata to answer where a curated record came from and how it was derived. |

## Deployment And Operations

| Area | Planned Approach |
| --- | --- |
| Local development | Docker Compose provides the database, orchestration, and supporting services for repeatable local runs. |
| Packaging | The repository should include clear environment instructions and scripts for reproducible setup. |
| CI | GitHub Actions runs tests and validation checks on each meaningful change. |
| Promotion path | The project can begin with a local-first workflow and later extend to a cloud deployment if needed. |

## Twelve-Week Roadmap

| Window | Milestone | Outcome |
| --- | --- | --- |
| Weeks 1-2 | Repository foundation and environment setup. | The project structure, dependencies, and documentation conventions are in place. |
| Weeks 3-4 | First source ingestion and raw landing zone. | At least one public source can be fetched and stored reproducibly. |
| Weeks 5-6 | Bronze and silver transformations. | A shared schema begins to emerge across sources. |
| Weeks 7-8 | Data quality and tests. | Validation rules and test coverage make the pipeline safer to change. |
| Weeks 9-10 | Gold layer and PostgreSQL serving. | Curated data is queryable in a warehouse-style layout. |
| Weeks 11-12 | Documentation, observability, and demo polish. | The project is ready to present as a portfolio artifact. |

## Future Evolution

If the core platform is stable, the next natural enhancements are cloud deployment, dbt for modeling ergonomics, Spark for scale testing, OpenMetadata for richer lineage, and selective NLP enrichment for free-text metadata fields.

Those extensions should come after the baseline system is complete so the project keeps a clear story and does not become fragmented.

## Source Artifact

The editable DOCX version is stored at [`../_render_technical_design/Nexumics_Technical_Design_Document.docx`](../_render_technical_design/Nexumics_Technical_Design_Document.docx).
