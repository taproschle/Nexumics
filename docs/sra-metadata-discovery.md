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

The first implementation now includes a tiny local discovery script that:

1. Calls `esearch` for a limited SRA query.
2. Calls `efetch` for a small number of returned UIDs.
3. Saves the raw XML response under an ignored local data path.
4. Parses a minimal bronze preview with experiment, study, sample, BioProject, BioSample, organism, library, platform, and run fields.
5. Parses a sample-attribute bronze preview from `SAMPLE_ATTRIBUTES`.
6. Prints or writes small CSV summaries for inspection.

Raw response sidecar metadata redacts `api_key` if it is provided.

Run it locally with:

```powershell
$env:NCBI_EMAIL = "your-email@example.com"
nexumics-sra-discovery --retmax 3
```

Implementation entry point:

```text
src/nexumics/cli/sra_discovery.py
```

Raw responses and bronze previews are written under `data/`, which is intentionally ignored by Git.

Current bronze outputs:

```text
data/bronze/sra/sra-bronze-preview-<query>-<timestamp>.csv
data/bronze/sra/sra-sample-attributes-preview-<query>-<timestamp>.csv
```

Local bronze previews can be combined with:

```powershell
nexumics-combine-sra-bronze
```

The combined files include `source_file` for traceability and deduplicate rows using natural preview keys. For sample attributes, the combine command recalculates normalized attribute names and categories with the current parser logic so older local previews can benefit from improved classification rules.

## Resumable Batch Ingestion

For moderate or large metadata pulls, Nexumics now includes a batch-oriented SRA ingestion command:

```powershell
$env:NCBI_EMAIL = "your-email@example.com"
nexumics-sra-batch-ingest --query "WGS[All Fields] AND bacteria[Organism]" --max-records 1000 --batch-size 200
```

This command uses Entrez History instead of passing long UID lists directly to `efetch`.

The batch flow is:

1. Call `esearch` with `usehistory=y` and `retmax=0`.
2. Parse `count`, `query_key`, and `WebEnv` from the search response.
3. Fetch records in `retstart` and `retmax` windows.
4. Save one raw XML file per batch.
5. Parse one run-level bronze CSV and one sample-attribute bronze CSV per batch.
6. Append a JSONL manifest event for each successful or failed batch.

Batch outputs are local-only and intentionally ignored by Git:

```text
data/raw/sra/<job-id>/
data/bronze/sra/batches/<query>-<job-id>/
data/manifests/sra/sra-batch-<query>-<job-id>.jsonl
```

Use `--job-id` to make a run resumable:

```powershell
nexumics-sra-batch-ingest --query "WGS[All Fields] AND bacteria[Organism]" --max-records 1000 --batch-size 200 --job-id bacteria-wgs-test
```

If the manifest already contains successful events for some `retstart` windows, rerunning with the same `--job-id` skips those completed batches.

Recommended first scale-up settings:

| Setting | Suggested Value | Reason |
| --- | --- | --- |
| `--max-records` | `1000` | Large enough to expose heterogeneity without making debugging painful. |
| `--batch-size` | `100` to `200` | Keeps raw XML files reviewable and failures cheap to retry. |
| `NCBI_API_KEY` | Optional but recommended | Allows a higher official request rate. |

The current implementation still targets metadata, not sequencing reads.

## Multi-Query Discovery Notes

Small local runs have been executed for human RNA-Seq, bacterial WGS, viral WGS, metagenomic, environmental, and host-associated microbiome examples.

The observed run-level metadata confirms that the current universal fields work across several domains:

| Example Area | Observed Organisms | Observed Library Sources |
| --- | --- | --- |
| Human RNA-Seq | `Homo sapiens` | `TRANSCRIPTOMIC` |
| Bacterial WGS | `Salmonella enterica`, `Listeria monocytogenes`, `Shigella sonnei` | `GENOMIC` |
| Viral WGS | `Measles morbillivirus`, `Hepatitis C virus subtype 4a` | `GENOMIC`, `VIRAL RNA` |
| Metagenomic | `fish metagenome`, `human gut metagenome`, `soil metagenome` | `METAGENOMIC` |
| Environmental | `wastewater metagenome` | `METAGENOMIC` |

The observed sample attributes confirm that the key-value model is needed. Common or useful attributes include:

- `collection_date`
- `geo_loc_name`
- `BioSampleModel`
- `isolation_source`
- `lat_lon`
- `env_broad_scale`
- `env_local_scale`
- `env_medium`
- `isolate`
- `strain`
- `host_age`
- `serovar`

Many host-associated microbiome attributes currently fall into `other`, especially diet, lifestyle, health survey, and microbiome-project-specific fields. This is acceptable for bronze. The next modeling step should decide whether to add broader categories such as `host_lifestyle`, `host_health`, `diet`, or `survey_metadata`.
