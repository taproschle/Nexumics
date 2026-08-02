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

## First-Pass Silver Implementation

The first implemented Silver step builds three local CSV tables from the latest consolidated Bronze files:

```powershell
nexumics-build-sra-silver
```

Outputs are written under:

```text
data/silver/sra/
```

Implemented tables:

| Table | Source | Grain |
| --- | --- | --- |
| `sra_run.csv` | Consolidated SRA Bronze run rows. | One row per `run_accession`. |
| `sra_sample.csv` | Consolidated SRA Bronze run rows. | One row per `sample_accession`, falling back to `biosample_accession` if needed. |
| `sra_sample_attribute.csv` | Consolidated SRA sample attribute rows. | One row per sample, BioSample, normalized attribute, and value. |
| `sra_sample_classification.csv` | Silver samples plus sample attribute signals. | One row per sample with derived domain, organism group, and sample context. |

This first pass intentionally stays in CSV and uses only the Python standard library. DuckDB and Parquet should be introduced after the table shapes are reviewed and stable.

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
| `environment_present` | Boolean derived from environmental attribute categories. |
| `clinical_present` | Boolean derived from clinical attribute categories; interpreted together with sample domain. |
| `metagenome_present` | Boolean derived from metagenome assembly attributes. |
| `attribute_category_summary` | Compact count of attribute categories observed for the sample. |
| `classification_basis` | Short explanation of which fields supported the classification. |

The first implementation uses transparent heuristic rules. For example, `Homo sapiens` or taxon `9606` maps to `human`, source datasets containing viral, bacterial, archaeal, fungal, plant, or metagenomic signals help infer broad domains, and attribute categories such as `host`, `environment`, and `clinical` help infer context. Ambiguous fields remain conservative until stronger taxonomy enrichment is added.

## Attribute Classification Strategy

Sample attributes should first be preserved as raw key-value rows. Silver classification can then derive higher-level categories from observed attributes.

The current normalization and categorization rules live in:

```text
src/nexumics/sra_attribute_dictionary.py
```

The parser and combine command both use this module so classification behavior stays consistent across new XML parses and older local CSV recombination.

Observed attributes can be profiled with:

```powershell
nexumics-profile-sra-attributes
```

The profile counts each normalized attribute, records its current category, counts distinct values, and includes sample values. This gives a data-driven way to improve the dictionary instead of guessing categories upfront.

| Attribute Pattern | Possible Category | Example |
| --- | --- | --- |
| `age`, `sex`, `disease`, `clinical_*` | `clinical` | Human or clinical study metadata. |
| `tissue`, `cell_type`, `cell_line` | `host_material` | Tissue or cell source. |
| `host`, `host_taxid`, `host_disease`, `host_age`, `host_sex`, `host_subject_id`, `host_raw_meat_feeding` | `host` | Host-associated microbial or viral sample. |
| `strain`, `isolate`, `serovar`, `cultivar`, `scientific_name`, `tax_id`, `mlst`, `organism` | `organism_identity` | Microbial, viral, plant, or isolate-level identity. |
| `isolation_source`, `source_material_id`, `source_type`, `sample_type`, `isolation_type`, `collection_method`, `experimental_specimen_type`, `source` | `source_material` | Source material for isolate or environmental sample. |
| `geo_loc_name`, `lat_lon`, `collection_date`, `geographic_location_*` | `spatiotemporal` | Location and collection metadata. |
| `env_biome`, `env_broad_scale`, `env_feature`, `env_local_scale`, `env_material`, `env_medium`, `environmental_sample` | `environment` | Environmental and metagenomic context. |
| `depth`, `altitude`, `elev`, `temp`, `samp_size` | `environmental_measurement` | Physical or environmental measurements. |
| `BioSampleModel` | `schema_hint` | BioSample package/model hint. |
| `sample_name`, `sample_alias`, `submitter_id`, `title`, `external_id`, `subject_id`, `patient_number`, `sequencing_identifier` | `sample_identifier` | Sample-level aliases and submitter identifiers. |
| `author`, `collected_by`, `sequenced_by`, `project_name`, `INSDC_*`, `ENA_*` | `submission_metadata` | Submitter, sequencing center, project, and archive metadata. |
| `purpose_of_sampling` | `public_health_surveillance` | Surveillance or monitoring intent, common in pathogen datasets. |
| `mic_*`, `carba_*` | `antimicrobial_resistance` | Antimicrobial susceptibility or resistance-marker metadata. |
| `mlst_type`, `mlst_scheme`, `pubmlst_scheme`, `sequence_type`, `phylogroup`, `locus_tag_prefix` | `molecular_typing` | Typing schemes, sequence types, and related identifiers. |
| `estimated_size`, `extrachrom_elements` | `genome_metadata` | Genome size or extra-chromosomal element hints. |
| `pathogenicity`, `field_diagnosis` | `pathogen_metadata` | Pathogenicity or diagnosis-oriented pathogen context. |
| `culture_collection`, `passage_history`, `replicate`, `specimen_voucher`, `mating_type` | `culture_metadata` | Culture, voucher, replicate, or passage metadata. |
| `location_in_facility` | `facility_metadata` | Facility-local sampling or storage context. |
| `potential_contaminant`, `comment`, `host_description` | `sample_quality` | Quality flags, contamination notes, or descriptive caveats. |
| `food_*`, `facility_type`, `IFSAC+ Category`, `intended_consumer` | `food_metadata` | Food-source and food-safety context. |
| `source_uvig`, `virus_enrich_appr`, `virus_enrichment_approach` | `viral_metadata` | Viral enrichment, virome, or viral-specific context. |
| `date_of_sars_cov_2_vaccination`, `prior_sars_cov_2_vaccination`, `vaccine_received` | `vaccination_metadata` | Vaccination context observed in viral records. |
| `definition_for_seropositive_sample` | `serology_metadata` | Serology or seropositive case definition metadata. |
| `ww_*`, `purpose_of_ww_sampling` | `wastewater_surveillance` | Wastewater surveillance metadata. |
| `covid_*`, `*_frequency`, `*_cat`, survey fields | `human_survey` | Human survey, lifestyle, demographic, or health questionnaire metadata. |
| `diet_type`, `drinking_water_source`, `gluten`, `whole_eggs`, `oils_*` | `diet_metadata` | Diet and consumption metadata. |
| `samp_*`, `sample_*`, `nucleic_acid_*`, `quality_control_*` | `sample_processing` | Collection, extraction, lysis, storage, or preprocessing metadata. |
| `sequencing_*`, `filename_*`, `seq_meth` | `sequencing_metadata` | Sequencing files, methods, or workflow metadata. |
| `statistical_analysis_*`, `taxonomic_annotation_*`, `pcr_primers` | `omics_analysis` | Analysis methods, annotation tools, or assay targets. |
| `fasting_glucose`, `fasting_insulin`, `homa_ir`, hormone-related fields | `physiology_measurement` | Host physiology or biomarker measurements. |
| `pig_*`, `breeds`, `weaning_age_days`, `sampling_weight_kg` | `animal_husbandry` | Animal husbandry or livestock context. |
| `dev_stage`, `developmental_stage`, `plant_developmental_stage`, `lifestage` | `developmental_stage` | Developmental or life-stage metadata. |
| `plant_*`, `biological_material_*`, `material_source_*`, `ecotype`, `population` | `plant_metadata` | Plant accession, structure, growth, or source metadata. |
| `gap_*` | `controlled_access_metadata` | dbGaP controlled-access identifiers and consent metadata. |
| `microbial_biomass_meth`, `sieving`, `soil_type_meth`, fungal enrichment fields | `fungal_metadata` | Fungal, soil, or fungal-enrichment-specific metadata. |
| `metagenome_source`, `completeness_estimated`, `contamination_estimated`, assembly/mapping/quality methods | `metagenome_assembly` | MAG, SAG, binning, assembly, or metagenome-derived genome metadata. |
| `rel_to_oxygen`, `gram_staining`, `motility`, `cell_shape`, `temperature_optimum` | `microbial_phenotype` | Microbial physiology or phenotype metadata. |
| `gender`, `diagnosis`, `histological_type`, `tnm_stage`, `immune_phenotype` | `clinical` | Clinical, tumor, or patient/sample disease descriptors. |
| `library_platform`, `sequencinglane`, `assay_type`, `barcoding`, `kit` | `sequencing_metadata` | Single-cell or assay-specific sequencing workflow metadata. |
| `genetic_modification`, `chip_antibody`, `immunoprecipitate`, `repeat`, `protocol` | `experimental_design` | Perturbation, antibody, replicate, protocol, or treatment design metadata. |
| `time_hr`, `time_point`, `temperature`, `mating_status`, `cell_id` | mixed categories | Insect and developmental profiles introduce time, temperature, mating status, and cell identifiers. |

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
