"""End-to-end local SRA lake build pipeline."""

from __future__ import annotations

from pathlib import Path

from nexumics.bronze_combine import (
    ATTRIBUTE_KEY,
    RUN_KEY,
    combine_csv_files,
    normalize_sample_attribute_row,
)
from nexumics.raw_storage import utc_timestamp
from nexumics.sra_gold import build_sra_gold_tables
from nexumics.sra_parquet import export_sra_silver_parquet
from nexumics.sra_quality import QualityCheck, validate_sra_lake, write_quality_report
from nexumics.sra_silver import build_silver_tables
from nexumics.sra_silver_summary import summarize_sra_silver


def build_sra_local_lake(
    *,
    bronze_batch_dir: Path = Path("data/bronze/sra/batches"),
    bronze_combined_dir: Path = Path("data/bronze/sra/combined"),
    silver_dir: Path = Path("data/silver/sra"),
    silver_parquet_dir: Path = Path("data/silver/sra/parquet"),
    silver_summary_dir: Path = Path("data/silver/sra/summary"),
    gold_parquet_dir: Path = Path("data/gold/sra/parquet"),
    taxonomy_reference_path: Path = Path("data/reference/ncbi_taxonomy/taxonomy_reference.csv"),
    quality_report_path: Path = Path("data/quality/sra/sra-local-lake-quality-report.csv"),
    max_unknown_samples: int = 10,
) -> dict[str, object]:
    timestamp = utc_timestamp()
    bronze_run_path = bronze_combined_dir / f"sra-bronze-combined-{timestamp}.csv"
    bronze_attribute_path = bronze_combined_dir / f"sra-sample-attributes-combined-{timestamp}.csv"

    bronze_run_count = combine_csv_files(
        input_dir=bronze_batch_dir,
        pattern="sra-bronze-batch-*.csv",
        output_path=bronze_run_path,
        dedupe_key=RUN_KEY,
        recursive=True,
        source_dataset_root=bronze_batch_dir,
    )
    bronze_attribute_count = combine_csv_files(
        input_dir=bronze_batch_dir,
        pattern="sra-sample-attributes-batch-*.csv",
        output_path=bronze_attribute_path,
        dedupe_key=ATTRIBUTE_KEY,
        row_transform=normalize_sample_attribute_row,
        recursive=True,
        source_dataset_root=bronze_batch_dir,
    )

    silver_counts = build_silver_tables(
        bronze_run_path=bronze_run_path,
        bronze_attribute_path=bronze_attribute_path,
        output_dir=silver_dir,
        taxonomy_reference_path=taxonomy_reference_path,
    )
    silver_parquet_counts = export_sra_silver_parquet(input_dir=silver_dir, output_dir=silver_parquet_dir)
    gold_counts = build_sra_gold_tables(input_dir=silver_parquet_dir, output_dir=gold_parquet_dir)
    silver_summary_counts = summarize_sra_silver(input_dir=silver_dir, output_dir=silver_summary_dir)
    quality_checks = validate_sra_lake(
        silver_dir=silver_dir,
        gold_dir=gold_parquet_dir,
        max_unknown_samples=max_unknown_samples,
    )
    write_quality_report(quality_report_path, quality_checks)

    return {
        "bronze_run_path": bronze_run_path,
        "bronze_attribute_path": bronze_attribute_path,
        "bronze_run_count": bronze_run_count,
        "bronze_attribute_count": bronze_attribute_count,
        "silver_counts": silver_counts,
        "silver_parquet_counts": silver_parquet_counts,
        "gold_counts": gold_counts,
        "silver_summary_counts": silver_summary_counts,
        "quality_report_path": quality_report_path,
        "quality_checks": quality_checks,
    }


def quality_passed(checks: list[QualityCheck]) -> bool:
    return all(check.status == "pass" for check in checks)
