import os
import unittest
from unittest import mock

from nexumics.metabase_dashboards import (
    DASHBOARDS,
    DEFAULT_METABASE_URL,
    MetabaseApiError,
    load_metabase_config_from_env,
    normalize_sql,
)


class MetabaseDashboardDefinitionTests(unittest.TestCase):
    def test_dashboard_definitions_have_cards(self) -> None:
        self.assertEqual(
            [
                "Nexumics Lake Overview",
                "Biological Diversity Explorer",
                "Sequencing Strategy & Metadata Quality",
            ],
            [dashboard.name for dashboard in DASHBOARDS],
        )

        for dashboard in DASHBOARDS:
            self.assertGreater(len(dashboard.cards), 0)
            for card in dashboard.cards:
                self.assertIn("gold_sra.", card.query)
                self.assertGreater(card.size_x, 0)
                self.assertGreater(card.size_y, 0)

    def test_normalize_sql_strips_indentation(self) -> None:
        query = """
            SELECT sample_domain
            FROM gold_sra.sra_domain_summary;
        """

        self.assertEqual(
            "SELECT sample_domain\nFROM gold_sra.sra_domain_summary;",
            normalize_sql(query),
        )

    def test_env_config_requires_credentials(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MetabaseApiError):
                load_metabase_config_from_env()

    def test_env_config_uses_defaults(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"METABASE_EMAIL": "admin@example.com", "METABASE_PASSWORD": "secret"},
            clear=True,
        ):
            config = load_metabase_config_from_env()

        self.assertEqual(DEFAULT_METABASE_URL, config["base_url"])
        self.assertEqual("admin@example.com", config["email"])
        self.assertEqual("secret", config["password"])
        self.assertEqual("Nexumics Gold", config["database_name"])
        self.assertEqual("Nexumics SRA Gold", config["collection_name"])


if __name__ == "__main__":
    unittest.main()
