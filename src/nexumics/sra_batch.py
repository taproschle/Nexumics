"""Batch SRA metadata ingestion using Entrez History."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from nexumics.entrez import EntrezClient, EntrezConfig, parse_esearch_history
from nexumics.raw_storage import slugify, utc_timestamp, write_raw_response
from nexumics.sra_parser import (
    parse_sra_efetch_xml,
    parse_sra_sample_attributes,
    write_bronze_preview,
    write_sample_attribute_preview,
)


@dataclass(frozen=True)
class SraBatchConfig:
    query: str
    email: str
    api_key: str | None = None
    output_dir: Path = Path("data")
    batch_size: int = 200
    max_records: int | None = 1000
    job_id: str | None = None


@dataclass(frozen=True)
class SraBatchSummary:
    job_id: str
    query: str
    query_slug: str
    total_available: int
    target_records: int
    completed_batches: int
    skipped_batches: int
    run_rows: int
    sample_attribute_rows: int
    manifest_path: Path


def iter_batch_windows(*, total_records: int, batch_size: int) -> list[tuple[int, int]]:
    if total_records < 0:
        raise ValueError("total_records must be non-negative")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return [
        (retstart, min(batch_size, total_records - retstart))
        for retstart in range(0, total_records, batch_size)
    ]


def run_sra_batch_ingestion(config: SraBatchConfig) -> SraBatchSummary:
    if not config.email:
        raise ValueError("email is required")
    if config.batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if config.max_records is not None and config.max_records <= 0:
        raise ValueError("max_records must be positive when provided")

    job_id = config.job_id or utc_timestamp()
    query_slug = slugify(config.query)
    output_dir = Path(config.output_dir)
    raw_dir = output_dir / "raw" / "sra" / job_id
    bronze_dir = output_dir / "bronze" / "sra" / "batches" / f"{query_slug}-{job_id}"
    manifest_path = output_dir / "manifests" / "sra" / f"sra-batch-{query_slug}-{job_id}.jsonl"

    requests_per_second = 10.0 if config.api_key else 3.0
    client = EntrezClient(
        EntrezConfig(
            email=config.email,
            api_key=config.api_key,
            requests_per_second=requests_per_second,
        )
    )

    search_response = client.esearch(db="sra", term=config.query, retmax=0, usehistory=True)
    search_stem = f"esearch-history-{query_slug}-{job_id}"
    write_raw_response(search_response, output_dir=raw_dir, stem=search_stem, extension="json")
    history = parse_esearch_history(search_response)
    if not history.query_key or not history.webenv:
        raise ValueError("ESearch did not return Entrez History handles")

    target_records = history.count
    if config.max_records is not None:
        target_records = min(target_records, config.max_records)

    completed_retstarts = load_completed_retstarts(manifest_path)
    completed_batches = 0
    skipped_batches = 0
    run_rows = 0
    sample_attribute_rows = 0

    for batch_number, (retstart, retmax) in enumerate(
        iter_batch_windows(total_records=target_records, batch_size=config.batch_size),
        start=1,
    ):
        if retstart in completed_retstarts:
            skipped_batches += 1
            continue

        batch_stem = f"{query_slug}-{job_id}-batch-{batch_number:06d}-retstart-{retstart}-retmax-{retmax}"
        try:
            fetch_response = client.efetch_history(
                db="sra",
                query_key=history.query_key,
                webenv=history.webenv,
                retstart=retstart,
                retmax=retmax,
                retmode="xml",
            )
            raw_xml_path = write_raw_response(
                fetch_response,
                output_dir=raw_dir,
                stem=f"efetch-{batch_stem}",
                extension="xml",
            )

            records = parse_sra_efetch_xml(fetch_response.text)
            attributes = parse_sra_sample_attributes(fetch_response.text)
            bronze_path = bronze_dir / f"sra-bronze-batch-{batch_number:06d}.csv"
            attributes_path = bronze_dir / f"sra-sample-attributes-batch-{batch_number:06d}.csv"
            write_bronze_preview(records, bronze_path)
            write_sample_attribute_preview(attributes, attributes_path)

            run_rows += len(records)
            sample_attribute_rows += len(attributes)
            completed_batches += 1
            append_manifest_event(
                manifest_path,
                {
                    "status": "success",
                    "job_id": job_id,
                    "query": config.query,
                    "query_slug": query_slug,
                    "batch_number": batch_number,
                    "retstart": retstart,
                    "retmax": retmax,
                    "raw_xml_path": str(raw_xml_path),
                    "bronze_path": str(bronze_path),
                    "sample_attributes_path": str(attributes_path),
                    "run_rows": len(records),
                    "sample_attribute_rows": len(attributes),
                },
            )
        except Exception as exc:
            append_manifest_event(
                manifest_path,
                {
                    "status": "failure",
                    "job_id": job_id,
                    "query": config.query,
                    "query_slug": query_slug,
                    "batch_number": batch_number,
                    "retstart": retstart,
                    "retmax": retmax,
                    "error": str(exc),
                },
            )
            raise

    return SraBatchSummary(
        job_id=job_id,
        query=config.query,
        query_slug=query_slug,
        total_available=history.count,
        target_records=target_records,
        completed_batches=completed_batches,
        skipped_batches=skipped_batches,
        run_rows=run_rows,
        sample_attribute_rows=sample_attribute_rows,
        manifest_path=manifest_path,
    )


def append_manifest_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"created_at": utc_timestamp(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def load_completed_retstarts(path: Path) -> set[int]:
    if not path.exists():
        return set()

    completed: set[int] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("status") == "success":
                completed.add(int(event["retstart"]))
    return completed
