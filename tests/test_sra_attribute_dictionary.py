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

    def test_categorize_attribute(self) -> None:
        self.assertEqual(categorize_attribute("env_biome"), "environment")
        self.assertEqual(categorize_attribute("env_broad_scale"), "environment")
        self.assertEqual(categorize_attribute("env_medium"), "environment")
        self.assertEqual(categorize_attribute("host"), "host")
        self.assertEqual(categorize_attribute("clinical_status"), "clinical")
        self.assertEqual(categorize_attribute("unexpected"), "other")

    def test_known_attribute_names_exposes_dictionary_terms(self) -> None:
        names = known_attribute_names()

        self.assertIn("age", names)
        self.assertIn("env_broad_scale", names)
        self.assertEqual(set(ATTRIBUTE_CATEGORY_MAP["host"]), {"host", "host_taxid", "host_disease", "host_body_site"})
