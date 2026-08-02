import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_gold import SRA_GOLD_TABLES, build_sra_gold_tables
from nexumics.sra_parquet import sql_string_literal


@unittest.skipIf(importlib.util.find_spec("duckdb") is None, "duckdb is not installed")
class SraGoldTests(unittest.TestCase):
    def test_build_sra_gold_tables_writes_expected_outputs(self) -> None:
        import duckdb

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "silver_parquet"
            output_dir = root / "gold_parquet"
            input_dir.mkdir()
            self.write_parquet(
                input_dir / "sra_run.parquet",
                [
                    {
                        "run_accession": "SRR1",
                        "sample_accession": "SRS1",
                        "experiment_accession": "SRX1",
                        "library_strategy": "RNA-Seq",
                        "total_spots": "10",
                        "total_bases": "1000",
                    },
                    {
                        "run_accession": "SRR2",
                        "sample_accession": "SRS2",
                        "experiment_accession": "SRX2",
                        "library_strategy": "WGS",
                        "total_spots": "20",
                        "total_bases": "2000",
                    },
                ],
            )
            self.write_parquet(
                input_dir / "sra_sample.parquet",
                [
                    {"sample_accession": "SRS1", "organism": "Homo sapiens", "taxon_id": "9606"},
                    {"sample_accession": "SRS2", "organism": "Escherichia coli", "taxon_id": "562"},
                ],
            )
            self.write_parquet(
                input_dir / "sra_sample_attribute.parquet",
                [
                    {"sample_accession": "SRS1", "attribute_category": "clinical"},
                    {"sample_accession": "SRS1", "attribute_category": "host_material"},
                    {"sample_accession": "SRS2", "attribute_category": "host"},
                ],
            )
            self.write_parquet(
                input_dir / "sra_sample_classification.parquet",
                [
                    {
                        "sample_accession": "SRS1",
                        "sample_domain": "human",
                        "organism_group": "Eukaryota",
                        "sample_context": "clinical",
                        "host_present": "False",
                        "environment_present": "False",
                        "clinical_present": "True",
                        "metagenome_present": "False",
                    },
                    {
                        "sample_accession": "SRS2",
                        "sample_domain": "microorganism",
                        "organism_group": "Bacteria",
                        "sample_context": "host-associated",
                        "host_present": "True",
                        "environment_present": "False",
                        "clinical_present": "False",
                        "metagenome_present": "False",
                    },
                ],
            )

            counts = build_sra_gold_tables(input_dir=input_dir, output_dir=output_dir)

            self.assertEqual(
                counts,
                {
                    "sra_domain_summary": 2,
                    "sra_context_summary": 2,
                    "sra_domain_library_strategy_summary": 2,
                    "sra_top_organisms_by_domain": 2,
                    "sra_attribute_category_by_domain": 3,
                    "sra_quality_summary": 1,
                },
            )
            for table_name in SRA_GOLD_TABLES:
                self.assertTrue((output_dir / f"{table_name}.parquet").exists())

            connection = duckdb.connect(":memory:")
            domain_rows = connection.execute(
                "SELECT sample_domain, sample_count, run_count, attribute_count "
                "FROM read_parquet(?) ORDER BY sample_domain",
                [str(output_dir / "sra_domain_summary.parquet")],
            ).fetchall()
            self.assertEqual(domain_rows, [("human", 1, 1, 2), ("microorganism", 1, 1, 1)])
            quality_rows = connection.execute(
                "SELECT sample_count, run_count, attribute_count, unknown_sample_count "
                "FROM read_parquet(?)",
                [str(output_dir / "sra_quality_summary.parquet")],
            ).fetchall()
            self.assertEqual(quality_rows, [(2, 2, 3, 0)])

    def write_parquet(self, path: Path, rows: list[dict[str, str]]) -> None:
        import duckdb

        csv_path = path.with_suffix(".csv")
        fieldnames = list(rows[0])
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        connection = duckdb.connect(":memory:")
        connection.execute(
            f"""
            COPY (
                SELECT *
                FROM read_csv_auto({sql_string_literal(csv_path)}, header = true, all_varchar = true)
            )
            TO {sql_string_literal(path)}
            (FORMAT PARQUET)
            """
        )
