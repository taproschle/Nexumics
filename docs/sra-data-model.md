# SRA Data Model

This document defines the intended SRA metadata model for Nexumics. It focuses on a robust structure that works across human, microorganism, host-associated, environmental, and metagenomic records.

## Design Principle

Do not model SRA metadata as if every sample were human.

Fields such as `age`, `sex`, and `tissue` are useful for human samples, but they are not universal. Microbial, viral, fungal, plant, animal, environmental, and metagenomic samples often use different attributes such as `strain`, `isolate`, `host`, `isolation_source`, `env_biome`, `env_feature`, or `env_material`.

The model should separate:

- universal SRA identifiers and technical metadata;
- flexible sample attributes;
- derived sample classification.

## Current Bronze Preview

The current `sra-bronze-preview` output is one row per SRA run and includes:

| Field | Meaning | Scope |
| --- | --- | --- |
| `experiment_accession` | SRA experiment accession, usually `SRX...`. | Universal |
| `run_accession` | SRA run accession, usually `SRR...`. | Universal |
| `study_accession` | SRA study accession, usually `SRP...`. | Universal |
| `bioproject_accession` | BioProject accession, usually `PRJNA...`. | Broad |
| `sample_accession` | SRA sample accession, usually `SRS...`. | Universal |
| `biosample_accession` | BioSample accession, usually `SAMN...`. | Broad |
| `organism` | Scientific organism name. | Universal |
| `taxon_id` | NCBI Taxonomy identifier. | Universal |
| `library_strategy` | Library strategy such as `RNA-Seq`, `WGS`, or `AMPLICON`. | Universal |
| `library_source` | Library source such as `TRANSCRIPTOMIC`, `GENOMIC`, or `METAGENOMIC`. | Universal |
| `library_selection` | Library selection method. | Broad |
| `library_layout` | Sequencing layout, for example `PAIRED` or `SINGLE`. | Universal |
| `platform` | Sequencing platform family, such as `ILLUMINA`. | Universal |
| `instrument_model` | Instrument model. | Broad |
| `total_spots` | Run spot count. | Run-level |
| `total_bases` | Run base count. | Run-level |

This is a good first preview, but it should not become the final silver model as a single wide table.

## Proposed Silver Entities

### `sra_study`

One row per SRA study.

| Field | Notes |
| --- | --- |
| `study_accession` | Primary key candidate. |
| `bioproject_accession` | External BioProject accession when present. |
| `study_title` | From SRA study descriptor. |
| `study_type` | From SRA study descriptor when present. |
| `study_abstract` | Useful for search and context. |

### `sra_experiment`

One row per SRA experiment.

| Field | Notes |
| --- | --- |
| `experiment_accession` | Primary key candidate. |
| `study_accession` | Foreign key candidate to `sra_study`. |
| `sample_accession` | Foreign key candidate to `sra_sample`. |
| `experiment_title` | Human-readable title. |
| `design_description` | Experimental design text. |
| `library_name` | Library name when present. |
| `library_strategy` | Sequencing strategy. |
| `library_source` | Source material category. |
| `library_selection` | Selection method. |
| `library_layout` | `PAIRED`, `SINGLE`, or other observed layout. |
| `platform` | Platform family. |
| `instrument_model` | Instrument model. |

### `sra_run`

One row per SRA run.

| Field | Notes |
| --- | --- |
| `run_accession` | Primary key candidate. |
| `experiment_accession` | Foreign key candidate to `sra_experiment`. |
| `total_spots` | Raw run-level count. |
| `total_bases` | Raw run-level count. |
| `size_bytes` | Run file or run payload size when available. |
| `published_at` | Run publication timestamp when available. |
| `is_public` | Public availability flag. |
| `load_done` | NCBI load completion flag. |
| `static_data_available` | Availability flag observed in run metadata. |

### `sra_sample`

One row per SRA sample.

| Field | Notes |
| --- | --- |
| `sample_accession` | Primary key candidate, usually `SRS...`. |
| `biosample_accession` | External BioSample accession, usually `SAMN...`. |
| `taxon_id` | NCBI Taxonomy identifier. |
| `organism` | Scientific organism name. |
| `biosample_model` | From sample attributes when present. |

### `sra_sample_attribute`

Flexible key-value table for all BioSample/SRA sample attributes.

| Field | Notes |
| --- | --- |
| `sample_accession` | Links back to `sra_sample`. |
| `biosample_accession` | Useful when joining across BioSample. |
| `attribute_name` | Original attribute tag from SRA XML. |
| `attribute_value` | Original attribute value from SRA XML. |
| `normalized_attribute_name` | Canonical project-level name when known. |
| `attribute_category` | Broad category such as host, environment, organism, clinical, technical, or other. |

This table is essential because sample attributes vary strongly across domains.

### `sra_sample_classification`

Derived classification table used for cross-domain filtering and analytics.

| Field | Notes |
| --- | --- |
| `sample_accession` | Links back to `sra_sample`. |
| `biosample_accession` | External BioSample accession. |
| `sample_domain` | Broad domain such as `human`, `animal`, `plant`, `microorganism`, `virus`, `environmental`, `metagenome`, or `unknown`. |
| `sample_context` | Context such as `host-associated`, `environmental`, `isolate`, `cell-line`, `tissue`, `clinical`, or `unknown`. |
| `organism_group` | Taxonomic group such as `Bacteria`, `Archaea`, `Eukaryota`, `Viruses`, or `unknown`. |
| `host_present` | Boolean derived from attributes such as `host`. |
| `classification_basis` | Short explanation of which fields supported the classification. |

## Attribute Classification Strategy

Sample attributes should first be preserved as raw key-value rows. Silver classification can then derive higher-level categories from observed attributes.

The current normalization and categorization rules live in:

```text
src/nexumics/sra_attribute_dictionary.py
```

The parser and combine command both use this module so classification behavior stays consistent across new XML parses and older local CSV recombination.

| Attribute Pattern | Possible Category | Example |
| --- | --- | --- |
| `age`, `sex`, `disease`, `clinical_*` | `clinical` | Human or clinical study metadata. |
| `tissue`, `cell_type`, `cell_line` | `host_material` | Tissue or cell source. |
| `host`, `host_taxid`, `host_disease` | `host` | Host-associated microbial or viral sample. |
| `strain`, `isolate`, `serovar`, `cultivar` | `organism_identity` | Microbial, viral, plant, or isolate-level identity. |
| `isolation_source`, `source_material_id` | `source_material` | Source material for isolate or environmental sample. |
| `geo_loc_name`, `lat_lon`, `collection_date` | `spatiotemporal` | Location and collection metadata. |
| `env_biome`, `env_broad_scale`, `env_feature`, `env_local_scale`, `env_material`, `env_medium`, `environmental_sample` | `environment` | Environmental and metagenomic context. |
| `BioSampleModel` | `schema_hint` | BioSample package/model hint. |

## Why This Shape Works

- Human-specific fields stay available without dominating the model.
- Microorganism and environmental metadata can be represented without schema changes.
- The raw attribute vocabulary is preserved for later reprocessing.
- Silver classification can improve over time as we inspect more sources.
- The model supports both narrow biological questions and broad data engineering demos.

## Implementation Priority

1. Add `sra_sample_attribute` extraction from `SAMPLE_ATTRIBUTES`. Done in the bronze preview pipeline.
2. Review sample attributes across human, bacterial, viral, metagenomic, and environmental examples.
3. Add title and description fields to the run preview or separated entities.
4. Add run status/date fields.
5. Add first-pass `sra_sample_classification` using simple rules.
6. Later enrich `organism_group` from NCBI Taxonomy instead of relying only on organism text.

## Open Questions

1. Should `sra_sample_classification` be generated immediately in bronze preview or only in silver?
2. Should `BioSampleModel` remain only as an attribute, or also be promoted into `sra_sample`?
3. Which classification values should be allowed in the first controlled vocabulary?
4. When should NCBI Taxonomy enrichment be introduced?
