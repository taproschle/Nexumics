"""Combine local SRA bronze preview CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.bronze_combine import (
    ATTRIBUTE_KEY,
    RUN_KEY,
    combine_csv_files,
    normalize_sample_attribute_row,
)
from nexumics.raw_storage import utc_timestamp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Combine local SRA bronze preview CSV files.")
    parser.add_argument(
        "--input-dir",
        default="data/bronze/sra/batches",
        help="Directory with per-query SRA bronze batch folders.",
    )
    parser.add_argument("--output-dir", default="data/bronze/sra/combined", help="Directory for combined outputs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    timestamp = utc_timestamp()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    run_count = combine_csv_files(
        input_dir=input_dir,
        pattern="sra-bronze-batch-*.csv",
        output_path=output_dir / f"sra-bronze-combined-{timestamp}.csv",
        dedupe_key=RUN_KEY,
        recursive=True,
        source_dataset_root=input_dir,
    )
    attribute_count = combine_csv_files(
        input_dir=input_dir,
        pattern="sra-sample-attributes-batch-*.csv",
        output_path=output_dir / f"sra-sample-attributes-combined-{timestamp}.csv",
        dedupe_key=ATTRIBUTE_KEY,
        row_transform=normalize_sample_attribute_row,
        recursive=True,
        source_dataset_root=input_dir,
    )

    print(f"Combined run rows: {run_count}")
    print(f"Combined sample attribute rows: {attribute_count}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
