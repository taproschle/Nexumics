import csv
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_quality import validate_sra_lake, write_quality_report


class SraQualityTests(unittest.TestCase):
    def test_validate_sra_lake_passes_expected_minimal_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silver_dir = root / "silver"
            gold_dir = root / "gold"
            silver_dir.mkdir()
            gold_dir.mkdir()
            self.write_valid_silver_tables(silver_dir)
            for table_name in (
                "sra_domain_summary",
                "sra_context_summary",
                "sra_domain_library_strategy_summary",
            ):
                (gold_dir / f"{table_name}.parquet").write_text("placeholder", encoding="utf-8")

            checks = validate_sra_lake(silver_dir=silver_dir, gold_dir=gold_dir, max_unknown_samples=1)

            self.assertTrue(all(check.status == "pass" for check in checks))

    def test_validate_sra_lake_fails_unexpected_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silver_dir = root / "silver"
            silver_dir.mkdir()
            self.write_valid_silver_tables(silver_dir, sample_domain="mystery")

            checks = validate_sra_lake(silver_dir=silver_dir)
            failed_checks = {check.name for check in checks if check.status == "fail"}

            self.assertIn("sra_sample_domain_allowed_values", failed_checks)

    def test_write_quality_report_writes_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silver_dir = root / "silver"
            silver_dir.mkdir()
            self.write_valid_silver_tables(silver_dir)
            checks = validate_sra_lake(silver_dir=silver_dir)

            count = write_quality_report(root / "report.csv", checks)

            self.assertEqual(count, len(checks))
            self.assertTrue((root / "report.csv").exists())

    def write_valid_silver_tables(self, silver_dir: Path, sample_domain: str = "human") -> None:
        self.write_csv(
            silver_dir / "sra_run.csv",
            ["run_accession", "sample_accession"],
            [{"run_accession": "SRR1", "sample_accession": "SRS1"}],
        )
        self.write_csv(
            silver_dir / "sra_sample.csv",
            ["sample_accession", "biosample_accession", "organism", "taxon_id"],
            [{"sample_accession": "SRS1", "biosample_accession": "SAMN1", "organism": "Homo sapiens", "taxon_id": "9606"}],
        )
        self.write_csv(
            silver_dir / "sra_sample_attribute.csv",
            ["sample_accession", "normalized_attribute_name", "attribute_category"],
            [{"sample_accession": "SRS1", "normalized_attribute_name": "sex", "attribute_category": "clinical"}],
        )
        self.write_csv(
            silver_dir / "sra_sample_classification.csv",
            ["sample_accession", "sample_domain"],
            [{"sample_accession": "SRS1", "sample_domain": sample_domain}],
        )

    def write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
