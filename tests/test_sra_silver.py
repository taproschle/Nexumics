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
            {
                "sample_accession": "SRS_RAT",
                "biosample_accession": "SAMN_RAT",
                "organism": "Rattus norvegicus",
                "taxon_id": "10116",
                "source_dataset": "single-cell-rnaseq",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_TOBACCO",
                "biosample_accession": "SAMN_TOBACCO",
                "organism": "Nicotiana tabacum",
                "taxon_id": "4097",
                "source_dataset": "amplicon-16s",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_SILKWORM",
                "biosample_accession": "SAMN_SILKWORM",
                "organism": "Bombyx mori",
                "taxon_id": "7091",
                "source_dataset": "single-cell-rnaseq",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_OYSTER",
                "biosample_accession": "SAMN_OYSTER",
                "organism": "Magallana gigas",
                "taxon_id": "29159",
                "source_dataset": "single-cell-rnaseq",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_YEAST",
                "biosample_accession": "SAMN_YEAST",
                "organism": "Saccharomyces paradoxus",
                "taxon_id": "27291",
                "source_dataset": "single-cell-rnaseq",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_FOX",
                "biosample_accession": "SAMN_FOX",
                "organism": "Vulpes lagopus",
                "taxon_id": "494514",
                "source_dataset": "single-cell-rnaseq",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_JEJUIBACTER",
                "biosample_accession": "SAMN_JEJUIBACTER",
                "organism": "Jejuibacter sp. L23",
                "taxon_id": "3092086",
                "source_dataset": "single-cell-rnaseq",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_CATTLE",
                "biosample_accession": "SAMN_CATTLE",
                "organism": "Bos taurus",
                "taxon_id": "9913",
                "source_dataset": "cattle-rnaseq-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_PLASMODIUM",
                "biosample_accession": "SAMN_PLASMODIUM",
                "organism": "Plasmodium falciparum",
                "taxon_id": "5833",
                "source_dataset": "apicomplexa-rnaseq-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_TOXOPLASMA",
                "biosample_accession": "SAMN_TOXOPLASMA",
                "organism": "Toxoplasma gondii",
                "taxon_id": "5811",
                "source_dataset": "apicomplexa-rnaseq-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_GREGARINE",
                "biosample_accession": "SAMN_GREGARINE",
                "organism": "Anthozoaphila gnarlus",
                "taxon_id": "2783686",
                "source_dataset": "apicomplexa-rnaseq-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_KLEBSIELLA",
                "biosample_accession": "SAMN_KLEBSIELLA",
                "organism": "Klebsiella pneumoniae",
                "taxon_id": "573",
                "source_dataset": "long-read-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_BAKER_YEAST",
                "biosample_accession": "SAMN_BAKER_YEAST",
                "organism": "Saccharomyces cerevisiae",
                "taxon_id": "4932",
                "source_dataset": "long-read-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_WILDLIFE",
                "biosample_accession": "SAMN_WILDLIFE",
                "organism": "Lacerta agilis",
                "taxon_id": "80427",
                "source_dataset": "long-read-5000",
                "source_file": "runs.csv",
            },
            {
                "sample_accession": "SRS_UNIDENTIFIED",
                "biosample_accession": "SAMN_UNIDENTIFIED",
                "organism": "unidentified",
                "taxon_id": "32644",
                "source_dataset": "long-read-5000",
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
        self.assertEqual(by_sample["SRS_RAT"]["sample_domain"], "animal")
        self.assertEqual(by_sample["SRS_TOBACCO"]["organism_group"], "Viridiplantae")
        self.assertEqual(by_sample["SRS_TOBACCO"]["sample_domain"], "plant")
        self.assertEqual(by_sample["SRS_SILKWORM"]["sample_domain"], "animal")
        self.assertEqual(by_sample["SRS_OYSTER"]["sample_domain"], "animal")
        self.assertEqual(by_sample["SRS_YEAST"]["organism_group"], "Fungi")
        self.assertEqual(by_sample["SRS_YEAST"]["sample_domain"], "fungi")
        self.assertEqual(by_sample["SRS_FOX"]["sample_domain"], "animal")
        self.assertEqual(by_sample["SRS_JEJUIBACTER"]["organism_group"], "Bacteria")
        self.assertEqual(by_sample["SRS_JEJUIBACTER"]["sample_domain"], "microorganism")
        self.assertEqual(by_sample["SRS_CATTLE"]["sample_domain"], "animal")
        self.assertEqual(by_sample["SRS_PLASMODIUM"]["organism_group"], "Protists")
        self.assertEqual(by_sample["SRS_PLASMODIUM"]["sample_domain"], "protist")
        self.assertEqual(by_sample["SRS_TOXOPLASMA"]["sample_domain"], "protist")
        self.assertEqual(by_sample["SRS_GREGARINE"]["sample_domain"], "protist")
        self.assertEqual(by_sample["SRS_KLEBSIELLA"]["organism_group"], "Bacteria")
        self.assertEqual(by_sample["SRS_KLEBSIELLA"]["sample_domain"], "microorganism")
        self.assertEqual(by_sample["SRS_BAKER_YEAST"]["organism_group"], "Fungi")
        self.assertEqual(by_sample["SRS_BAKER_YEAST"]["sample_domain"], "fungi")
        self.assertEqual(by_sample["SRS_WILDLIFE"]["sample_domain"], "animal")
        self.assertEqual(by_sample["SRS_UNIDENTIFIED"]["sample_domain"], "unknown")

    def write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
