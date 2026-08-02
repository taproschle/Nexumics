import unittest

from nexumics.sra_parser import parse_sra_efetch_xml, parse_sra_sample_attributes


SRA_XML = """<?xml version="1.0" encoding="UTF-8"?>
<EXPERIMENT_PACKAGE_SET>
  <EXPERIMENT_PACKAGE>
    <EXPERIMENT accession="SRX1">
      <TITLE>Example experiment</TITLE>
      <STUDY_REF accession="SRP1" />
      <DESIGN>
        <SAMPLE_DESCRIPTOR accession="SRS1" />
        <LIBRARY_DESCRIPTOR>
          <LIBRARY_STRATEGY>RNA-Seq</LIBRARY_STRATEGY>
          <LIBRARY_SOURCE>TRANSCRIPTOMIC</LIBRARY_SOURCE>
          <LIBRARY_SELECTION>PolyA</LIBRARY_SELECTION>
          <LIBRARY_LAYOUT><PAIRED /></LIBRARY_LAYOUT>
        </LIBRARY_DESCRIPTOR>
      </DESIGN>
      <PLATFORM>
        <ILLUMINA>
          <INSTRUMENT_MODEL>Illumina NovaSeq X Plus</INSTRUMENT_MODEL>
        </ILLUMINA>
      </PLATFORM>
    </EXPERIMENT>
    <STUDY accession="SRP1">
      <IDENTIFIERS>
        <EXTERNAL_ID namespace="BioProject">PRJNA1</EXTERNAL_ID>
      </IDENTIFIERS>
    </STUDY>
    <SAMPLE accession="SRS1">
      <IDENTIFIERS>
        <EXTERNAL_ID namespace="BioSample">SAMN1</EXTERNAL_ID>
      </IDENTIFIERS>
      <SAMPLE_NAME>
        <TAXON_ID>9606</TAXON_ID>
        <SCIENTIFIC_NAME>Homo sapiens</SCIENTIFIC_NAME>
      </SAMPLE_NAME>
      <SAMPLE_ATTRIBUTES>
        <SAMPLE_ATTRIBUTE>
          <TAG>age</TAG>
          <VALUE>22 years</VALUE>
        </SAMPLE_ATTRIBUTE>
        <SAMPLE_ATTRIBUTE>
          <TAG>geo loc name</TAG>
          <VALUE>USA: Manassas, VA</VALUE>
        </SAMPLE_ATTRIBUTE>
        <SAMPLE_ATTRIBUTE>
          <TAG>strain</TAG>
          <VALUE>Example strain</VALUE>
        </SAMPLE_ATTRIBUTE>
      </SAMPLE_ATTRIBUTES>
    </SAMPLE>
    <RUN_SET>
      <RUN accession="SRR1" total_spots="10" total_bases="1500" />
    </RUN_SET>
  </EXPERIMENT_PACKAGE>
</EXPERIMENT_PACKAGE_SET>
"""


class SraParserTests(unittest.TestCase):
    def test_parse_sra_efetch_xml_extracts_bronze_preview_fields(self) -> None:
        records = parse_sra_efetch_xml(SRA_XML)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.experiment_accession, "SRX1")
        self.assertEqual(record.run_accession, "SRR1")
        self.assertEqual(record.study_accession, "SRP1")
        self.assertEqual(record.bioproject_accession, "PRJNA1")
        self.assertEqual(record.sample_accession, "SRS1")
        self.assertEqual(record.biosample_accession, "SAMN1")
        self.assertEqual(record.organism, "Homo sapiens")
        self.assertEqual(record.library_strategy, "RNA-Seq")
        self.assertEqual(record.library_layout, "PAIRED")
        self.assertEqual(record.platform, "ILLUMINA")
        self.assertEqual(record.instrument_model, "Illumina NovaSeq X Plus")
        self.assertEqual(record.total_spots, "10")

    def test_parse_sra_sample_attributes_extracts_flexible_attributes(self) -> None:
        records = parse_sra_sample_attributes(SRA_XML)

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].sample_accession, "SRS1")
        self.assertEqual(records[0].biosample_accession, "SAMN1")
        self.assertEqual(records[0].attribute_name, "age")
        self.assertEqual(records[0].attribute_value, "22 years")
        self.assertEqual(records[0].normalized_attribute_name, "age")
        self.assertEqual(records[0].attribute_category, "clinical")
        self.assertEqual(records[1].normalized_attribute_name, "geo_loc_name")
        self.assertEqual(records[1].attribute_category, "spatiotemporal")
        self.assertEqual(records[2].attribute_category, "organism_identity")
