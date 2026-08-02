import csv
import os
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_silver import build_silver_tables, latest_matching_file


class SraSilverTests(unittest.TestCase):
    def test_latest_matching_file_returns_most_recent_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "sra-bronze-combined-a.csv"
            newer = root / "sra-bronze-combined-b.csv"
            older.write_text("x\n", encoding="utf-8")
            newer.write_text("x\n", encoding="utf-8")
            os.utime(older, (1, 1))
            os.utime(newer, (2, 2))

            self.assertEqual(latest_matching_file(root, "sra-bronze-combined-*.csv"), newer)

    def test_build_silver_tables_projects_and_dedupes_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bronze_run_path = root / "sra-bronze-combined.csv"
            bronze_attribute_path = root / "sra-sample-attributes-combined.csv"
            output_dir = root / "silver"

            self.write_csv(
                bronze_run_path,
                [
                    "source_dataset",
                    "source_file",
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
                        "source_dataset": "dataset-a",
                        "source_file": "batch-1.csv",
                        "experiment_accession": "SRX1",
                        "run_accession": "SRR1",
                        "study_accession": "SRP1",
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
                    },
                    {
                        "source_dataset": "dataset-a",
                        "source_file": "batch-2.csv",
                        "experiment_accession": "SRX1",
                        "run_accession": "SRR1",
                        "study_accession": "SRP1",
                        "sample_accession": "SRS1",
                        "biosample_accession": "SAMN1",
                        "organism": "Homo sapiens",
                        "taxon_id": "9606",
                    },
                ],
            )
            self.write_csv(
                bronze_attribute_path,
                [
                    "source_dataset",
                    "source_file",
                    "sample_accession",
                    "biosample_accession",
                    "attribute_name",
                    "attribute_value",
                    "normalized_attribute_name",
                    "attribute_category",
                ],
                [
                    {
                        "source_dataset": "dataset-a",
                        "source_file": "batch-1.csv",
                        "sample_accession": "SRS1",
                        "biosample_accession": "SAMN1",
                        "attribute_name": "sex",
                        "attribute_value": "female",
                        "normalized_attribute_name": "sex",
                        "attribute_category": "clinical",
                    },
                    {
                        "source_dataset": "dataset-a",
                        "source_file": "batch-2.csv",
                        "sample_accession": "SRS1",
                        "biosample_accession": "SAMN1",
                        "attribute_name": "sex",
                        "attribute_value": "female",
                        "normalized_attribute_name": "sex",
                        "attribute_category": "clinical",
                    },
                ],
            )

            counts = build_silver_tables(
                bronze_run_path=bronze_run_path,
                bronze_attribute_path=bronze_attribute_path,
                output_dir=output_dir,
            )

            self.assertEqual(counts, {"sra_run": 1, "sra_sample": 1, "sra_sample_attribute": 1})
            self.assertEqual(len(self.read_csv(output_dir / "sra_run.csv")), 1)
            self.assertEqual(len(self.read_csv(output_dir / "sra_sample.csv")), 1)
            self.assertEqual(len(self.read_csv(output_dir / "sra_sample_attribute.csv")), 1)

    def write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
