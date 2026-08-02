"""Run SRA metadata ingestion in resumable Entrez History batches."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from nexumics.sra_batch import SraBatchConfig, run_sra_batch_ingestion


DEFAULT_QUERY = "RNA-Seq[All Fields] AND Homo sapiens[Organism]"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run resumable SRA metadata batch ingestion.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="SRA Entrez query.")
    parser.add_argument("--batch-size", type=int, default=200, help="Records requested per EFetch batch.")
    parser.add_argument("--max-records", type=int, default=1000, help="Maximum records to fetch for this job.")
    parser.add_argument("--job-id", help="Stable job id for resumable reruns. Defaults to a UTC timestamp.")
    parser.add_argument("--email", default=os.getenv("NCBI_EMAIL"), help="Contact email for NCBI E-utilities.")
    parser.add_argument("--api-key", default=os.getenv("NCBI_API_KEY"), help="Optional NCBI API key.")
    parser.add_argument("--output-dir", default="data", help="Local output directory ignored by Git.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.email:
        raise SystemExit("Provide --email or set NCBI_EMAIL before calling NCBI E-utilities.")

    summary = run_sra_batch_ingestion(
        SraBatchConfig(
            query=args.query,
            email=args.email,
            api_key=args.api_key,
            output_dir=Path(args.output_dir),
            batch_size=args.batch_size,
            max_records=args.max_records,
            job_id=args.job_id,
        )
    )

    print(f"Job ID: {summary.job_id}")
    print(f"Query: {summary.query}")
    print(f"Total available: {summary.total_available}")
    print(f"Target records: {summary.target_records}")
    print(f"Completed batches: {summary.completed_batches}")
    print(f"Skipped batches: {summary.skipped_batches}")
    print(f"Run rows: {summary.run_rows}")
    print(f"Sample attribute rows: {summary.sample_attribute_rows}")
    print(f"Manifest: {summary.manifest_path}")


if __name__ == "__main__":
    main()
