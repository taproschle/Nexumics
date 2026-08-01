# AGENTS.md

## Project Context

Nexumics is an open-source data engineering project for ingesting, standardizing, and serving public omics metadata through a lakehouse-style architecture.

The project is intended to work as a production-minded portfolio project. It should demonstrate clean engineering judgment across ingestion, storage, transformation, validation, orchestration, testing, documentation, and presentation.

## Documentation Language

All project-facing documentation must be written in English.

Spanish can be used in user conversation when the user writes in Spanish, but repository files, comments intended for maintainers, README content, architecture notes, and technical documentation should stay in English unless the user explicitly requests otherwise.

## High-Level Architecture

```text
APIs -> Raw JSON -> Bronze Parquet -> Silver Standardized -> Gold Analytics -> PostgreSQL -> Metabase
```

## Target Data Sources

- GEO
- SRA
- ENA
- BioProject
- BioSample

## Planned Stack

- Python for ingestion, transformation, orchestration glue, and tests.
- Polars for dataframe transformations.
- DuckDB for local analytical work over Parquet.
- PostgreSQL for the curated serving layer.
- Dagster for orchestration and asset lineage.
- Docker and Docker Compose for reproducible local environments.
- Pandera for data contracts and validation.
- pytest for automated testing.
- GitHub Actions for CI/CD.
- Metabase for dashboarding and data exploration.

## Repository Status

The repository is in the initial documentation stage. The current artifacts are:

- `README.md`: project entry point.
- `docs/project-brief.md`: GitHub-readable project brief.
- `docs/technical-design.md`: GitHub-readable technical design document.

Local DOCX render/export folders such as `_render_project_brief/` and `_render_technical_design/` are intentionally ignored by Git. Use the Markdown files in `docs/` as the versioned source for repository-visible documentation.

The codebase has not been scaffolded yet.

## Current Priorities

1. Keep the documentation coherent and fully in English.
2. Define the source code structure before adding implementation files.
3. Establish the ingestion pipeline and raw storage layer.
4. Add bronze and silver transformations with explicit schemas.
5. Add tests, validation checks, and observability as first-class project concerns.
6. Publish a first queryable gold layer through PostgreSQL.

## Agent Working Guidelines

- Read `README.md` and this file before making project-level decisions.
- Preserve the lakehouse layering language: raw, bronze, silver, gold.
- Prefer small, well-scoped changes that make the project easier to understand.
- Do not introduce a framework or service unless it supports the planned stack or the user explicitly approves the change.
- Keep generated artifacts, render outputs, caches, and local environment files out of version control.
- Keep `_render_*` folders local-only unless the user explicitly changes the publishing policy.
- When creating code later, include tests for behavior that affects ingestion, transformations, validation, or schema contracts.
- Keep implementation examples reproducible from a fresh clone.

## Naming And Style

- Use clear English names for files, folders, classes, functions, and documentation sections.
- Prefer explicit names over abbreviations unless the abbreviation is standard in the data or omics domain.
- Keep Markdown concise and navigable.
- Use ASCII punctuation in repository files unless a source format requires otherwise.

## Open Decisions

- Final source code folder structure.
- First repository/source adapter to implement.
- Initial refresh cadence: manual, scheduled batch, or orchestrated local run.
- Whether the first user-facing exploration layer should be Metabase only or include a lightweight app later.
- Whether cloud deployment belongs in the first milestone or a later extension.
