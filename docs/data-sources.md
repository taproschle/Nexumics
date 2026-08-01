# Data Sources

This document tracks the data source strategy for Nexumics. It should be updated whenever source access patterns, API assumptions, or ingestion priorities change.

## Initial Decision

Nexumics will start with NCBI Entrez E-utilities as the first source access layer.

This is the preferred starting point because E-utilities provide a stable HTTP interface into the Entrez database system, including databases that are central to the Nexumics domain: SRA, BioProject, BioSample, GEO DataSets, and GEO Profiles.

## Why NCBI Entrez First

- It gives the project one consistent API style before adding source-specific clients.
- It supports search, summary, fetch, and linking workflows that map naturally to a metadata ingestion pipeline.
- It covers several planned Nexumics sources through Entrez database names such as `sra`, `bioproject`, `biosample`, `gds`, and `geoprofiles`.
- It allows a small first milestone: search a database, retrieve identifiers, fetch summaries, and persist raw responses.
- It makes cross-database linking possible through Entrez links, which is important for connecting SRA, BioProject, BioSample, and GEO metadata.

## Official References

- [Entrez Programming Utilities Help](https://www.ncbi.nlm.nih.gov/sites/books/NBK25501/)
- [E-utilities Quick Start](https://www.ncbi.nlm.nih.gov/books/NBK25500/)
- [A General Introduction to the E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
- [The E-utilities In-Depth: Parameters, Syntax and More](https://www.ncbi.nlm.nih.gov/books/NBK25499/)
- [NCBI API key support article](https://support.nlm.nih.gov/kbArticle/?pn=KA-05317)
- [NCBI E-utilities usage policy support article](https://support.nlm.nih.gov/kbArticle/?pn=KA-05510)

## E-utilities Base URL

All E-utilities requests should use the NCBI E-utilities base URL:

```text
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

## Relevant Entrez Databases

| Nexumics Domain | Entrez Database Name | Initial Role |
| --- | --- | --- |
| SRA | `sra` | Sequencing experiment and run metadata. |
| BioProject | `bioproject` | Project-level grouping and study context. |
| BioSample | `biosample` | Sample-level metadata and biological material descriptions. |
| GEO DataSets | `gds` | GEO dataset and study-level metadata. |
| GEO Profiles | `geoprofiles` | GEO expression/profile records, likely secondary for the first milestone. |

## Core E-utilities To Evaluate

| Utility | Purpose In Nexumics |
| --- | --- |
| `einfo` | Inspect available Entrez databases and supported fields/links. |
| `esearch` | Search a database and retrieve matching UIDs. |
| `esummary` | Retrieve compact document summaries for matching UIDs. |
| `efetch` | Retrieve fuller records when available and appropriate. |
| `elink` | Discover relationships between databases, such as SRA to BioProject or BioProject to BioSample. |

## Access And Rate-Limit Notes

NCBI E-utilities can be used without an API key, but request throughput is limited. Current NCBI support guidance describes a default limit of up to 3 requests per second, with up to 10 requests per second when using an API key.

For Nexumics, the ingestion client should:

- Support an optional `NCBI_API_KEY` environment variable.
- Send a `tool` parameter identifying the project.
- Send an `email` parameter for responsible API usage.
- Apply conservative rate limiting even during local development.
- Retry transient failures with backoff.
- Persist raw responses before transformation.

## First Discovery Questions

The first implementation spike should answer:

1. Which Entrez database should be queried first for the smallest end-to-end demo?
2. What fields are available from `esummary` for `sra`, `bioproject`, `biosample`, and `gds`?
3. Which links are available between SRA, BioProject, BioSample, and GEO DataSets?
4. Which response format should be used for the raw layer: XML, JSON, or both?
5. What minimal record identity should be preserved across raw, bronze, and silver layers?

## Proposed First Milestone

Start with a small NCBI Entrez discovery client that can:

1. Call `einfo` for the relevant databases.
2. Run a small `esearch` query against one selected database.
3. Retrieve `esummary` output for a limited number of records.
4. Save raw responses locally under a future ignored data directory.
5. Document the observed fields and links before building transformations.

## Current Decision

Use NCBI Entrez E-utilities as the first source access layer.

The first implementation should remain intentionally small and educational. The goal is to understand the API shape and metadata relationships before designing the full ingestion package.
