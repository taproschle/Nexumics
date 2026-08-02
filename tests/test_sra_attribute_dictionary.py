import unittest

from nexumics.sra_attribute_dictionary import (
    ATTRIBUTE_CATEGORY_MAP,
    categorize_attribute,
    known_attribute_names,
    normalize_attribute_name,
)


class SraAttributeDictionaryTests(unittest.TestCase):
    def test_normalize_attribute_name(self) -> None:
        self.assertEqual(normalize_attribute_name("geo loc name"), "geo_loc_name")
        self.assertEqual(normalize_attribute_name("host-body-site"), "host_body_site")
        self.assertEqual(normalize_attribute_name(" env/broad scale "), "env_broad_scale")
        self.assertEqual(
            normalize_attribute_name("geographic location (country and/or sea)"),
            "geographic_location_country_and_or_sea",
        )
        self.assertEqual(normalize_attribute_name("IFSAC+ Category"), "ifsac_category")

    def test_categorize_attribute(self) -> None:
        self.assertEqual(categorize_attribute("env_biome"), "environment")
        self.assertEqual(categorize_attribute("env_broad_scale"), "environment")
        self.assertEqual(categorize_attribute("env_medium"), "environment")
        self.assertEqual(categorize_attribute("host"), "host")
        self.assertEqual(categorize_attribute("host_scientific_name"), "host")
        self.assertEqual(categorize_attribute("host_sex"), "host")
        self.assertEqual(categorize_attribute("source_type"), "source_material")
        self.assertEqual(categorize_attribute("source"), "source_material")
        self.assertEqual(categorize_attribute("sample_name"), "sample_identifier")
        self.assertEqual(categorize_attribute("sequenced_by"), "submission_metadata")
        self.assertEqual(categorize_attribute("purpose_of_sampling"), "public_health_surveillance")
        self.assertEqual(categorize_attribute("food_origin"), "food_metadata")
        self.assertEqual(categorize_attribute("mic_meropenem"), "antimicrobial_resistance")
        self.assertEqual(categorize_attribute("sequence_type"), "molecular_typing")
        self.assertEqual(categorize_attribute("depth"), "environmental_measurement")
        self.assertEqual(categorize_attribute("replicate"), "culture_metadata")
        self.assertEqual(categorize_attribute("location_in_facility"), "facility_metadata")
        self.assertEqual(categorize_attribute("potential_contaminant"), "sample_quality")
        self.assertEqual(categorize_attribute("clinical_status"), "clinical")
        self.assertEqual(categorize_attribute("unexpected"), "other")

    def test_known_attribute_names_exposes_dictionary_terms(self) -> None:
        names = known_attribute_names()

        self.assertIn("age", names)
        self.assertIn("env_broad_scale", names)
        self.assertIn("source_type", names)
        self.assertEqual(
            set(ATTRIBUTE_CATEGORY_MAP["host"]),
            {
                "host",
                "host_age",
                "host_associated",
                "host_body_site",
                "host_body_product",
                "host_common_name",
                "host_disease",
                "host_health_state",
                "host_scientific_name",
                "host_sex",
                "host_subject_id",
                "host_taxid",
                "lab_host",
                "specific_host",
            },
        )
