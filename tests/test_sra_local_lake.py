import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_local_lake import build_sra_local_lake, quality_passed


@unittest.skipIf(importlib.util.find_spec("duckdb") is None, "duckdb is not installed")
class SraLocalLakeTests(unittest.TestCase):
    def test_build_sra_local_lake_runs_complete_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bronze_batch_dir = root / "bronze" / "batches"
            batch_dir = bronze_batch_dir / "test-human-rnaseq"
            batch_dir.mkdir(parents=True)
            self.write_csv(
                batch_dir / "sra-bronze-batch-000001.csv",
                [
                    "experiment_accession",
                    "run_accession",
                    "study_accession",
                    "bioproject_accession",
                    "sample_accession",
                    "biosample_accession",
                    "organism",
                    "taxon_id",
                    "library_strategy",
                    "library_source",
                    "library_selection",
                    "library_layout",
                    "platform",
                    "instrument_model",
                    "total_spots",
                    "total_bases",
                ],
                [
                    {
                        "experiment_accession": "SRX1",
                        "run_accession": "SRR1",
                        "study_accession": "SRP1",
                        "bioproject_accession": "PRJNA1",
                        "sample_accession": "SRS1",
                        "biosample_accession": "SAMN1",
                        "organism": "Homo sapiens",
                        "taxon_id": "9606",
                        "library_strategy": "RNA-Seq",
                        "library_source": "TRANSCRIPTOMIC",
                        "library_selection": "cDNA",
                        "library_layout": "PAIRED",
                        "platform": "ILLUMINA",
                        "instrument_model": "NovaSeq 6000",
                        "total_spots": "10",
                        "total_bases": "1000",
                    }
                ],
            )
            self.write_csv(
                batch_dir / "sra-sample-attributes-batch-000001.csv",
                [
                    "sample_accession",
                    "biosample_accession",
                    "attribute_name",
                    "attribute_value",
                    "normalized_attribute_name",
                    "attribute_category",
                ],
                [
                    {
                        "sample_accession": "SRS1",
                        "biosample_accession": "SAMN1",
                        "attribute_name": "sex",
                        "attribute_value": "female",
                        "normalized_attribute_name": "sex",
                        "attribute_category": "clinical",
                    }
                ],
            )

            result = build_sra_local_lake(
                bronze_batch_dir=bronze_batch_dir,
                bronze_combined_dir=root / "bronze" / "combined",
                silver_dir=root / "silver",
                silver_parquet_dir=root / "silver_parquet",
                silver_summary_dir=root / "summary",
                gold_parquet_dir=root / "gold_parquet",
                quality_report_path=root / "quality" / "report.csv",
            )

            self.assertEqual(result["bronze_run_count"], 1)
            self.assertEqual(result["bronze_attribute_count"], 1)
            self.assertEqual(result["silver_counts"]["sra_sample_classification"], 1)
            self.assertEqual(result["gold_counts"]["sra_domain_summary"], 1)
            self.assertTrue(quality_passed(result["quality_checks"]))
            self.assertTrue((root / "quality" / "report.csv").exists())

    def write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
