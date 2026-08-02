"""Update the local NCBI Taxonomy reference table from Silver SRA samples."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from nexumics.taxonomy_reference import update_taxonomy_reference


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update the local NCBI Taxonomy reference table.")
    parser.add_argument("--sample-path", default="data/silver/sra/sra_sample.csv")
    parser.add_argument("--output-path", default="data/reference/ncbi_taxonomy/taxonomy_reference.csv")
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--rebuild", action="store_true", help="Ignore any existing reference and rebuild from input IDs.")
    parser.add_argument("--email", default=os.getenv("NCBI_EMAIL"), help="Contact email for NCBI E-utilities.")
    parser.add_argument("--api-key", default=os.getenv("NCBI_API_KEY"), help="Optional NCBI API key.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.email:
        raise SystemExit("Provide --email or set NCBI_EMAIL before calling NCBI E-utilities.")

    summary = update_taxonomy_reference(
        sample_path=Path(args.sample_path),
        output_path=Path(args.output_path),
        email=args.email,
        api_key=args.api_key,
        batch_size=args.batch_size,
        rebuild=args.rebuild,
    )

    print(f"Input taxon IDs: {summary.input_taxon_ids}")
    print(f"Existing taxon IDs: {summary.existing_taxon_ids}")
    print(f"Fetched taxon IDs: {summary.fetched_taxon_ids}")
    print(f"Output taxon IDs: {summary.output_taxon_ids}")
    print(f"Output path: {summary.output_path}")


if __name__ == "__main__":
    main()
