from pathlib import Path
import tempfile
import unittest

from nexumics.postgres_gold_loader import (
    SRA_GOLD_POSTGRES_SCHEMA,
    qualified_table_name,
    quote_identifier,
    validate_gold_inputs,
)
from nexumics.sra_gold import SRA_GOLD_TABLES


class PostgresGoldLoaderTests(unittest.TestCase):
    def test_gold_postgres_schema_covers_all_gold_tables(self) -> None:
        self.assertEqual(set(SRA_GOLD_POSTGRES_SCHEMA), set(SRA_GOLD_TABLES))

    def test_quote_identifier_escapes_double_quotes(self) -> None:
        self.assertEqual(quote_identifier('bad"name'), '"bad""name"')

    def test_qualified_table_name_quotes_schema_and_table(self) -> None:
        self.assertEqual(
            qualified_table_name("gold_sra", "sra_domain_summary"),
            '"gold_sra"."sra_domain_summary"',
        )

    def test_validate_gold_inputs_fails_when_table_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Missing required Gold Parquet table"):
                validate_gold_inputs(Path(tmp))

