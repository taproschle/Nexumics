# SRA Metadata Discovery

This document records the first inspection of SRA metadata through NCBI Entrez E-utilities.

Discovery date: 2026-08-01

## Goal

Understand what SRA metadata is available through Entrez before designing the first ingestion code.

The goal is not to download sequencing files. The initial goal is to inspect metadata shape, identifiers, links, and fields that could become raw, bronze, silver, and gold layer inputs later.

## Official Interfaces Used

Base URL:

```text
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

Utilities inspected:

- `einfo`: inspect SRA searchable fields and links.
- `esearch`: search SRA and retrieve Entrez UIDs.
- `esummary`: retrieve compact summaries for selected UIDs.
- `efetch`: retrieve fuller XML records for selected UIDs.
- `elink`: inspect related records in BioProject, BioSample, GEO DataSets, PubMed, and Taxonomy.

Official references:

- [Entrez Programming Utilities Help](https://www.ncbi.nlm.nih.gov/sites/books/NBK25501/)
- [E-utilities In-Depth](https://www.ncbi.nlm.nih.gov/books/NBK25499/)
- [Search in SRA Entrez](https://www.ncbi.nlm.nih.gov/sra/docs/srasearch/)

## SRA Database Snapshot

The `einfo` response for `db=sra` reported:

| Field | Value |
| --- | --- |
| Database name | `sra` |
| Menu name | `SRA` |
| Description | SRA Database |
| Build observed | `Build260731-2338m.1` |
| Record count observed | `45780842` |
| Last update observed | `2026/08/01 02:08` |

## Useful Search Fields

| Field Code | Full Name | Why It Matters |
| --- | --- | --- |
| `ACCN` | Accession | Search or filter by SRA accessions such as SRX, SRR, SRP, or SRS-linked records. |
| `TITL` | Title | Search experiment titles. |
| `PROP` | Properties | Filter controlled SRA properties such as platform, strategy, layout, and access. |
| `WORD` | Text Word | Broad free-text discovery. |
| `ORGN` | Organism | Filter by organism, for example `Homo sapiens`. |
| `PDAT` | Publication Date | Filter by publication or release date. |
| `MDAT` | Modification Date | Filter by update date. |
| `GPRJ` | BioProject | Search by BioProject association. |
| `BSPL` | BioSample | Search by BioSample association. |
| `PLAT` | Platform | Filter by sequencing platform. |
| `STRA` | Strategy | Filter by library strategy, such as RNA-Seq. |
| `SRC` | Source | Filter by library source. |
| `SEL` | Selection | Filter by library selection. |
| `LAY` | Layout | Filter paired or single layout. |
| `RLEN` | ReadLength | Numeric read length search field. |
| `ACS` | Access | Public or controlled access. |
| `ALN` | Aligned | Numeric aligned-read field. |
| `MBS` | Mbases | Numeric size field in megabases. |

## Available Links From SRA

The `einfo` response reported the following useful SRA outbound links:

| Link Name | Target Database | Why It Matters |
| --- | --- | --- |
| `sra_bioproject` | `bioproject` | Connects experiments/runs to project-level context. |
| `sra_biosample` | `biosample` | Connects sequencing records to sample-level metadata. |
| `sra_gds` | `gds` | Connects SRA records to related GEO DataSets when available. |
| `sra_pubmed` | `pubmed` | Connects records to publications when available. |
| `sra_taxonomy` | `taxonomy` | Connects records to organism/taxonomy metadata. |
| `sra_assembly` | `assembly` | Useful for genome assembly relationships in some contexts. |

## Example Search

Query used:

```text
RNA-Seq[All Fields] AND Homo sapiens[Organism]
```

Endpoint pattern:

```text
esearch.fcgi?db=sra&term=RNA-Seq[All Fields] AND Homo sapiens[Organism]&retmax=3&retmode=json
```

Observed UIDs:

| UID |
| --- |
| `45985764` |
| `45985763` |
| `45985762` |

## Example ESummary Metadata

For UID `45985764`, `esummary` returned top-level JSON fields:

| Field | Observed Value Or Meaning |
| --- | --- |
| `uid` | `45985764` |
| `expxml` | XML string containing experiment, study, organism, sample, library, BioProject, and BioSample summary metadata. |
| `runs` | XML string containing run accession and run-level statistics. |
| `extlinks` | External links when available. Empty in the inspected record. |
| `createdate` | `2026/07/31` |
| `updatedate` | `2026/07/31` |

Important note: `esummary` is JSON, but important SRA details are embedded as XML strings inside `expxml` and `runs`.

## Example EFetch Metadata

For UID `45985764`, `efetch` returned an `EXPERIMENT_PACKAGE_SET`.

The inspected XML included these major sections:

| Section | Example Fields |
| --- | --- |
| `EXPERIMENT` | Experiment accession `SRX34620150`, title, study reference, design, sample descriptor, library descriptor, platform. |
| `SUBMISSION` | Submission accession `SRA2499939`, center name, lab name, submitter ID. |
| `Organization` | Submitter organization and contact details. |
| `STUDY` | Study accession `SRP723296`, external BioProject ID `PRJNA1505714`, study title, study type, abstract. |
| `SAMPLE` | Sample accession `SRS30186470`, external BioSample ID `SAMN62099445`, taxon, scientific name, sample attributes. |
| `SAMPLE_ATTRIBUTES` | Key-value attributes such as age, sex, tissue, collection date, location, and BioSample model. |
| `Pool` | Sample pool member data including spots, bases, tax ID, and organism. |
| `RUN_SET` | Run count, bases, spots, bytes, and run records. |
| `RUN` | Run accession `SRR39952987`, total spots, total bases, size, public status, published timestamp. |

## Example Identifiers

| Entity | Example Identifier |
| --- | --- |
| Entrez SRA UID | `45985764` |
| Experiment | `SRX34620150` |
| Run | `SRR39952987` |
| Study | `SRP723296` |
| Submission | `SRA2499939` |
| BioProject | `PRJNA1505714` |
| BioSample | `SAMN62099445` |
| SRA Sample | `SRS30186470` |
| Taxonomy | `9606` |

## Example Links For UID 45985764

`elink` showed:

| Target Database | Entrez Link Name | Linked ID |
| --- | --- | --- |
| `bioproject` | `sra_bioproject` | `1505714` |
| `biosample` | `sra_biosample` | `62099445` |
| `taxonomy` | `sra_taxonomy` | `9606` |

No `gds` or `pubmed` links were observed for this inspected UID.

## Initial Metadata Model Candidates

The first bronze layer could parse SRA metadata into these candidate tables or records:

| Candidate Record | Purpose |
| --- | --- |
| `sra_experiment` | One record per SRA experiment accession, centered on SRX. |
| `sra_run` | One record per run accession, centered on SRR. |
| `sra_study` | Study-level metadata, centered on SRP and linked BioProject. |
| `sra_sample` | SRA sample and BioSample identifiers, centered on SRS and SAMN. |
| `sra_sample_attribute` | Flexible key-value attributes from `SAMPLE_ATTRIBUTES`. |
| `sra_link` | Cross-database relationships observed through `elink`. |

## Design Implications

- The raw layer should preserve full `einfo`, `esearch`, `esummary`, `efetch`, and `elink` responses.
- `efetch` XML looks like the strongest source for structured SRA metadata.
- `esummary` is useful for quick previews, but it embeds XML strings that still need parsing.
- SRA metadata has both stable structured sections and flexible sample attributes.
- Cross-database linking should be treated as first-class metadata, not an afterthought.
- Sample attributes should probably remain flexible in bronze, then become normalized selectively in silver.

## Open Questions

1. Should the first implementation use `efetch` XML as the main raw source for SRA records?
2. Should `esummary` be used only for lightweight previews and record discovery?
3. Should the first demo query start from SRA directly or from BioProject and then link into SRA?
4. Which sample attributes should be promoted into silver columns first?
5. How much personal/contact submitter metadata should be retained, ignored, or redacted in downstream layers?

## Proposed Next Step

Build a tiny local discovery script that:

1. Calls `esearch` for a limited SRA query.
2. Calls `efetch` for a small number of returned UIDs.
3. Saves the raw XML response under an ignored local data path.
4. Parses a minimal bronze preview with experiment, study, sample, BioProject, BioSample, organism, library, platform, and run fields.
5. Prints or writes a small Markdown/CSV summary for inspection.
