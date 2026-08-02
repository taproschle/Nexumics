"""Profile SRA sample attributes from local bronze CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexumics.raw_storage import utc_timestamp
from nexumics.sra_attribute_profile import profile_sra_attributes, write_attribute_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profile SRA sample attributes from local bronze CSV files.")
    parser.add_argument(
        "--input-dir",
        default="data/bronze/sra",
        help="Directory containing SRA sample attribute bronze CSV files.",
    )
    parser.add_argument(
        "--pattern",
        default="sra-sample-attributes*.csv",
        help="Glob pattern searched recursively under input-dir.",
    )
    parser.add_argument(
        "--output-path",
        help="Output CSV path. Defaults to data/profiles/sra/sra-attribute-profile-<timestamp>.csv.",
    )
    parser.add_argument("--max-examples", type=int, default=5, help="Maximum example values per attribute.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_path = Path(args.output_path) if args.output_path else Path(
        "data/profiles/sra"
    ) / f"sra-attribute-profile-{utc_timestamp()}.csv"

    rows = profile_sra_attributes(
        input_dir=Path(args.input_dir),
        pattern=args.pattern,
        max_examples=args.max_examples,
    )
    write_attribute_profile(rows, output_path)

    other_count = sum(1 for row in rows if row.attribute_category == "other")
    print(f"Profiled attributes: {len(rows)}")
    print(f"Attributes categorized as other: {other_count}")
    print(f"Output profile: {output_path}")


if __name__ == "__main__":
    main()
