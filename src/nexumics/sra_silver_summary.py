"""Summarize local SRA Silver CSV tables."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from pathlib import Path


SUMMARY_TABLES = {
    "sample_domain_counts.csv": ["sample_domain"],
    "organism_group_counts.csv": ["organism_group"],
    "sample_context_counts.csv": ["sample_context"],
    "sample_domain_context_counts.csv": ["sample_domain", "sample_context"],
    "attribute_category_counts.csv": ["attribute_category"],
    "library_strategy_counts.csv": ["library_strategy"],
}


def summarize_sra_silver(*, input_dir: Path, output_dir: Path) -> dict[str, int]:
    classification_rows = read_csv_rows(input_dir / "sra_sample_classification.csv")
    attribute_rows = read_csv_rows(input_dir / "sra_sample_attribute.csv")
    run_rows = read_csv_rows(input_dir / "sra_run.csv")

    outputs = {
        "sample_domain_counts.csv": count_by_fields(classification_rows, ["sample_domain"]),
        "organism_group_counts.csv": count_by_fields(classification_rows, ["organism_group"]),
        "sample_context_counts.csv": count_by_fields(classification_rows, ["sample_context"]),
        "sample_domain_context_counts.csv": count_by_fields(classification_rows, ["sample_domain", "sample_context"]),
        "attribute_category_counts.csv": count_by_fields(attribute_rows, ["attribute_category"]),
        "library_strategy_counts.csv": count_by_fields(run_rows, ["library_strategy"]),
    }

    output_counts: dict[str, int] = {}
    for filename, rows in outputs.items():
        fieldnames = [*SUMMARY_TABLES[filename], "count"]
        output_counts[filename] = write_csv_rows(output_dir / filename, fieldnames, rows)
    return output_counts


def count_by_fields(rows: Iterable[dict[str, str]], fields: list[str]) -> list[dict[str, str]]:
    counter: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        key = tuple(row.get(field, "") or "missing" for field in fields)
        counter[key] += 1

    summary_rows = [
        {**{field: value for field, value in zip(fields, key)}, "count": str(count)}
        for key, count in counter.items()
    ]
    return sorted(summary_rows, key=lambda row: (-int(row["count"]), tuple(row[field] for field in fields)))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ValueError(f"Missing required Silver table: {path}")
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
