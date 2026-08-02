"""Profile observed SRA sample attributes from bronze CSV files."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from pathlib import Path

from nexumics.sra_attribute_dictionary import categorize_attribute, normalize_attribute_name


PROFILE_FIELDNAMES = [
    "normalized_attribute_name",
    "attribute_category",
    "count",
    "distinct_value_count",
    "original_attribute_names",
    "example_values",
]


@dataclass(frozen=True)
class AttributeProfileRow:
    normalized_attribute_name: str
    attribute_category: str
    count: int
    distinct_value_count: int
    original_attribute_names: str
    example_values: str


def profile_sra_attributes(
    *,
    input_dir: Path,
    pattern: str = "sra-sample-attributes*.csv",
    max_examples: int = 5,
) -> list[AttributeProfileRow]:
    if max_examples <= 0:
        raise ValueError("max_examples must be positive")

    files = sorted(input_dir.rglob(pattern))
    if not files:
        raise ValueError(f"No CSV files matched {pattern} under {input_dir}")

    counts: Counter[str] = Counter()
    values: dict[str, set[str]] = defaultdict(set)
    original_names: dict[str, set[str]] = defaultdict(set)

    for path in files:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                continue
            for row in reader:
                original_name = row.get("attribute_name", "")
                normalized_name = normalize_attribute_name(original_name)
                value = row.get("attribute_value", "")
                if not normalized_name:
                    continue
                counts[normalized_name] += 1
                original_names[normalized_name].add(original_name)
                if value:
                    values[normalized_name].add(value)

    return [
        AttributeProfileRow(
            normalized_attribute_name=normalized_name,
            attribute_category=categorize_attribute(normalized_name),
            count=count,
            distinct_value_count=len(values[normalized_name]),
            original_attribute_names=" | ".join(sorted(original_names[normalized_name])),
            example_values=" | ".join(sorted(values[normalized_name])[:max_examples]),
        )
        for normalized_name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def write_attribute_profile(rows: list[AttributeProfileRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROFILE_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "normalized_attribute_name": row.normalized_attribute_name,
                    "attribute_category": row.attribute_category,
                    "count": row.count,
                    "distinct_value_count": row.distinct_value_count,
                    "original_attribute_names": row.original_attribute_names,
                    "example_values": row.example_values,
                }
            )
