"""Validate local SRA lake outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.sra_quality import validate_sra_lake, write_quality_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate local SRA lake outputs.")
    parser.add_argument("--silver-dir", default="data/silver/sra", help="Directory containing SRA Silver CSV tables.")
    parser.add_argument("--gold-dir", default="data/gold/sra/parquet", help="Directory containing SRA Gold Parquet tables.")
    parser.add_argument(
        "--report-path",
        default="data/quality/sra/sra-local-lake-quality-report.csv",
        help="CSV quality report output path.",
    )
    parser.add_argument("--max-unknown-samples", type=int, default=10, help="Maximum allowed unknown samples.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    checks = validate_sra_lake(
        silver_dir=Path(args.silver_dir),
        gold_dir=Path(args.gold_dir),
        max_unknown_samples=args.max_unknown_samples,
    )
    write_quality_report(Path(args.report_path), checks)
    failed = [check for check in checks if check.status == "fail"]

    print(f"Quality checks: {len(checks)}")
    print(f"Passed: {len(checks) - len(failed)}")
    print(f"Failed: {len(failed)}")
    print(f"Report: {args.report_path}")
    for check in failed:
        print(f"FAIL {check.name}: {check.message} observed={check.observed} expected={check.expected}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
