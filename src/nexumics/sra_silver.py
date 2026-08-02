"""Build first-pass Silver SRA tables from consolidated Bronze CSV files."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path


SRA_RUN_FIELDS = [
    "run_accession",
    "experiment_accession",
    "study_accession",
    "sample_accession",
    "biosample_accession",
    "library_strategy",
    "library_source",
    "library_selection",
    "library_layout",
    "platform",
    "instrument_model",
    "total_spots",
    "total_bases",
    "source_dataset",
    "source_file",
]

SRA_SAMPLE_FIELDS = [
    "sample_accession",
    "biosample_accession",
    "organism",
    "taxon_id",
    "source_dataset",
    "source_file",
]

SRA_SAMPLE_ATTRIBUTE_FIELDS = [
    "sample_accession",
    "biosample_accession",
    "attribute_name",
    "attribute_value",
    "normalized_attribute_name",
    "attribute_category",
    "source_dataset",
    "source_file",
]


def latest_matching_file(directory: Path, pattern: str) -> Path:
    files = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not files:
        raise ValueError(f"No files matched {pattern} in {directory}")
    return files[0]


def build_sra_run_rows(bronze_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in bronze_rows:
        run_accession = row.get("run_accession", "")
        if not run_accession or run_accession in seen:
            continue
        seen.add(run_accession)
        rows.append(project_fields(row, SRA_RUN_FIELDS))
    return rows


def build_sra_sample_rows(bronze_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in bronze_rows:
        sample_key = row.get("sample_accession") or row.get("biosample_accession", "")
        if not sample_key or sample_key in seen:
            continue
        seen.add(sample_key)
        rows.append(project_fields(row, SRA_SAMPLE_FIELDS))
    return rows


def build_sra_sample_attribute_rows(attribute_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in attribute_rows:
        key = (
            row.get("sample_accession", ""),
            row.get("biosample_accession", ""),
            row.get("normalized_attribute_name", ""),
            row.get("attribute_value", ""),
        )
        if not any(key) or key in seen:
            continue
        seen.add(key)
        rows.append(project_fields(row, SRA_SAMPLE_ATTRIBUTE_FIELDS))
    return rows


def project_fields(row: dict[str, str], fields: list[str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in fields}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            row_count += 1
    return row_count


def build_silver_tables(
    *,
    bronze_run_path: Path,
    bronze_attribute_path: Path,
    output_dir: Path,
) -> dict[str, int]:
    bronze_run_rows = read_csv_rows(bronze_run_path)
    bronze_attribute_rows = read_csv_rows(bronze_attribute_path)

    run_count = write_csv_rows(
        output_dir / "sra_run.csv",
        SRA_RUN_FIELDS,
        build_sra_run_rows(bronze_run_rows),
    )
    sample_count = write_csv_rows(
        output_dir / "sra_sample.csv",
        SRA_SAMPLE_FIELDS,
        build_sra_sample_rows(bronze_run_rows),
    )
    attribute_count = write_csv_rows(
        output_dir / "sra_sample_attribute.csv",
        SRA_SAMPLE_ATTRIBUTE_FIELDS,
        build_sra_sample_attribute_rows(bronze_attribute_rows),
    )

    return {
        "sra_run": run_count,
        "sra_sample": sample_count,
        "sra_sample_attribute": attribute_count,
    }
