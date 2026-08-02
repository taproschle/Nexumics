"""SRA sample attribute normalization and categorization rules."""

from __future__ import annotations


ATTRIBUTE_CATEGORY_MAP: dict[str, frozenset[str]] = {
    "clinical": frozenset({"age", "sex", "disease"}),
    "host_material": frozenset({"tissue", "cell_type", "cell_line"}),
    "host": frozenset({"host", "host_taxid", "host_disease", "host_body_site"}),
    "organism_identity": frozenset({"strain", "isolate", "serovar", "cultivar", "genotype"}),
    "source_material": frozenset({"isolation_source", "source_material_id"}),
    "spatiotemporal": frozenset({"geo_loc_name", "lat_lon", "collection_date"}),
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
    "schema_hint": frozenset({"biosamplemodel"}),
    "administrative": frozenset({"biomaterial_provider", "unique_identifier"}),
}

ATTRIBUTE_CATEGORY_PREFIXES: dict[str, tuple[str, ...]] = {
    "clinical": ("clinical_",),
}


def normalize_attribute_name(name: str) -> str:
    normalized = name.strip().lower()
    for old, new in ((" ", "_"), ("-", "_"), ("/", "_")):
        normalized = normalized.replace(old, new)
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
