import csv
from pathlib import Path
import tempfile
import unittest

from nexumics.taxonomy_reference import (
    parse_taxonomy_xml,
    read_unique_taxon_ids,
    write_taxonomy_reference,
)


class TaxonomyReferenceTests(unittest.TestCase):
    def test_parse_taxonomy_xml_derives_domain_from_lineage(self) -> None:
        rows = parse_taxonomy_xml(
            """<?xml version="1.0" ?>
            <TaxaSet>
              <Taxon>
                <TaxId>5833</TaxId>
                <ScientificName>Plasmodium falciparum</ScientificName>
                <Rank>species</Rank>
                <ParentTaxId>5820</ParentTaxId>
                <Lineage>cellular organisms; Eukaryota; Alveolata; Apicomplexa; Plasmodium</Lineage>
                <LineageEx>
                  <Taxon>
                    <TaxId>2759</TaxId>
                    <ScientificName>Eukaryota</ScientificName>
                    <Rank>superkingdom</Rank>
                  </Taxon>
                  <Taxon>
                    <TaxId>33630</TaxId>
                    <ScientificName>Alveolata</ScientificName>
                    <Rank>clade</Rank>
                  </Taxon>
                  <Taxon>
                    <TaxId>5794</TaxId>
                    <ScientificName>Apicomplexa</ScientificName>
                    <Rank>phylum</Rank>
                  </Taxon>
                  <Taxon>
                    <TaxId>5820</TaxId>
                    <ScientificName>Plasmodium</ScientificName>
                    <Rank>genus</Rank>
                  </Taxon>
                </LineageEx>
              </Taxon>
            </TaxaSet>
            """
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows["5833"]["organism_group"], "Protists")
        self.assertEqual(rows["5833"]["sample_domain"], "protist")
        self.assertEqual(rows["5833"]["phylum"], "Apicomplexa")
        self.assertEqual(rows["5833"]["genus"], "Plasmodium")

    def test_parse_taxonomy_xml_keeps_controls_unknown(self) -> None:
        rows = parse_taxonomy_xml(
            """<?xml version="1.0" ?>
            <TaxaSet>
              <Taxon>
                <TaxId>32644</TaxId>
                <ScientificName>unidentified</ScientificName>
                <Rank>no rank</Rank>
                <ParentTaxId>1</ParentTaxId>
              </Taxon>
            </TaxaSet>
            """
        )

        self.assertEqual(rows["32644"]["organism_group"], "unknown")
        self.assertEqual(rows["32644"]["sample_domain"], "unknown")

    def test_parse_taxonomy_xml_derives_animal_from_metazoa_lineage(self) -> None:
        rows = parse_taxonomy_xml(
            """<?xml version="1.0" ?>
            <TaxaSet>
              <Taxon>
                <TaxId>9913</TaxId>
                <ScientificName>Bos taurus</ScientificName>
                <Rank>species</Rank>
                <ParentTaxId>9903</ParentTaxId>
                <Lineage>cellular organisms; Eukaryota; Metazoa; Chordata; Mammalia; Bos</Lineage>
                <LineageEx>
                  <Taxon>
                    <TaxId>2759</TaxId>
                    <ScientificName>Eukaryota</ScientificName>
                    <Rank>superkingdom</Rank>
                  </Taxon>
                  <Taxon>
                    <TaxId>33208</TaxId>
                    <ScientificName>Metazoa</ScientificName>
                    <Rank>kingdom</Rank>
                  </Taxon>
                  <Taxon>
                    <TaxId>9903</TaxId>
                    <ScientificName>Bos</ScientificName>
                    <Rank>genus</Rank>
                  </Taxon>
                </LineageEx>
              </Taxon>
            </TaxaSet>
            """
        )

        self.assertEqual(rows["9913"]["organism_group"], "Eukaryota")
        self.assertEqual(rows["9913"]["sample_domain"], "animal")

    def test_read_unique_taxon_ids_from_sra_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / "sra_sample.csv"
            with sample_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["sample_accession", "taxon_id"])
                writer.writeheader()
                writer.writerows(
                    [
                        {"sample_accession": "SRS1", "taxon_id": "9606"},
                        {"sample_accession": "SRS2", "taxon_id": "9606"},
                        {"sample_accession": "SRS3", "taxon_id": "5833"},
                        {"sample_accession": "SRS4", "taxon_id": ""},
                    ]
                )

            self.assertEqual(read_unique_taxon_ids(sample_path), {"9606", "5833"})

    def test_write_taxonomy_reference_sorts_by_taxon_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "taxonomy_reference.csv"

            count = write_taxonomy_reference(
                path,
                [
                    {"taxon_id": "9606", "scientific_name": "Homo sapiens"},
                    {"taxon_id": "5833", "scientific_name": "Plasmodium falciparum"},
                ],
            )

            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(count, 2)
            self.assertEqual([row["taxon_id"] for row in rows], ["5833", "9606"])
