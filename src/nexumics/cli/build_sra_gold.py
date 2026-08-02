"""Build first-pass Gold SRA analytical tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.sra_gold import build_sra_gold_tables


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build first-pass SRA Gold analytical tables with DuckDB.")
    parser.add_argument(
        "--input-dir",
        default="data/silver/sra/parquet",
        help="Directory containing SRA Silver Parquet tables.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/gold/sra/parquet",
        help="Directory for SRA Gold Parquet outputs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    counts = build_sra_gold_tables(input_dir=Path(args.input_dir), output_dir=Path(args.output_dir))

    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    for table_name, row_count in counts.items():
        print(f"{table_name}.parquet: {row_count} rows")


if __name__ == "__main__":
    main()
