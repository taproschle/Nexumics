"""Run a small SRA metadata discovery flow."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from nexumics.entrez import EntrezClient, EntrezConfig, parse_esearch_ids
from nexumics.raw_storage import slugify, utc_timestamp, write_raw_response
from nexumics.sra_parser import parse_sra_efetch_xml, write_bronze_preview


DEFAULT_QUERY = "RNA-Seq[All Fields] AND Homo sapiens[Organism]"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a small SRA Entrez metadata discovery flow.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="SRA Entrez query.")
    parser.add_argument("--retmax", type=int, default=3, help="Maximum SRA UIDs to fetch.")
    parser.add_argument("--email", default=os.getenv("NCBI_EMAIL"), help="Contact email for NCBI E-utilities.")
    parser.add_argument("--api-key", default=os.getenv("NCBI_API_KEY"), help="Optional NCBI API key.")
    parser.add_argument("--output-dir", default="data", help="Local output directory ignored by Git.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.email:
        raise SystemExit("Provide --email or set NCBI_EMAIL before calling NCBI E-utilities.")

    timestamp = utc_timestamp()
    query_slug = slugify(args.query)
    raw_dir = Path(args.output_dir) / "raw" / "sra" / timestamp
    bronze_dir = Path(args.output_dir) / "bronze" / "sra"

    requests_per_second = 10.0 if args.api_key else 3.0
    client = EntrezClient(
        EntrezConfig(
            email=args.email,
            api_key=args.api_key,
            requests_per_second=requests_per_second,
        )
    )

    search_response = client.esearch(db="sra", term=args.query, retmax=args.retmax)
    search_stem = f"esearch-{query_slug}-{timestamp}"
    write_raw_response(search_response, output_dir=raw_dir, stem=search_stem, extension="json")

    ids = parse_esearch_ids(search_response)
    if not ids:
        raise SystemExit("No SRA UIDs returned for query.")

    fetch_response = client.efetch(db="sra", ids=ids, retmode="xml")
    fetch_stem = f"efetch-{query_slug}-{timestamp}"
    raw_xml_path = write_raw_response(fetch_response, output_dir=raw_dir, stem=fetch_stem, extension="xml")

    records = parse_sra_efetch_xml(fetch_response.text)
    preview_path = bronze_dir / f"sra-bronze-preview-{timestamp}.csv"
    write_bronze_preview(records, preview_path)

    print(f"SRA UIDs: {', '.join(ids)}")
    print(f"Raw XML: {raw_xml_path}")
    print(f"Bronze preview: {preview_path}")


if __name__ == "__main__":
    main()
