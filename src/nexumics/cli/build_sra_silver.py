"""Build first-pass SRA Silver tables from consolidated Bronze outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.sra_silver import build_silver_tables, latest_matching_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build first-pass SRA Silver tables.")
    parser.add_argument(
        "--bronze-dir",
        default="data/bronze/sra/combined",
        help="Directory containing consolidated SRA Bronze CSV files.",
    )
    parser.add_argument("--bronze-run-path", help="Optional explicit consolidated SRA run CSV.")
    parser.add_argument("--bronze-attribute-path", help="Optional explicit consolidated SRA sample attribute CSV.")
    parser.add_argument("--output-dir", default="data/silver/sra", help="Directory for Silver SRA outputs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    bronze_dir = Path(args.bronze_dir)
    bronze_run_path = (
        Path(args.bronze_run_path)
        if args.bronze_run_path
        else latest_matching_file(bronze_dir, "sra-bronze-combined-*.csv")
    )
    bronze_attribute_path = (
        Path(args.bronze_attribute_path)
        if args.bronze_attribute_path
        else latest_matching_file(bronze_dir, "sra-sample-attributes-combined-*.csv")
    )

    counts = build_silver_tables(
        bronze_run_path=bronze_run_path,
        bronze_attribute_path=bronze_attribute_path,
        output_dir=Path(args.output_dir),
    )

    print(f"Bronze run input: {bronze_run_path}")
    print(f"Bronze attribute input: {bronze_attribute_path}")
    print(f"Silver SRA runs: {counts['sra_run']}")
    print(f"Silver SRA samples: {counts['sra_sample']}")
    print(f"Silver SRA sample attributes: {counts['sra_sample_attribute']}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
