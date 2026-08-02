"""SRA sample attribute normalization and categorization rules."""

from __future__ import annotations

import re


ATTRIBUTE_CATEGORY_MAP: dict[str, frozenset[str]] = {
    "clinical": frozenset({"age", "sex", "disease"}),
    "host_material": frozenset({"tissue", "cell_type", "cell_line"}),
    "host": frozenset(
        {
            "add_host_info",
            "host",
            "host_age",
            "host_associated",
            "host_behaviour",
            "host_body_product",
            "host_body_site",
            "host_common_name",
            "host_disease",
            "host_habitat",
            "host_health_state",
            "host_age_normalized_years",
            "host_raw_meat_feeding",
            "host_scientific_name",
            "host_sex",
            "host_subject_id",
            "host_taxid",
            "lab_host",
            "specific_host",
            "host_disease_outcome",
        }
    ),
    "organism_identity": frozenset(
        {
            "breed",
            "common_name",
            "cultivar",
            "genotype",
            "isolate",
            "isolate_host",
            "isolate_name_alias",
            "mlst",
            "organism",
            "original_isolate_name",
            "species",
            "scientific_name",
            "serotype",
            "serovar",
            "strain",
            "subtype",
            "tax_id",
            "type_material",
            "virus_identifier",
        }
    ),
    "source_material": frozenset(
        {
            "coll_site_geo_feat",
            "collection_method",
            "concentration_method",
            "experimental_specimen_type",
            "extraction_method",
            "host_tissue_sampled",
            "isol_growth_condt",
            "isolation_source",
            "isolation_source_host_associated",
            "isolation_type",
            "local_sampling_context",
            "sample_type",
            "source",
            "source_material_id",
            "source_type",
            "sample_description",
            "type_details",
            "typedetails",
        }
    ),
    "spatiotemporal": frozenset(
        {
            "collection_date",
            "cult_isol_date",
            "geo_loc_name",
            "geographic_location",
            "geographical_location",
            "geographic_location_country_and_or_sea",
            "geographic_location_latitude",
            "geographic_location_longitude",
            "geographic_location_region_and_locality",
            "lat_lon",
            "latitude",
            "lattitude",
            "latitude_and_longitude",
            "longitude",
            "country",
            "country_of_birth",
            "receipt_date",
            "state",
            "time",
            "timepoint",
        }
    ),
    "environment": frozenset(
        {
            "animal_env",
            "broad_scale_environmental_context",
            "env_biome",
            "env_broad_scale",
            "env_feature",
            "env_local_scale",
            "env_material",
            "env_medium",
            "environmental_medium",
            "environmental_sample",
            "local_environmental_context",
            "soil_type",
            "wastewater_type",
        }
    ),
    "environmental_measurement": frozenset(
        {"altitude", "depth", "elev", "elevation", "osmolality_mosmkg", "samp_size", "temp"}
    ),
    "schema_hint": frozenset({"biosamplemodel"}),
    "sample_identifier": frozenset(
        {
            "alias",
            "bioproject_id",
            "biosamples",
            "external_id",
            "gisaid_accession",
            "gisaid_virus_name",
            "library_id",
            "ngdc_project_id",
            "ngdc_sample_id",
            "names",
            "patient_number",
            "assembled_sequence_accession",
            "donation_campaign",
            "donation_number",
            "sample_alias",
            "sample_name",
            "sample_title",
            "sequencing_identifier",
            "specimen_source_id",
            "subject_id",
            "submitter_id",
            "title",
            "unique_attribute",
            "unique_id",
            "unique_identifier",
            "origin_sample",
        }
    ),
    "submission_metadata": frozenset(
        {
            "arrayexpress_species",
            "author",
            "biomaterial_provider",
            "broker_name",
            "collected_by",
            "collecting_institution",
            "collector_name",
            "ena_first_public",
            "ena_last_update",
            "batch_nr",
            "file_location",
            "identified_by",
            "insdc_center_alias",
            "insdc_center_name",
            "insdc_first_public",
            "insdc_last_update",
            "insdc_status",
            "ngdc_release_date",
            "num_replicons",
            "project_name",
            "ref_biomaterial",
            "sequenced_by",
            "sequencing_run",
        }
    ),
    "public_health_surveillance": frozenset(
        {
            "purpose_of_sampling",
            "purpose_of_sequencing",
            "purpose_of_ww_sampling",
            "sample_capture_status",
            "study_phase",
        }
    ),
    "antimicrobial_resistance": frozenset({"amr_qc", "carba_allel", "mic_meropenem"}),
    "molecular_typing": frozenset(
        {"locus_tag_prefix", "mlst_scheme", "mlst_type", "phylogroup", "pubmlst_scheme", "sequence_type"}
    ),
    "genome_metadata": frozenset({"estimated_size", "extrachrom_elements", "genome_group"}),
    "pathogen_metadata": frozenset({"field_diagnosis", "pathogenicity", "pathotype"}),
    "sequencing_metadata": frozenset(
        {
            "filename_1",
            "filename_2",
            "seq_meth",
            "sequencing_data_link",
            "sequencing_reads_alignment_tool",
            "sequencing_reads_assembly_tool",
            "sequencing_reads_binning_tool",
        }
    ),
    "culture_metadata": frozenset(
        {
            "aliqot",
            "biological_replicate",
            "culture_collection",
            "extra_growth_cycles",
            "growth_medium",
            "mating_type",
            "passage_history",
            "propagation",
            "replicate",
            "replicate_line",
            "replication",
            "specimen_voucher",
        }
    ),
    "facility_metadata": frozenset({"location_in_facility", "sampling_location"}),
    "sample_quality": frozenset(
        {
            "comment",
            "extraction_control",
            "host_description",
            "pos_cont_type",
            "potential_contaminant",
            "sample_role",
            "sample_storage_conditions",
            "sequence_qc",
        }
    ),
    "viral_metadata": frozenset({"description", "source_uvig", "virus_enrich_appr", "virus_enrichment_approach"}),
    "serology_metadata": frozenset({"definition_for_seropositive_sample"}),
    "vaccination_metadata": frozenset(
        {"date_of_sars_cov_2_vaccination", "flu_vaccine_date", "prior_sars_cov_2_vaccination", "vaccine_received"}
    ),
    "experimental_design": frozenset(
        {
            "evolution_regime",
            "experimental_run",
            "osmotic_condition",
            "perturbation",
            "study_day",
            "tab",
            "target_gene",
            "treat",
            "group",
            "treatment_group",
        }
    ),
    "diet_metadata": frozenset(
        {
            "diet_type",
            "drinking_water_source",
            "fermented_increased",
            "gluten",
            "oils_frequency_oxalate",
            "oils_frequency_soy",
            "olive_oil",
            "types_of_plants",
            "whole_eggs",
        }
    ),
    "human_survey": frozenset(
        {
            "acid_reflux",
            "add_adhd",
            "age_cat",
            "alcohol_frequency",
            "antibiotic_history",
            "artificial_sweeteners",
            "autoimmune",
            "birth_control",
            "birth_year",
            "bmi_cat",
            "bowel_movement_frequency",
            "bowel_movement_quality",
            "contraceptive",
            "deodorant_use",
            "drinks_per_session",
            "exercise_location",
            "fed_as_infant",
            "fungal_overgrowth",
            "ibd",
            "ibs",
            "last_travel",
            "level_of_education",
            "lung_disease",
            "migraine",
            "race",
            "roommates",
            "sibo",
            "skin_condition",
            "sleep_duration",
            "thyroid",
            "vivid_dreams",
            "ethnicity",
            "host_body_habitat",
            "host_body_mass_index",
            "host_height",
            "host_weight",
            "host_diet",
            "illness_symptoms",
            "urine_collect_meth",
        }
    ),
    "sample_processing": frozenset(
        {
            "samp_collect_device",
            "samp_collect_method",
            "samp_mat_process",
            "sample_collection_temp",
            "sample_lysis_method",
            "sample_storage_duration",
            "sample_storage_temp_c",
            "nucleic_acid_extraction_kit_method",
            "nucl_acid_ext_ng_ul",
            "quality_control_trimming_software",
        }
    ),
    "animal_husbandry": frozenset(
        {"age_days", "breeds", "sampling_weight_kg", "weaning_age_days", "pig_housing_location", "pig_housing_type", "pig_location_sampling"}
    ),
    "omics_analysis": frozenset(
        {
            "pcr_primers",
            "statistical_analysis_metrics",
            "statistical_analysis_tools",
            "taxonomic_annotation_tools",
            "taxonomic_anotation_database",
        }
    ),
    "physiology_measurement": frozenset(
        {
            "dhea_sulfate",
            "fai",
            "fasting_glucose",
            "fasting_insulin",
            "free_testosterone",
            "hemoglobin_aonec",
            "homa_ir",
            "homa_ir_values",
            "ifg",
            "igt",
        }
    ),
    "wastewater_surveillance": frozenset(
        {
            "ww_population",
            "ww_sample_duration",
            "ww_sample_matrix",
            "ww_sample_site",
            "ww_sample_type",
            "ww_surv_jurisdiction",
            "ww_surv_system_sample_id",
            "ww_surv_target_1",
            "ww_surv_target_1_conc",
            "ww_surv_target_1_conc_unit",
            "ww_surv_target_1_gene",
            "ww_surv_target_1_known_present",
        }
    ),
    "food_metadata": frozenset(
        {
            "facility_type",
            "food_industry_class",
            "food_industry_code",
            "food_origin",
            "food_processing_method",
            "food_source",
            "food_type_processed",
            "ifsac_category",
            "intended_consumer",
        }
    ),
}

ATTRIBUTE_CATEGORY_PREFIXES: dict[str, tuple[str, ...]] = {
    "clinical": ("clinical_",),
    "environment": ("environment_", "local_scale_environmental_", "mfd_hab"),
    "food_metadata": ("food_",),
    "human_survey": ("covid_",),
    "sample_processing": ("sample_", "samp_", "nucl_acid_", "nucleic_acid_", "quality_control_"),
    "wastewater_surveillance": ("ww_",),
}

ATTRIBUTE_CATEGORY_SUFFIXES: dict[str, tuple[str, ...]] = {
    "human_survey": ("_cat", "_frequency"),
}


def normalize_attribute_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def categorize_attribute(normalized_name: str) -> str:
    for category, names in ATTRIBUTE_CATEGORY_MAP.items():
        if normalized_name in names:
            return category

    for category, prefixes in ATTRIBUTE_CATEGORY_PREFIXES.items():
        if normalized_name.startswith(prefixes):
            return category

    for category, suffixes in ATTRIBUTE_CATEGORY_SUFFIXES.items():
        if normalized_name.endswith(suffixes):
            return category

    return "other"


def known_attribute_names() -> frozenset[str]:
    names: set[str] = set()
    for category_names in ATTRIBUTE_CATEGORY_MAP.values():
        names.update(category_names)
    return frozenset(names)
