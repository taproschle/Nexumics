"""Quality checks for local SRA lake outputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ALLOWED_SAMPLE_DOMAINS = {
    "animal",
    "fungi",
    "human",
    "metagenome",
    "microorganism",
    "plant",
    "unknown",
    "virus",
}


@dataclass(frozen=True)
class QualityCheck:
    name: str
    status: str
    observed: str
    expected: str
    message: str


def validate_sra_lake(
    *,
    silver_dir: Path,
    gold_dir: Path | None = None,
    max_unknown_samples: int = 10,
) -> list[QualityCheck]:
    checks: list[QualityCheck] = []
    required_silver_files = {
        "sra_run": silver_dir / "sra_run.csv",
        "sra_sample": silver_dir / "sra_sample.csv",
        "sra_sample_attribute": silver_dir / "sra_sample_attribute.csv",
        "sra_sample_classification": silver_dir / "sra_sample_classification.csv",
    }

    for table_name, path in required_silver_files.items():
        checks.append(file_exists_check(f"silver_{table_name}_exists", path))

    if any(check.status == "fail" for check in checks):
        return checks

    run_rows = read_csv_rows(required_silver_files["sra_run"])
    sample_rows = read_csv_rows(required_silver_files["sra_sample"])
    attribute_rows = read_csv_rows(required_silver_files["sra_sample_attribute"])
    classification_rows = read_csv_rows(required_silver_files["sra_sample_classification"])

    checks.extend(
        [
            non_empty_unique_check("sra_run_run_accession_unique", run_rows, "run_accession"),
            non_empty_unique_check("sra_sample_sample_accession_unique", sample_rows, "sample_accession"),
            non_empty_unique_check(
                "sra_classification_sample_accession_unique",
                classification_rows,
                "sample_accession",
            ),
            row_count_match_check(
                "sra_sample_classification_matches_samples",
                len(classification_rows),
                len(sample_rows),
            ),
            required_field_present_check(
                "sra_sample_attribute_required_fields_present",
                attribute_rows,
                ["sample_accession", "normalized_attribute_name", "attribute_category"],
            ),
            allowed_values_check(
                "sra_sample_domain_allowed_values",
                classification_rows,
                "sample_domain",
                ALLOWED_SAMPLE_DOMAINS,
            ),
            max_value_check(
                "sra_unknown_sample_count_below_threshold",
                count_matching(classification_rows, "sample_domain", "unknown"),
                max_unknown_samples,
            ),
        ]
    )

    if gold_dir is not None:
        for table_name in (
            "sra_domain_summary",
            "sra_context_summary",
            "sra_domain_library_strategy_summary",
        ):
            checks.append(file_exists_check(f"gold_{table_name}_exists", gold_dir / f"{table_name}.parquet"))

    return checks


def file_exists_check(name: str, path: Path) -> QualityCheck:
    return QualityCheck(
        name=name,
        status="pass" if path.exists() else "fail",
        observed=str(path),
        expected="file exists",
        message="Found required file." if path.exists() else "Required file is missing.",
    )


def non_empty_unique_check(name: str, rows: list[dict[str, str]], field: str) -> QualityCheck:
    values = [row.get(field, "") for row in rows]
    non_empty_values = [value for value in values if value]
    duplicate_count = len(non_empty_values) - len(set(non_empty_values))
    missing_count = len(values) - len(non_empty_values)
    passed = duplicate_count == 0 and missing_count == 0
    return QualityCheck(
        name=name,
        status="pass" if passed else "fail",
        observed=f"rows={len(rows)}; missing={missing_count}; duplicates={duplicate_count}",
        expected=f"{field} is non-empty and unique",
        message="Primary key candidate is valid." if passed else "Primary key candidate has missing or duplicate values.",
    )


def row_count_match_check(name: str, observed_count: int, expected_count: int) -> QualityCheck:
    return QualityCheck(
        name=name,
        status="pass" if observed_count == expected_count else "fail",
        observed=str(observed_count),
        expected=str(expected_count),
        message="Row counts match." if observed_count == expected_count else "Row counts do not match.",
    )


def required_field_present_check(name: str, rows: list[dict[str, str]], fields: list[str]) -> QualityCheck:
    missing_count = sum(1 for row in rows for field in fields if not row.get(field, ""))
    return QualityCheck(
        name=name,
        status="pass" if missing_count == 0 else "fail",
        observed=str(missing_count),
        expected="0 missing required values",
        message="Required fields are present." if missing_count == 0 else "Required fields contain missing values.",
    )


def allowed_values_check(
    name: str,
    rows: list[dict[str, str]],
    field: str,
    allowed_values: set[str],
) -> QualityCheck:
    invalid_values = sorted({row.get(field, "") for row in rows if row.get(field, "") not in allowed_values})
    return QualityCheck(
        name=name,
        status="pass" if not invalid_values else "fail",
        observed=" | ".join(invalid_values) if invalid_values else "none",
        expected=" | ".join(sorted(allowed_values)),
        message="All values are allowed." if not invalid_values else "Unexpected values were found.",
    )


def max_value_check(name: str, observed_value: int, max_value: int) -> QualityCheck:
    return QualityCheck(
        name=name,
        status="pass" if observed_value <= max_value else "fail",
        observed=str(observed_value),
        expected=f"<= {max_value}",
        message="Value is within threshold." if observed_value <= max_value else "Value exceeds threshold.",
    )


def count_matching(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(1 for row in rows if row.get(field, "") == value)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_quality_report(path: Path, checks: list[QualityCheck]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "status", "observed", "expected", "message"])
        writer.writeheader()
        for check in checks:
            writer.writerow(
                {
                    "name": check.name,
                    "status": check.status,
                    "observed": check.observed,
                    "expected": check.expected,
                    "message": check.message,
                }
            )
    return len(checks)
