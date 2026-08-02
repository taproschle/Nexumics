# AGENTS.md

This file gives programming agents the context required to continue work on Nexumics without losing the project direction. Read this file and `README.md` before making repository-level decisions.

## Project Context

Nexumics is an open-source data engineering project for ingesting, standardizing, and serving public omics metadata through a lakehouse-style architecture.

The project is intended to work as a production-minded portfolio project. It should demonstrate clean engineering judgment across ingestion, storage, transformation, validation, orchestration, testing, documentation, and presentation.

## Documentation Language

All repository-facing documentation must be written in English.

Spanish can be used in user conversation when the user writes in Spanish, but files intended for GitHub, maintainers, architecture notes, technical documentation, code comments, commit messages, and issue-style notes should stay in English unless the user explicitly changes that policy.

## Collaboration Style

The user wants to build this project step by step while understanding the decisions being made. Agents should explain meaningful implementation choices, especially:

- Why a tool, library, framework, or folder structure is being introduced.
- What tradeoffs were considered.
- How the change fits the lakehouse/data engineering goals.
- What should be discussed with the user before proceeding.

Do not rush through large scaffolding changes without context. Prefer small, understandable increments that the user can follow and review.

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

The repository now has a working local SRA metadata lake pipeline. The current versioned artifacts are:

- `README.md`: project entry point.
- `AGENTS.md`: public agent context and repository working guidelines.
- `docs/data-sources.md`: source access strategy and NCBI Entrez decision record.
- `docs/sra-metadata-discovery.md`: first SRA metadata inspection and design implications.
- `docs/sra-data-model.md`: SRA bronze/silver modeling strategy across humans, animals, plants, fungi, protists, microorganisms, viruses, and environmental/metagenomic samples.
- `docs/local-sra-pipeline.md`: implemented local rebuild flow from Bronze batches to Silver CSV, Silver Parquet, Gold Parquet, summaries, and quality reports.
- `docs/postgres-serving-layer.md`: first PostgreSQL serving layer for SRA Gold tables.
- `docs/metabase-dashboarding.md`: first local Metabase setup for visual dashboard exploration over PostgreSQL Gold tables.
- `docs/project-brief.md`: GitHub-readable project brief.
- `docs/technical-design.md`: GitHub-readable technical design document.
- `src/nexumics/`: Python package for Entrez access, raw storage, SRA parsing, SRA attribute dictionary rules, SRA attribute profiling, Bronze combining, local NCBI Taxonomy reference updates, Silver modeling, Parquet export, Gold analytics, quality checks, local pipeline rebuilds, and resumable SRA batch ingestion.
- `tests/`: unit tests for behavior that does not require network access.

Local DOCX render/export folders such as `_render_project_brief/` and `_render_technical_design/` are intentionally ignored by Git. Use the Markdown files in `docs/` as the versioned source for repository-visible documentation.

The code implements a small SRA discovery flow, a resumable SRA batch ingestion flow using Entrez History, and a full local rebuild command for already-downloaded SRA batch metadata.

## Current Priorities

1. Keep public repository documentation coherent and fully in English.
2. Use NCBI Entrez E-utilities as the first source access layer.
3. Define the source code structure before adding implementation files.
4. Establish the ingestion pipeline and raw storage layer.
5. Add bronze and silver transformations with explicit schemas.
6. Keep tests, validation checks, and observability as first-class project concerns.
7. Continue improving taxonomy-aware sample classification and attribute normalization as new domains are added.
8. Publish a first queryable serving layer through PostgreSQL or Metabase after the local Gold layer is stable.

## Agent Working Guidelines

- Read `README.md`, `AGENTS.md`, and the relevant files under `docs/` before making project-level decisions.
- Preserve the lakehouse layering language: raw, bronze, silver, gold.
- Treat NCBI Entrez E-utilities as the first source access layer unless the user explicitly revisits the decision.
- Treat SRA metadata discovery as the current first source exploration path.
- Keep `nexumics-sra-discovery` small: `esearch` for UIDs, `efetch` for XML, raw local persistence, and bronze CSV previews.
- Use `nexumics-sra-batch-ingest` for moderate SRA metadata pulls. It should use Entrez History, per-batch raw XML, per-batch bronze CSVs, and a JSONL manifest for resumability.
- Use `nexumics-update-ncbi-taxonomy-reference` after Silver samples exist to update `data/reference/ncbi_taxonomy/taxonomy_reference.csv` from observed `taxon_id` values. This command calls NCBI Taxonomy, should fetch only missing IDs unless `--rebuild` is explicitly used, and should preserve raw XML plus a JSONL manifest under `data/raw/ncbi_taxonomy/` and `data/manifests/ncbi_taxonomy/`.
- Use `nexumics-build-sra-local-lake` to rebuild local artifacts from existing Bronze batches. This command does not download new data.
- Use `nexumics-load-sra-gold-postgres` to publish Gold Parquet tables to PostgreSQL under the `gold_sra` schema. PostgreSQL is a serving layer, not the source of truth for raw/Bronze/Silver/Gold files.
- Use `docker compose up -d postgres metabase` to start the local serving and dashboard stack. In Metabase, connect to PostgreSQL with host `postgres`, not `localhost`, because both services run inside Docker Compose.
- Do not promote human-specific sample fields such as `age`, `sex`, and `tissue` into the universal SRA model without a flexible attribute strategy.
- Preserve `SAMPLE_ATTRIBUTES` as flexible key-value bronze records before deriving sample classifications.
- Keep `sra_sample_classification` conservative and evidence-based. Known sample domains currently include `human`, `animal`, `plant`, `fungi`, `protist`, `microorganism`, `virus`, `metagenome`, and `unknown`.
- Prefer lineage-derived classification from the local NCBI Taxonomy reference over adding more manual taxon allowlists. Keep heuristic fallback rules for missing taxon IDs and transparent behavior.
- Keep SRA sample attribute normalization and category rules centralized in `src/nexumics/sra_attribute_dictionary.py`.
- Use `nexumics-profile-sra-attributes` after batch runs to inspect observed attribute names, categories, frequencies, and example values before expanding the dictionary.
- Prefer small, well-scoped changes that make the project easier to understand.
- Do not introduce a framework or service unless it supports the planned stack or the user explicitly approves the change.
- Explain meaningful technical decisions in the user conversation before or while implementing them.
- Keep generated artifacts, render outputs, caches, and local environment files out of version control.
- Keep `_render_*` folders local-only unless the user explicitly changes the publishing policy.
- When creating code later, include tests for behavior that affects ingestion, transformations, validation, or schema contracts.
- Keep implementation examples reproducible from a fresh clone.

## Naming And Style

- Use clear English names for files, folders, classes, functions, and documentation sections.
- Prefer explicit names over abbreviations unless the abbreviation is standard in the data or omics domain.
- Keep Markdown concise and navigable.
- Use ASCII punctuation in repository files unless a source format requires otherwise.

## Local Companion Context

The user may keep an ignored local file named `AGENTS_LOCAL.md` for Spanish learning notes, decision records, and collaboration preferences. That file is intentionally not part of the public GitHub repository.

When a decision affects both public project direction and the user's learning context, update:

- `AGENTS.md` for durable public guidance in English.
- `AGENTS_LOCAL.md` for Spanish explanations, learning notes, and collaboration context.

## Open Decisions

- Final source code folder structure.
- First Entrez database to implement: `sra`, `bioproject`, `biosample`, `gds`, or `geoprofiles`.
- Initial refresh cadence: manual, scheduled batch, or orchestrated local run.
- Whether the first user-facing exploration layer should be Metabase only or include a lightweight app later.
- Whether cloud deployment belongs in the first milestone or a later extension.
