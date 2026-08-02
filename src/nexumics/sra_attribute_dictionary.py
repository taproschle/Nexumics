"""SRA sample attribute normalization and categorization rules."""

from __future__ import annotations

import re


ATTRIBUTE_CATEGORY_MAP: dict[str, frozenset[str]] = {
    "clinical": frozenset({"age", "sex", "disease"}),
    "host_material": frozenset({"tissue", "cell_type", "cell_line"}),
    "host": frozenset(
        {
            "host",
            "host_common_name",
            "host_disease",
            "host_health_state",
            "host_age",
            "host_associated",
            "host_body_product",
            "host_scientific_name",
            "host_sex",
            "host_subject_id",
            "host_taxid",
            "host_body_site",
            "lab_host",
            "specific_host",
        }
    ),
    "organism_identity": frozenset(
        {
            "breed",
            "common_name",
            "genotype",
            "isolate",
            "isolate_host",
            "isolate_name_alias",
            "mlst",
            "organism",
            "scientific_name",
            "serovar",
            "serotype",
            "strain",
            "tax_id",
            "type_material",
            "cultivar",
        }
    ),
    "source_material": frozenset(
        {
            "coll_site_geo_feat",
            "host_tissue_sampled",
            "isol_growth_condt",
            "isolation_source",
            "isolation_type",
            "source",
            "sample_type",
            "source_material_id",
            "source_type",
        }
    ),
    "spatiotemporal": frozenset(
        {
            "collection_date",
            "cult_isol_date",
            "geo_loc_name",
            "geographic_location",
            "geographic_location_country_and_or_sea",
            "geographic_location_region_and_locality",
            "lat_lon",
        }
    ),
    "environment": frozenset(
        {
            "env_biome",
            "env_broad_scale",
            "env_feature",
            "env_local_scale",
            "env_material",
            "env_medium",
            "environmental_sample",
        }
    ),
    "environmental_measurement": frozenset({"altitude", "depth", "elev", "samp_size", "temp"}),
    "schema_hint": frozenset({"biosamplemodel"}),
    "sample_identifier": frozenset(
        {
            "alias",
            "biosamples",
            "external_id",
            "sample_alias",
            "sample_name",
            "sample_title",
            "subject_id",
            "submitter_id",
            "title",
            "unique_identifier",
        }
    ),
    "submission_metadata": frozenset(
        {
            "author",
            "arrayexpress_species",
            "biomaterial_provider",
            "broker_name",
            "collected_by",
            "ena_first_public",
            "ena_last_update",
            "file_location",
            "identified_by",
            "insdc_center_alias",
            "insdc_center_name",
            "insdc_first_public",
            "insdc_last_update",
            "insdc_status",
            "num_replicons",
            "project_name",
            "ref_biomaterial",
            "sequenced_by",
        }
    ),
    "public_health_surveillance": frozenset({"purpose_of_sampling"}),
    "antimicrobial_resistance": frozenset({"carba_allel", "mic_meropenem"}),
    "molecular_typing": frozenset(
        {"locus_tag_prefix", "mlst_scheme", "mlst_type", "pubmlst_scheme", "sequence_type"}
    ),
    "culture_metadata": frozenset(
        {
            "aliqot",
            "culture_collection",
            "mating_type",
            "passage_history",
            "replicate",
            "replication",
            "specimen_voucher",
        }
    ),
    "facility_metadata": frozenset({"location_in_facility"}),
    "sample_quality": frozenset({"comment", "host_description", "potential_contaminant"}),
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

    return "other"


def known_attribute_names() -> frozenset[str]:
    names: set[str] = set()
    for category_names in ATTRIBUTE_CATEGORY_MAP.values():
        names.update(category_names)
    return frozenset(names)
