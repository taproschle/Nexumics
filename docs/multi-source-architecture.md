# Multi-Source Architecture

This document records the decision to evolve Nexumics from an SRA-first pipeline into a modular multi-source metadata platform.

## Why This Matters

The current implementation is intentionally SRA-first. That was a good starting point because SRA provides rich sequencing metadata and natural links to BioSample, BioProject, GEO, organisms, library strategies, platforms, and sample attributes.

However, Nexumics is not meant to be an SRA-only project. The broader goal is to integrate public omics metadata across multiple repositories while preserving source lineage and producing unified analytical outputs.

The target architecture should support:

- SRA sequencing run and experiment metadata.
- GEO study, sample, and platform metadata.
- BioSample biological sample metadata.
- BioProject project-level context.
- ENA records as an additional or complementary source.

## Direction

The project should move from:

```text
SRA -> Bronze -> Silver -> Gold -> PostgreSQL -> Metabase
```

to:

```text
SRA        -> Bronze -> Silver -> Gold
GEO        -> Bronze -> Silver -> Gold
BioSample  -> Bronze -> Silver -> Gold
BioProject -> Bronze -> Silver -> Gold
ENA        -> Bronze -> Silver -> Gold
                         |
                         v
              Unified Gold -> PostgreSQL -> Metabase
```

## Source-Specific Versus Shared Layers

Each source can have source-specific raw, bronze, silver, and gold artifacts when the native records have different shapes.

Shared logic should live outside source-specific modules when it applies across sources, such as:

- raw response persistence;
- manifests and resumability;
- schema validation;
- taxonomy reference updates;
- quality checks;
- lake rebuild orchestration;
- PostgreSQL publishing;
- dashboard-facing Gold tables.

Source-specific logic should stay isolated when it depends on native source formats, such as:

- SRA XML parsing;
- GEO Series and Sample parsing;
- BioSample attribute parsing;
- BioProject project metadata parsing;
- source-specific Entrez query defaults.

## Proposed Code Organization

The existing SRA implementation should not be refactored all at once. The safer path is to introduce modular structure gradually.

A future organization could look like:

```text
src/nexumics/
  core/
  lake/
  quality/
  taxonomy/
  sources/
    sra/
    geo/
    biosample/
    bioproject/
    ena/
```

The first step should be documentation and small extraction of clearly shared utilities. Large moves should wait until a second source, likely GEO, exposes which abstractions are actually useful.

## Source Interface Concept

Each source module should eventually answer:

- How records are searched.
- How raw records are fetched.
- How raw responses are stored.
- How Bronze tables are produced.
- How Silver tables are standardized.
- How source-specific Gold tables are created.
- How records link to shared entities such as organisms, BioSample, BioProject, or GEO Series.
- Which quality checks apply.

This does not require a formal Python base class immediately. A documented convention is enough until at least two source implementations exist.

## GEO As The Next Pilot Source

GEO is a strong candidate for the second source because it adds study, sample, platform, and expression metadata while often linking back to SRA.

Useful GEO relationships include:

```text
GEO Series -> GEO Samples -> SRA Runs
BioProject -> BioSample -> SRA
```

Adding GEO would help Nexumics move from a sequencing-run metadata lake toward a broader public omics metadata graph.

## Implementation Principle

Do not perform a large structural rewrite before there is a second source.

The recommended path is:

1. Keep the current SRA pipeline stable.
2. Document the multi-source direction.
3. Add a minimal GEO discovery flow.
4. Compare SRA and GEO needs.
5. Extract only the abstractions that are proven useful.

This keeps the project understandable while still moving toward a scalable architecture.
