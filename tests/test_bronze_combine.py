import csv
from pathlib import Path
import tempfile
import unittest

from nexumics.bronze_combine import combine_csv_files, normalize_sample_attribute_row


class BronzeCombineTests(unittest.TestCase):
    def test_combine_csv_files_adds_source_and_dedupes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "sra-bronze-preview-a.csv"
            second = root / "sra-bronze-preview-b.csv"
            fieldnames = ["experiment_accession", "run_accession", "organism"]

            for path, organism in ((first, "A"), (second, "B")):
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerow(
                        {
                            "experiment_accession": "SRX1",
                            "run_accession": "SRR1",
                            "organism": organism,
                        }
                    )

            output_path = root / "combined.csv"
            row_count = combine_csv_files(
                input_dir=root,
                pattern="sra-bronze-preview-*.csv",
                output_path=output_path,
                dedupe_key=("experiment_accession", "run_accession"),
            )

            with output_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(row_count, 1)
            self.assertEqual(rows[0]["source_dataset"], "root")
            self.assertEqual(rows[0]["source_file"], f"{first.name} | {second.name}")
            self.assertEqual(rows[0]["run_accession"], "SRR1")

    def test_combine_csv_files_recurses_and_merges_source_datasets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_dir = root / "dataset-a"
            second_dir = root / "dataset-b"
            first_dir.mkdir()
            second_dir.mkdir()
            fieldnames = ["experiment_accession", "run_accession", "organism"]

            for directory, organism in ((first_dir, "A"), (second_dir, "B")):
                path = directory / "sra-bronze-batch-000001.csv"
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerow(
                        {
                            "experiment_accession": "SRX1",
                            "run_accession": "SRR1",
                            "organism": organism,
                        }
                    )

            output_path = root / "combined.csv"
            row_count = combine_csv_files(
                input_dir=root,
                pattern="sra-bronze-batch-*.csv",
                output_path=output_path,
                dedupe_key=("experiment_accession", "run_accession"),
                recursive=True,
                source_dataset_root=root,
            )

            with output_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(row_count, 1)
            self.assertEqual(rows[0]["source_dataset"], "dataset-a | dataset-b")
            self.assertEqual(rows[0]["source_file"], "sra-bronze-batch-000001.csv")

    def test_normalize_sample_attribute_row_recomputes_category(self) -> None:
        row = {
            "attribute_name": "env broad scale",
            "attribute_value": "terrestrial biome",
            "normalized_attribute_name": "env_broad_scale",
            "attribute_category": "other",
        }

        normalized = normalize_sample_attribute_row(row)

        self.assertEqual(normalized["normalized_attribute_name"], "env_broad_scale")
        self.assertEqual(normalized["attribute_category"], "environment")
