"""Export local SRA Silver CSV tables to Parquet."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.sra_parquet import export_sra_silver_parquet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export local SRA Silver CSV tables to Parquet with DuckDB.")
    parser.add_argument("--input-dir", default="data/silver/sra", help="Directory containing SRA Silver CSV tables.")
    parser.add_argument(
        "--output-dir",
        default="data/silver/sra/parquet",
        help="Directory for SRA Silver Parquet outputs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    counts = export_sra_silver_parquet(input_dir=Path(args.input_dir), output_dir=Path(args.output_dir))

    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    for table_name, row_count in counts.items():
        print(f"{table_name}.parquet: {row_count} rows")


if __name__ == "__main__":
    main()
