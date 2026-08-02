import csv
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_silver_summary import count_by_fields, summarize_sra_silver


class SraSilverSummaryTests(unittest.TestCase):
    def test_count_by_fields_sorts_by_count_descending(self) -> None:
        rows = [
            {"sample_domain": "human", "sample_context": "clinical"},
            {"sample_domain": "human", "sample_context": "clinical"},
            {"sample_domain": "animal", "sample_context": "tissue"},
        ]

        summary = count_by_fields(rows, ["sample_domain", "sample_context"])

        self.assertEqual(
            summary,
            [
                {"sample_domain": "human", "sample_context": "clinical", "count": "2"},
                {"sample_domain": "animal", "sample_context": "tissue", "count": "1"},
            ],
        )

    def test_summarize_sra_silver_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "silver"
            output_dir = root / "summary"
            input_dir.mkdir()

            self.write_csv(
                input_dir / "sra_sample_classification.csv",
                ["sample_accession", "sample_domain", "organism_group", "sample_context"],
                [
                    {
                        "sample_accession": "SRS1",
                        "sample_domain": "human",
                        "organism_group": "Eukaryota",
                        "sample_context": "clinical",
                    },
                    {
                        "sample_accession": "SRS2",
                        "sample_domain": "animal",
                        "organism_group": "Eukaryota",
                        "sample_context": "tissue",
                    },
                ],
            )
            self.write_csv(
                input_dir / "sra_sample_attribute.csv",
                ["sample_accession", "attribute_category"],
                [
                    {"sample_accession": "SRS1", "attribute_category": "clinical"},
                    {"sample_accession": "SRS1", "attribute_category": "clinical"},
                    {"sample_accession": "SRS2", "attribute_category": "host_material"},
                ],
            )
            self.write_csv(
                input_dir / "sra_run.csv",
                ["run_accession", "library_strategy"],
                [
                    {"run_accession": "SRR1", "library_strategy": "RNA-Seq"},
                    {"run_accession": "SRR2", "library_strategy": "WGS"},
                ],
            )

            counts = summarize_sra_silver(input_dir=input_dir, output_dir=output_dir)

            self.assertEqual(counts["sample_domain_counts.csv"], 2)
            self.assertEqual(counts["organism_group_counts.csv"], 1)
            self.assertEqual(counts["sample_context_counts.csv"], 2)
            self.assertEqual(counts["sample_domain_context_counts.csv"], 2)
            self.assertEqual(counts["attribute_category_counts.csv"], 2)
            self.assertEqual(counts["library_strategy_counts.csv"], 2)
            self.assertEqual(
                self.read_csv(output_dir / "attribute_category_counts.csv")[0],
                {"attribute_category": "clinical", "count": "2"},
            )

    def write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
