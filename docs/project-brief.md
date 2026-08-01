# Nexumics Project Brief

Tagline: Connecting Public Omics Data

## Executive Summary

Nexumics is an open-source data engineering project focused on ingesting, standardizing, and serving public omics metadata through a layered analytics platform. The project is designed to look and behave like a production system: sources are tracked, transformations are reproducible, quality checks are explicit, and the resulting dataset can be explored through a warehouse and BI layer.

The near-term goal is to produce a credible portfolio project that demonstrates end-to-end engineering judgment, not just data collection. That means building a pipeline with clear contracts, durable storage layers, and a documented path from raw source data to analysis-ready outputs.

## Project Metadata

| Field | Details |
| --- | --- |
| Document status | Working draft |
| Audience | Project stakeholders, collaborators, and future contributors |
| Primary objective | Define the project direction, scope, and delivery expectations for Nexumics |
| Data domain | Public omics metadata from GEO, SRA, ENA, BioProject, and BioSample |
| Core stack | Python, Polars, DuckDB, PostgreSQL, Dagster, Docker, Pandera, pytest, GitHub Actions |

## Mission And Vision

### Mission

Create a transparent, reusable platform that consolidates public omics metadata into a form that is easier to query, compare, and analyze.

### Vision

Build a production-grade portfolio system that showcases modern data engineering practices across ingestion, modeling, orchestration, testing, quality, and delivery.

## Why This Project Matters

The public omics ecosystem is rich, but its metadata is spread across multiple repositories and naming conventions. A well-structured integration layer makes the information more accessible for analysis and reuse.

The project also serves as a practical demonstration of how to design a layered data platform with clear accountability at each stage of the pipeline.

As a portfolio artifact, Nexumics should communicate technical depth while remaining understandable to a reviewer who is not already familiar with omics data.

## Scope

| Area | Details |
| --- | --- |
| In scope | Automated ingestion of public metadata, normalization into a lakehouse-style layout, validation, serving through PostgreSQL, and exploration through Metabase or an equivalent BI layer. |
| Out of scope | Wet-lab experimentation, proprietary datasets, production-grade identity management, and real-time streaming infrastructure. |

## Success Criteria

| Outcome | How We Measure It | Target |
| --- | --- | --- |
| Source coverage | All five target repositories are represented in the pipeline. | Initial end-to-end ingestion path exists for each source. |
| Pipeline reliability | Jobs complete with explicit validation and retry behavior. | Failures are observable and diagnosable without manual guessing. |
| Data quality | Standardized records pass documented contract checks. | Quality rules are visible and repeatable. |
| Portfolio value | A reviewer can understand the architecture, stack, and tradeoffs. | Documentation and diagrams tell a coherent story. |

## Delivery Roadmap

| Phase | Focus | Exit Criteria |
| --- | --- | --- |
| 1. Foundation | Repository structure, conventions, environment setup, and baseline documentation. | The project can be cloned and understood quickly. |
| 2. Ingestion | Connect to public sources and capture raw responses with lineage. | Raw landing data is consistently reproducible. |
| 3. Standardization | Create bronze and silver layers with shared schemas and validation. | Core entities are normalized and testable. |
| 4. Serving | Load curated outputs into PostgreSQL and expose them to BI. | Analysis-ready tables can be queried end to end. |
| 5. Polish | Observability, documentation polish, and demo narrative. | The project is presentable as a portfolio artifact. |

## Risks And Dependencies

| Risk | Mitigation |
| --- | --- |
| Source schema drift or API changes | Use source-specific adapters, versioned contracts, and validation checks that fail loudly when upstream payloads change. |
| Inconsistent identifiers across repositories | Introduce canonical identifiers and mapping rules early in the silver layer. |
| Scope creep from too many nice-to-have features | Deliver in phases and keep the first release focused on the core pipeline story. |
| Ambiguous data licensing or source terms | Document source-specific usage notes and stay within public metadata boundaries. |

## Open Decisions

| Decision | Current Notes |
| --- | --- |
| Initial presentation layer | Confirm whether the first portfolio view should prioritize Metabase dashboards, a lightweight web app, or both. |
| Data refresh cadence | Decide whether the first release should run on a scheduled batch cadence or remain manually triggered. |
| Cloud path | Determine whether the public repo stays local-first or evolves into a cloud-hosted deployment in a later phase. |

## Source Artifact

The editable DOCX version is stored at [`../_render_project_brief/Nexumics_Project_Brief.docx`](../_render_project_brief/Nexumics_Project_Brief.docx).
