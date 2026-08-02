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

SRA_SAMPLE_CLASSIFICATION_FIELDS = [
    "sample_accession",
    "biosample_accession",
    "sample_domain",
    "organism_group",
    "sample_context",
    "host_present",
    "environment_present",
    "clinical_present",
    "metagenome_present",
    "attribute_category_summary",
    "classification_basis",
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


def build_sra_sample_classification_rows(
    sample_rows: Iterable[dict[str, str]],
    attribute_rows: Iterable[dict[str, str]],
) -> list[dict[str, str]]:
    signals = collect_attribute_signals(attribute_rows)
    rows: list[dict[str, str]] = []
    for sample in sample_rows:
        sample_accession = sample.get("sample_accession", "")
        signal = signals.get(sample_accession, empty_attribute_signal())
        organism = sample.get("organism", "")
        source_dataset = sample.get("source_dataset", "")
        organism_group = classify_organism_group(
            organism=organism,
            taxon_id=sample.get("taxon_id", ""),
            source_dataset=source_dataset,
        )
        sample_domain = classify_sample_domain(
            organism=organism,
            taxon_id=sample.get("taxon_id", ""),
            source_dataset=source_dataset,
            organism_group=organism_group,
            signal=signal,
        )
        sample_context = classify_sample_context(
            organism=organism,
            source_dataset=source_dataset,
            sample_domain=sample_domain,
            signal=signal,
        )
        rows.append(
            {
                "sample_accession": sample_accession,
                "biosample_accession": sample.get("biosample_accession", ""),
                "sample_domain": sample_domain,
                "organism_group": organism_group,
                "sample_context": sample_context,
                "host_present": str(signal["host_present"]),
                "environment_present": str(signal["environment_present"]),
                "clinical_present": str(signal["clinical_present"]),
                "metagenome_present": str(signal["metagenome_present"]),
                "attribute_category_summary": summarize_categories(signal["categories"]),
                "classification_basis": classification_basis(
                    organism=organism,
                    taxon_id=sample.get("taxon_id", ""),
                    source_dataset=source_dataset,
                    organism_group=organism_group,
                    sample_domain=sample_domain,
                    sample_context=sample_context,
                    signal=signal,
                ),
                "source_dataset": source_dataset,
                "source_file": sample.get("source_file", ""),
            }
        )
    return rows


def collect_attribute_signals(attribute_rows: Iterable[dict[str, str]]) -> dict[str, dict[str, object]]:
    signals: dict[str, dict[str, object]] = {}
    for row in attribute_rows:
        sample_accession = row.get("sample_accession", "")
        if not sample_accession:
            continue
        signal = signals.setdefault(sample_accession, empty_attribute_signal())
        category = row.get("attribute_category", "")
        categories = signal["categories"]
        assert isinstance(categories, dict)
        categories[category] = categories.get(category, 0) + 1
        if category == "host":
            signal["host_present"] = True
        elif category == "environment":
            signal["environment_present"] = True
        elif category == "clinical":
            signal["clinical_present"] = True
        elif category == "metagenome_assembly":
            signal["metagenome_present"] = True
    return signals


def empty_attribute_signal() -> dict[str, object]:
    return {
        "categories": {},
        "host_present": False,
        "environment_present": False,
        "clinical_present": False,
        "metagenome_present": False,
    }


def classify_organism_group(*, organism: str, taxon_id: str, source_dataset: str) -> str:
    organism_lower = organism.lower()
    dataset_lower = source_dataset.lower()
    animal_taxon_ids = {
        "7955",  # Danio rerio
        "8319",  # Pleurodeles waltl
        "9031",  # Gallus gallus
        "9544",  # Macaca mulatta
        "9597",  # Pan paniscus
        "9598",  # Pan troglodytes
        "9796",  # Equus caballus
        "9823",  # Sus scrofa
        "9913",  # Bos taurus
        "9940",  # Ovis aries
        "10092",  # Mus musculus domesticus
        "10116",  # Rattus norvegicus
        "494514",  # Vulpes lagopus
        "7782",  # Leucoraja erinaceus
        "8296",  # Ambystoma mexicanum
        "29159",  # Magallana gigas
        "30301",  # Botryllus schlosseri
        "34765",  # Oikopleura dioica
        "37000",  # Pyrrhocoris apterus
        "159736",  # Macrobrachium nipponense
        "1962980",  # Aurelia coerulea
    }
    plant_taxon_ids = {
        "4097",  # Nicotiana tabacum
        "3403",  # Magnolia liliiflora
        "4577",  # Zea mays
        "188998",  # Sinningia aggregata
        "374723",  # Phtheirospermum japonicum
    }
    insect_taxon_ids = {
        "7070",  # Tribolium castaneum
        "7091",  # Bombyx mori
        "108931",  # Nilaparvata lugens
    }
    fungal_taxon_ids = {
        "27291",  # Saccharomyces paradoxus
        "4932",  # Saccharomyces cerevisiae
    }
    algae_taxon_ids = {
        "44745",  # Haematococcus lacustris
    }
    protist_taxon_ids = {
        "5801",  # Eimeria acervulina
        "5802",  # Eimeria tenella
        "5804",  # Eimeria maxima
        "5806",  # Cryptosporidium
        "5807",  # Cryptosporidium parvum
        "5810",  # Toxoplasma
        "5811",  # Toxoplasma gondii
        "5821",  # Plasmodium berghei
        "5823",  # Plasmodium berghei ANKA
        "5825",  # Plasmodium chabaudi
        "5833",  # Plasmodium falciparum
        "5843",  # Plasmodium falciparum NF54
        "5850",  # Plasmodium knowlesi
        "5855",  # Plasmodium vivax
        "5861",  # Plasmodium yoelii
        "5866",  # Babesia bigemina
        "5874",  # Theileria annulata
        "5875",  # Theileria parva
        "5693",  # Trypanosoma cruzi
        "29176",  # Neospora caninum
        "35133",  # Labyrinthula
        "36329",  # Plasmodium falciparum 3D7
        "383379",  # Toxoplasma gondii RH
        "42890",  # Sarcocystis neurona
        "471275",  # Eimeria stiedae
        "483139",  # Cystoisospora suis
        "508771",  # Toxoplasma gondii ME49
        "1344799",  # Sarcocystis calchasi
        "2041159",  # Apicomplexa sp.
        "2605654",  # Selenidium validusae
        "3135041",  # Devanium robustum
        "3135043",  # Lunidium laculatum
        "3135044",  # Lunidium melongena
        "1973199",  # Plasmodium homocircumflexum
        "3391652",  # Apicomplexa sp. corallicolid ex Madracis mirabilis
    }
    if taxon_id == "9606" or organism_lower == "homo sapiens":
        return "Eukaryota"
    if taxon_id == "10090" or taxon_id in animal_taxon_ids or organism_lower == "mus musculus":
        return "Eukaryota"
    if taxon_id in insect_taxon_ids or "drosophila" in organism_lower:
        return "Eukaryota"
    if taxon_id in plant_taxon_ids or "viridiplantae" in dataset_lower or "plant-wgs" in dataset_lower:
        return "Viridiplantae"
    if (
        taxon_id in fungal_taxon_ids
        or "fungi" in dataset_lower
        or "candidozyma" in organism_lower
        or "candida " in organism_lower
        or "fungus" in organism_lower
    ):
        return "Fungi"
    if taxon_id in algae_taxon_ids:
        return "Viridiplantae"
    if taxon_id in protist_taxon_ids or any(
        term in organism_lower
        for term in (
            "babesia",
            "cryptosporidium",
            "eimeria",
            "apicomplexa",
            "amplectina",
            "anthozoaphila",
            "labyrinthula",
            "belladina",
            "cephaloidophora",
            "difficilina",
            "ganymedes",
            "kinetosphaera",
            "klossia",
            "lankesteria",
            "lecudina",
            "legerella",
            "lentusidium",
            "loxomoprha",
            "lunidium",
            "metzidium",
            "neospora",
            "paralecudina",
            "plasmodium",
            "polyrhabdina",
            "sarcocystis",
            "selenidium",
            "siedleckia",
            "theileria",
            "thiriotia",
            "toxoplasma",
            "trypanosoma",
            "trollidium",
            "urospora",
        )
    ):
        return "Protists"
    if "archaea" in dataset_lower or any(term in organism_lower for term in ("methano", "archae")):
        return "Archaea"
    if "virus" in organism_lower or "viruses-organism" in dataset_lower:
        return "Viruses"
    if "bacteria" in dataset_lower or any(
        term in organism_lower
        for term in (
            "escherichia",
            "jejuibacter",
            "acinetobacter",
            "bacillus",
            "burkholderia",
            "campylobacter",
            "citrobacter",
            "enterococcus",
            "enterobacter",
            "elizabethkingia",
            "faecalibacterium",
            "klebsiella",
            "legionella",
            "listeria",
            "mycobacterium",
            "proteus",
            "raoultella",
            "salmonella",
            "pseudomonas",
            "rickettsia",
            "streptococcus",
            "staphylococcus",
            "vibrio",
        )
    ):
        return "Bacteria"
    if "metagenome" in organism_lower or "metagenomic" in dataset_lower:
        return "Metagenome"
    if (
        "long-read" in dataset_lower
        and organism_lower
        and organism_lower not in {"blank sample", "synthetic construct", "unidentified"}
    ):
        return "Eukaryota"
    return "unknown"


def classify_sample_domain(
    *,
    organism: str,
    taxon_id: str,
    source_dataset: str,
    organism_group: str,
    signal: dict[str, object],
) -> str:
    organism_lower = organism.lower()
    dataset_lower = source_dataset.lower()
    if taxon_id == "9606" or organism_lower == "homo sapiens":
        return "human"
    if "viridiplantae" in dataset_lower or organism_group == "Viridiplantae":
        return "plant"
    if organism_group == "Fungi":
        return "fungi"
    if organism_group == "Viruses":
        return "virus"
    if organism_group in {"Bacteria", "Archaea"}:
        return "microorganism"
    if organism_group == "Protists":
        return "protist"
    if "metagenome" in organism_lower or "metagenomic" in dataset_lower or signal["metagenome_present"]:
        return "metagenome"
    if organism_group == "Eukaryota":
        return "animal"
    return "unknown"


def classify_sample_context(
    *,
    organism: str,
    source_dataset: str,
    sample_domain: str,
    signal: dict[str, object],
) -> str:
    organism_lower = organism.lower()
    dataset_lower = source_dataset.lower()
    if sample_domain == "human" and signal["clinical_present"]:
        return "clinical"
    if signal["host_present"]:
        return "host-associated"
    if signal["environment_present"] or "wastewater" in organism_lower or "soil" in organism_lower:
        return "environmental"
    if sample_domain == "metagenome":
        return "metagenomic"
    categories = signal["categories"]
    assert isinstance(categories, dict)
    if "host_material" in categories:
        return "tissue"
    if "experimental_design" in categories or "single-cell" in dataset_lower:
        return "experimental"
    return "unknown"


def summarize_categories(categories: object) -> str:
    if not isinstance(categories, dict):
        return ""
    category_counts = sorted(categories.items(), key=lambda item: (-item[1], item[0]))
    return " | ".join(f"{category}:{count}" for category, count in category_counts)


def classification_basis(
    *,
    organism: str,
    taxon_id: str,
    source_dataset: str,
    organism_group: str,
    sample_domain: str,
    sample_context: str,
    signal: dict[str, object],
) -> str:
    basis = [
        f"organism={organism or 'missing'}",
        f"taxon_id={taxon_id or 'missing'}",
        f"source_dataset={source_dataset or 'missing'}",
        f"organism_group={organism_group}",
        f"sample_domain={sample_domain}",
        f"sample_context={sample_context}",
    ]
    if signal["host_present"]:
        basis.append("host_attribute_present")
    if signal["environment_present"]:
        basis.append("environment_attribute_present")
    if signal["clinical_present"]:
        basis.append("clinical_attribute_present")
    if signal["metagenome_present"]:
        basis.append("metagenome_assembly_attribute_present")
    return "; ".join(basis)


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
    classification_count = write_csv_rows(
        output_dir / "sra_sample_classification.csv",
        SRA_SAMPLE_CLASSIFICATION_FIELDS,
        build_sra_sample_classification_rows(
            build_sra_sample_rows(bronze_run_rows),
            build_sra_sample_attribute_rows(bronze_attribute_rows),
        ),
    )

    return {
        "sra_run": run_count,
        "sra_sample": sample_count,
        "sra_sample_attribute": attribute_count,
        "sra_sample_classification": classification_count,
    }
