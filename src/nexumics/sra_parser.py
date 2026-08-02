"""Parse a small bronze preview from SRA EFetch XML."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
from pathlib import Path
import xml.etree.ElementTree as ET

from nexumics.sra_attribute_dictionary import categorize_attribute, normalize_attribute_name


@dataclass(frozen=True)
class SraBronzeRecord:
    experiment_accession: str
    run_accession: str
    study_accession: str
    bioproject_accession: str
    sample_accession: str
    biosample_accession: str
    organism: str
    taxon_id: str
    library_strategy: str
    library_source: str
    library_selection: str
    library_layout: str
    platform: str
    instrument_model: str
    total_spots: str
    total_bases: str


@dataclass(frozen=True)
class SraSampleAttributeRecord:
    sample_accession: str
    biosample_accession: str
    attribute_name: str
    attribute_value: str
    normalized_attribute_name: str
    attribute_category: str


def parse_sra_efetch_xml(xml_text: str) -> list[SraBronzeRecord]:
    root = ET.fromstring(xml_text)
    records: list[SraBronzeRecord] = []

    for package in root.findall("EXPERIMENT_PACKAGE"):
        experiment = package.find("EXPERIMENT")
        study = package.find("STUDY")
        sample = package.find("SAMPLE")
        run_set = package.find("RUN_SET")

        experiment_accession = _attr(experiment, "accession")
        study_accession = _attr(study, "accession") or _attr(experiment.find("STUDY_REF") if experiment is not None else None, "accession")
        bioproject_accession = _external_id(study, "BioProject")
        sample_accession = _attr(sample, "accession")
        biosample_accession = _external_id(sample, "BioSample")
        organism = _text(sample, "SAMPLE_NAME/SCIENTIFIC_NAME")
        taxon_id = _text(sample, "SAMPLE_NAME/TAXON_ID")

        library = experiment.find("DESIGN/LIBRARY_DESCRIPTOR") if experiment is not None else None
        layout = _library_layout(library)
        platform_node = experiment.find("PLATFORM") if experiment is not None else None

        runs = run_set.findall("RUN") if run_set is not None else []
        if not runs:
            records.append(
                _record(
                    experiment_accession=experiment_accession,
                    run_accession="",
                    study_accession=study_accession,
                    bioproject_accession=bioproject_accession,
                    sample_accession=sample_accession,
                    biosample_accession=biosample_accession,
                    organism=organism,
                    taxon_id=taxon_id,
                    library=library,
                    library_layout=layout,
                    platform_node=platform_node,
                    run=None,
                )
            )
            continue

        for run in runs:
            records.append(
                _record(
                    experiment_accession=experiment_accession,
                    run_accession=_attr(run, "accession"),
                    study_accession=study_accession,
                    bioproject_accession=bioproject_accession,
                    sample_accession=sample_accession,
                    biosample_accession=biosample_accession,
                    organism=organism,
                    taxon_id=taxon_id,
                    library=library,
                    library_layout=layout,
                    platform_node=platform_node,
                    run=run,
                )
            )

    return records


def parse_sra_sample_attributes(xml_text: str) -> list[SraSampleAttributeRecord]:
    root = ET.fromstring(xml_text)
    records: list[SraSampleAttributeRecord] = []

    for sample in root.findall("EXPERIMENT_PACKAGE/SAMPLE"):
        sample_accession = _attr(sample, "accession")
        biosample_accession = _external_id(sample, "BioSample")
        for attribute in sample.findall("SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE"):
            name = _text(attribute, "TAG")
            value = _text(attribute, "VALUE")
            normalized_name = normalize_attribute_name(name)
            records.append(
                SraSampleAttributeRecord(
                    sample_accession=sample_accession,
                    biosample_accession=biosample_accession,
                    attribute_name=name,
                    attribute_value=value,
                    normalized_attribute_name=normalized_name,
                    attribute_category=categorize_attribute(normalized_name),
                )
            )

    return records


def write_bronze_preview(records: list[SraBronzeRecord], output_path: Path) -> None:
    _write_records(records, output_path, SraBronzeRecord)


def write_sample_attribute_preview(
    records: list[SraSampleAttributeRecord], output_path: Path
) -> None:
    _write_records(records, output_path, SraSampleAttributeRecord)


def _write_records(records: list, output_path: Path, record_type: type) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(record_type.__dataclass_fields__.keys())
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def _record(
    *,
    experiment_accession: str,
    run_accession: str,
    study_accession: str,
    bioproject_accession: str,
    sample_accession: str,
    biosample_accession: str,
    organism: str,
    taxon_id: str,
    library: ET.Element | None,
    library_layout: str,
    platform_node: ET.Element | None,
    run: ET.Element | None,
) -> SraBronzeRecord:
    return SraBronzeRecord(
        experiment_accession=experiment_accession,
        run_accession=run_accession,
        study_accession=study_accession,
        bioproject_accession=bioproject_accession,
        sample_accession=sample_accession,
        biosample_accession=biosample_accession,
        organism=organism,
        taxon_id=taxon_id,
        library_strategy=_text(library, "LIBRARY_STRATEGY"),
        library_source=_text(library, "LIBRARY_SOURCE"),
        library_selection=_text(library, "LIBRARY_SELECTION"),
        library_layout=library_layout,
        platform=_platform_name(platform_node),
        instrument_model=_instrument_model(platform_node),
        total_spots=_attr(run, "total_spots"),
        total_bases=_attr(run, "total_bases"),
    )


def _attr(node: ET.Element | None, name: str) -> str:
    return "" if node is None else node.attrib.get(name, "")


def _text(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    found = node.find(path)
    return "" if found is None or found.text is None else found.text.strip()


def _external_id(node: ET.Element | None, namespace: str) -> str:
    if node is None:
        return ""
    for external_id in node.findall("IDENTIFIERS/EXTERNAL_ID"):
        if external_id.attrib.get("namespace") == namespace and external_id.text:
            return external_id.text.strip()
    return ""


def _library_layout(library: ET.Element | None) -> str:
    if library is None:
        return ""
    layout = library.find("LIBRARY_LAYOUT")
    if layout is None or len(layout) == 0:
        return ""
    return layout[0].tag


def _platform_name(platform_node: ET.Element | None) -> str:
    if platform_node is None or len(platform_node) == 0:
        return ""
    return platform_node[0].tag


def _instrument_model(platform_node: ET.Element | None) -> str:
    if platform_node is None or len(platform_node) == 0:
        return ""
    instrument = platform_node[0].find("INSTRUMENT_MODEL")
    return "" if instrument is None or instrument.text is None else instrument.text.strip()
