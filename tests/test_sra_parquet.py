import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_parquet import SRA_SILVER_TABLES, export_sra_silver_parquet, load_duckdb


class SraParquetTests(unittest.TestCase):
    def test_load_duckdb_reports_install_hint_when_missing(self) -> None:
        if importlib.util.find_spec("duckdb") is not None:
            self.skipTest("duckdb is installed")

        with self.assertRaisesRegex(RuntimeError, "python -m pip install -e"):
            load_duckdb()

    @unittest.skipIf(importlib.util.find_spec("duckdb") is None, "duckdb is not installed")
    def test_export_sra_silver_parquet_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "silver"
            output_dir = root / "parquet"
            input_dir.mkdir()
            for table_name in SRA_SILVER_TABLES:
                self.write_csv(
                    input_dir / f"{table_name}.csv",
                    ["sample_accession", "value"],
                    [{"sample_accession": "SRS1", "value": table_name}],
                )

            counts = export_sra_silver_parquet(input_dir=input_dir, output_dir=output_dir)

            self.assertEqual(counts, {table_name: 1 for table_name in SRA_SILVER_TABLES})
            for table_name in SRA_SILVER_TABLES:
                self.assertTrue((output_dir / f"{table_name}.parquet").exists())

    def write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
