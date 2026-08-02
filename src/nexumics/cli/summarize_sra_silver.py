"""Summarize local SRA Silver CSV tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.sra_silver_summary import summarize_sra_silver


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize local SRA Silver tables.")
    parser.add_argument("--input-dir", default="data/silver/sra", help="Directory containing SRA Silver CSV tables.")
    parser.add_argument(
        "--output-dir",
        default="data/silver/sra/summary",
        help="Directory for SRA Silver summary CSV outputs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    counts = summarize_sra_silver(input_dir=Path(args.input_dir), output_dir=Path(args.output_dir))

    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    for filename, row_count in counts.items():
        print(f"{filename}: {row_count} rows")


if __name__ == "__main__":
    main()
