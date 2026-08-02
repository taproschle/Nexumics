import csv
import os
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_silver import (
    build_silver_tables,
    build_sra_sample_classification_rows,
    latest_matching_file,
)


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

            self.assertEqual(
                counts,
                {
                    "sra_run": 1,
                    "sra_sample": 1,
                    "sra_sample_attribute": 1,
                    "sra_sample_classification": 1,
                },
            )
            self.assertEqual(len(self.read_csv(output_dir / "sra_run.csv")), 1)
            self.assertEqual(len(self.read_csv(output_dir / "sra_sample.csv")), 1)
            self.assertEqual(len(self.read_csv(output_dir / "sra_sample_attribute.csv")), 1)
            self.assertEqual(len(self.read_csv(output_dir / "sra_sample_classification.csv")), 1)

    def test_build_sra_sample_classification_rows_classifies_contextual_domains(self) -> None:
        sample_rows = [
            {
                "sample_accession": "SRS_HUMAN",
                "biosample_accession": "SAMN_HUMAN",
                "organism": "Homo sapiens",
                "taxon_id": "9606",
                "source_dataset": "human-rnaseq",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_SOIL",
                "biosample_accession": "SAMN_SOIL",
                "organism": "soil metagenome",
                "taxon_id": "410658",
                "source_dataset": "metagenomic-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_ECOLI",
                "biosample_accession": "SAMN_ECOLI",
                "organism": "Escherichia coli",
                "taxon_id": "562",
                "source_dataset": "bacteria-wgs",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_RICKETTSIA",
                "biosample_accession": "SAMN_RICKETTSIA",
                "organism": "Candidatus Rickettsia sp.",
                "taxon_id": "123",
                "source_dataset": "metagenomic-5000 | bacteria-wgs",
                "source_file": "runs.csv",
            },
        ]
        attribute_rows = [
            {
                "sample_accession": "SRS_HUMAN",
                "biosample_accession": "SAMN_HUMAN",
                "attribute_name": "diagnosis",
                "attribute_value": "breast cancer",
                "normalized_attribute_name": "diagnosis",
                "attribute_category": "clinical",
            },
            {
                "sample_accession": "SRS_SOIL",
                "biosample_accession": "SAMN_SOIL",
                "attribute_name": "env_biome",
                "attribute_value": "soil biome",
                "normalized_attribute_name": "env_biome",
                "attribute_category": "environment",
            },
            {
                "sample_accession": "SRS_ECOLI",
                "biosample_accession": "SAMN_ECOLI",
                "attribute_name": "host",
                "attribute_value": "Homo sapiens",
                "normalized_attribute_name": "host",
                "attribute_category": "host",
            },
        ]

        rows = build_sra_sample_classification_rows(sample_rows, attribute_rows)
        by_sample = {row["sample_accession"]: row for row in rows}

        self.assertEqual(by_sample["SRS_HUMAN"]["sample_domain"], "human")
        self.assertEqual(by_sample["SRS_HUMAN"]["sample_context"], "clinical")
        self.assertEqual(by_sample["SRS_SOIL"]["sample_domain"], "metagenome")
        self.assertEqual(by_sample["SRS_SOIL"]["sample_context"], "environmental")
        self.assertEqual(by_sample["SRS_ECOLI"]["organism_group"], "Bacteria")
        self.assertEqual(by_sample["SRS_ECOLI"]["sample_domain"], "microorganism")
        self.assertEqual(by_sample["SRS_ECOLI"]["sample_context"], "host-associated")
        self.assertEqual(by_sample["SRS_RICKETTSIA"]["organism_group"], "Bacteria")
        self.assertEqual(by_sample["SRS_RICKETTSIA"]["sample_domain"], "microorganism")

    def write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
