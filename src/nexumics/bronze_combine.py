"""Combine local bronze preview CSV files."""

from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path

from nexumics.sra_attribute_dictionary import categorize_attribute, normalize_attribute_name


RUN_KEY = ("experiment_accession", "run_accession")
ATTRIBUTE_KEY = (
    "sample_accession",
    "biosample_accession",
    "normalized_attribute_name",
    "attribute_value",
)


def combine_csv_files(
    *,
    input_dir: Path,
    pattern: str,
    output_path: Path,
    dedupe_key: tuple[str, ...],
    row_transform: Callable[[dict[str, str]], dict[str, str]] | None = None,
    recursive: bool = False,
    source_dataset_root: Path | None = None,
) -> int:
    files = sorted(input_dir.rglob(pattern) if recursive else input_dir.glob(pattern))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    seen: dict[tuple[str, ...], int] = {}
    fieldnames: list[str] | None = None

    for path in files:
        if output_path.resolve() == path.resolve():
            continue
        source_dataset = source_dataset_name(path, source_dataset_root or input_dir)
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                continue
            if fieldnames is None:
                fieldnames = ["source_dataset", "source_file", *reader.fieldnames]
            for row in reader:
                if row_transform is not None:
                    row = row_transform(row)
                key = tuple(row.get(field, "") for field in dedupe_key)
                if key in seen:
                    existing = rows[seen[key]]
                    existing["source_dataset"] = merge_source_value(existing["source_dataset"], source_dataset)
                    existing["source_file"] = merge_source_value(existing["source_file"], path.name)
                    continue
                seen[key] = len(rows)
                rows.append({"source_dataset": source_dataset, "source_file": path.name, **row})

    if fieldnames is None:
        raise ValueError(f"No CSV files matched {pattern} in {input_dir}")

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def merge_source_value(existing_value: str, new_value: str) -> str:
    values = [value for value in existing_value.split(" | ") if value]
    if new_value not in values:
        values.append(new_value)
    return " | ".join(values)


def source_dataset_name(path: Path, root: Path) -> str:
    try:
        relative_parent = path.parent.relative_to(root)
    except ValueError:
        return path.parent.name

    if str(relative_parent) == ".":
        return "root"
    return relative_parent.parts[0]


def normalize_sample_attribute_row(row: dict[str, str]) -> dict[str, str]:
    normalized_name = normalize_attribute_name(row.get("attribute_name", ""))
    return {
        **row,
        "normalized_attribute_name": normalized_name,
        "attribute_category": categorize_attribute(normalized_name),
    }
