"""Build the complete local SRA lake from batch Bronze files."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.sra_local_lake import build_sra_local_lake, quality_passed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the complete local SRA lake.")
    parser.add_argument("--bronze-batch-dir", default="data/bronze/sra/batches")
    parser.add_argument("--bronze-combined-dir", default="data/bronze/sra/combined")
    parser.add_argument("--silver-dir", default="data/silver/sra")
    parser.add_argument("--silver-parquet-dir", default="data/silver/sra/parquet")
    parser.add_argument("--silver-summary-dir", default="data/silver/sra/summary")
    parser.add_argument("--gold-parquet-dir", default="data/gold/sra/parquet")
    parser.add_argument("--taxonomy-reference-path", default="data/reference/ncbi_taxonomy/taxonomy_reference.csv")
    parser.add_argument("--taxonomy-manifest-path", default="data/manifests/ncbi_taxonomy/taxonomy-reference-updates.jsonl")
    parser.add_argument("--quality-report-path", default="data/quality/sra/sra-local-lake-quality-report.csv")
    parser.add_argument("--max-unknown-samples", type=int, default=10)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = build_sra_local_lake(
        bronze_batch_dir=Path(args.bronze_batch_dir),
        bronze_combined_dir=Path(args.bronze_combined_dir),
        silver_dir=Path(args.silver_dir),
        silver_parquet_dir=Path(args.silver_parquet_dir),
        silver_summary_dir=Path(args.silver_summary_dir),
        gold_parquet_dir=Path(args.gold_parquet_dir),
        taxonomy_reference_path=Path(args.taxonomy_reference_path),
        taxonomy_manifest_path=Path(args.taxonomy_manifest_path),
        quality_report_path=Path(args.quality_report_path),
        max_unknown_samples=args.max_unknown_samples,
    )
    quality_checks = result["quality_checks"]

    print(f"Bronze run rows: {result['bronze_run_count']}")
    print(f"Bronze sample attribute rows: {result['bronze_attribute_count']}")
    print(f"Silver counts: {result['silver_counts']}")
    print(f"Silver Parquet counts: {result['silver_parquet_counts']}")
    print(f"Gold counts: {result['gold_counts']}")
    print(f"Silver summary counts: {result['silver_summary_counts']}")
    print(f"Quality report: {result['quality_report_path']}")
    print(f"Quality checks passed: {quality_passed(quality_checks)}")

    if not quality_passed(quality_checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
