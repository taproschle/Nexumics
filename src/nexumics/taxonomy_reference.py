"""Build and use a local NCBI Taxonomy reference table."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from nexumics.entrez import EntrezClient, EntrezConfig
from nexumics.raw_storage import utc_timestamp, write_raw_response


TAXONOMY_REFERENCE_FIELDS = [
    "taxon_id",
    "scientific_name",
    "rank",
    "parent_taxon_id",
    "lineage",
    "lineage_taxon_ids",
    "superkingdom",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species",
    "organism_group",
    "sample_domain",
]


@dataclass(frozen=True)
class TaxonomyUpdateSummary:
    input_taxon_ids: int
    existing_taxon_ids: int
    fetched_taxon_ids: int
    output_taxon_ids: int
    output_path: Path
    raw_batch_count: int
    manifest_path: Path


def update_taxonomy_reference(
    *,
    sample_path: Path,
    output_path: Path,
    email: str,
    api_key: str | None = None,
    batch_size: int = 200,
    rebuild: bool = False,
    raw_dir: Path = Path("data/raw/ncbi_taxonomy"),
    manifest_path: Path = Path("data/manifests/ncbi_taxonomy/taxonomy-reference-updates.jsonl"),
) -> TaxonomyUpdateSummary:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    sample_taxon_ids = read_unique_taxon_ids(sample_path)
    existing_rows = read_taxonomy_reference(output_path) if output_path.exists() and not rebuild else {}
    missing_taxon_ids = sorted(sample_taxon_ids - set(existing_rows), key=taxon_sort_key)

    fetched_rows: dict[str, dict[str, str]] = {}
    raw_batch_count = 0
    if missing_taxon_ids:
        client = EntrezClient(EntrezConfig(email=email, api_key=api_key))
        for batch_number, batch in enumerate(batched(missing_taxon_ids, batch_size), start=1):
            response = client.efetch(db="taxonomy", ids=batch, retmode="xml")
            raw_xml_path = write_raw_response(
                response,
                output_dir=raw_dir,
                stem=f"efetch-taxonomy-batch-{batch_number:06d}-{utc_timestamp()}",
                extension="xml",
            )
            batch_rows = parse_taxonomy_xml(response.text)
            fetched_rows.update(batch_rows)
            raw_batch_count += 1
            append_taxonomy_manifest_event(
                manifest_path,
                {
                    "status": "success",
                    "batch_number": batch_number,
                    "requested_taxon_ids": len(batch),
                    "fetched_taxon_ids": len(batch_rows),
                    "raw_xml_path": str(raw_xml_path),
                    "output_path": str(output_path),
                    "rebuild": rebuild,
                },
            )
    else:
        append_taxonomy_manifest_event(
            manifest_path,
            {
                "status": "noop",
                "requested_taxon_ids": 0,
                "fetched_taxon_ids": 0,
                "output_path": str(output_path),
                "rebuild": rebuild,
            },
        )

    all_rows = {**existing_rows, **fetched_rows}
    write_taxonomy_reference(output_path, all_rows.values())

    return TaxonomyUpdateSummary(
        input_taxon_ids=len(sample_taxon_ids),
        existing_taxon_ids=len(existing_rows),
        fetched_taxon_ids=len(fetched_rows),
        output_taxon_ids=len(all_rows),
        output_path=output_path,
        raw_batch_count=raw_batch_count,
        manifest_path=manifest_path,
    )


def parse_taxonomy_xml(xml_text: str) -> dict[str, dict[str, str]]:
    root = ET.fromstring(xml_text)
    rows: dict[str, dict[str, str]] = {}
    for taxon in root.findall("./Taxon"):
        taxon_id = text_or_empty(taxon, "TaxId")
        if not taxon_id:
            continue

        lineage_entries = parse_lineage_entries(taxon)
        lineage_names = [entry["scientific_name"] for entry in lineage_entries]
        lineage_taxon_ids = [entry["taxon_id"] for entry in lineage_entries]
        scientific_name = text_or_empty(taxon, "ScientificName")
        rank_by_name = {entry["rank"]: entry["scientific_name"] for entry in lineage_entries}

        organism_group = classify_organism_group_from_lineage(
            taxon_id=taxon_id,
            scientific_name=scientific_name,
            lineage_names=lineage_names,
        )
        sample_domain = classify_sample_domain_from_organism_group(
            taxon_id=taxon_id,
            scientific_name=scientific_name,
            organism_group=organism_group,
        )

        rows[taxon_id] = {
            "taxon_id": taxon_id,
            "scientific_name": scientific_name,
            "rank": text_or_empty(taxon, "Rank"),
            "parent_taxon_id": text_or_empty(taxon, "ParentTaxId"),
            "lineage": text_or_empty(taxon, "Lineage"),
            "lineage_taxon_ids": " | ".join(lineage_taxon_ids),
            "superkingdom": rank_by_name.get("superkingdom", ""),
            "kingdom": rank_by_name.get("kingdom", ""),
            "phylum": rank_by_name.get("phylum", ""),
            "class": rank_by_name.get("class", ""),
            "order": rank_by_name.get("order", ""),
            "family": rank_by_name.get("family", ""),
            "genus": rank_by_name.get("genus", ""),
            "species": scientific_name if text_or_empty(taxon, "Rank") == "species" else rank_by_name.get("species", ""),
            "organism_group": organism_group,
            "sample_domain": sample_domain,
        }
    return rows


def parse_lineage_entries(taxon: ET.Element) -> list[dict[str, str]]:
    entries = []
    for lineage_taxon in taxon.findall("./LineageEx/Taxon"):
        entries.append(
            {
                "taxon_id": text_or_empty(lineage_taxon, "TaxId"),
                "scientific_name": text_or_empty(lineage_taxon, "ScientificName"),
                "rank": text_or_empty(lineage_taxon, "Rank"),
            }
        )
    return entries


def classify_organism_group_from_lineage(
    *,
    taxon_id: str,
    scientific_name: str,
    lineage_names: list[str],
) -> str:
    name_lower = scientific_name.lower()
    lineage = {name.lower() for name in lineage_names}

    if taxon_id == "9606" or name_lower == "homo sapiens":
        return "Eukaryota"
    if any(term in name_lower for term in ("blank sample", "synthetic construct", "unidentified")):
        return "unknown"
    if "metagenomes" in lineage or "metagenome" in name_lower:
        return "Metagenome"
    if "viruses" in lineage:
        return "Viruses"
    if "bacteria" in lineage:
        return "Bacteria"
    if "archaea" in lineage:
        return "Archaea"
    if "viridiplantae" in lineage:
        return "Viridiplantae"
    if "fungi" in lineage:
        return "Fungi"
    if any(term in lineage for term in ("apicomplexa", "alveolata", "stramenopiles", "discoba")):
        return "Protists"
    if "metazoa" in lineage:
        return "Eukaryota"
    if "eukaryota" in lineage:
        return "Protists"
    return "unknown"


def classify_sample_domain_from_organism_group(
    *,
    taxon_id: str,
    scientific_name: str,
    organism_group: str,
) -> str:
    if taxon_id == "9606" or scientific_name.lower() == "homo sapiens":
        return "human"
    if organism_group == "Viridiplantae":
        return "plant"
    if organism_group == "Fungi":
        return "fungi"
    if organism_group == "Protists":
        return "protist"
    if organism_group in {"Bacteria", "Archaea"}:
        return "microorganism"
    if organism_group == "Viruses":
        return "virus"
    if organism_group == "Metagenome":
        return "metagenome"
    if organism_group == "Eukaryota":
        return "animal"
    return "unknown"


def read_unique_taxon_ids(sample_path: Path) -> set[str]:
    with sample_path.open(encoding="utf-8", newline="") as handle:
        return {
            row.get("taxon_id", "").strip()
            for row in csv.DictReader(handle)
            if row.get("taxon_id", "").strip()
        }


def read_taxonomy_reference(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            row["taxon_id"]: {field: row.get(field, "") for field in TAXONOMY_REFERENCE_FIELDS}
            for row in csv.DictReader(handle)
            if row.get("taxon_id")
        }


def write_taxonomy_reference(path: Path, rows: Iterable[dict[str, str]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_rows = sorted(rows, key=lambda row: taxon_sort_key(row.get("taxon_id", "")))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TAXONOMY_REFERENCE_FIELDS)
        writer.writeheader()
        for row in sorted_rows:
            writer.writerow({field: row.get(field, "") for field in TAXONOMY_REFERENCE_FIELDS})
    return len(sorted_rows)


def append_taxonomy_manifest_event(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"created_at": utc_timestamp(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def batched(values: list[str], batch_size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), batch_size):
        yield values[start : start + batch_size]


def text_or_empty(element: ET.Element, child_name: str) -> str:
    child = element.find(child_name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def taxon_sort_key(taxon_id: str) -> tuple[int, str]:
    return (int(taxon_id), taxon_id) if taxon_id.isdigit() else (10**12, taxon_id)
