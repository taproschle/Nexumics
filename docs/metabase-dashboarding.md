# Metabase Dashboarding

This document describes the first local Metabase setup for Nexumics.

## Purpose

Metabase is the first visual exploration layer on top of the PostgreSQL serving database.

The data flow is:

```text
Gold Parquet -> PostgreSQL gold_sra schema -> Metabase dashboards
```

Metabase is not the source of truth. Raw, Bronze, Silver, Gold, and Taxonomy artifacts remain local lake files under `data/`. PostgreSQL serves the curated Gold tables, and Metabase reads from PostgreSQL.

## Start Services

Start PostgreSQL and Metabase:

```powershell
docker compose up -d postgres metabase
```

Metabase will be available at:

```text
http://localhost:3001
```

The first startup can take a few minutes while Docker pulls the image and Metabase initializes.

## Load Data Before Exploring

Build the local lake and load Gold tables into PostgreSQL:

```powershell
python -m nexumics.cli.build_sra_local_lake
python -m nexumics.cli.load_sra_gold_postgres
```

## Connect Metabase To PostgreSQL

During Metabase setup, add a PostgreSQL database with:

| Setting | Value |
| --- | --- |
| Database type | PostgreSQL |
| Display name | `Nexumics Gold` |
| Host | `postgres` |
| Port | `5432` |
| Database name | `nexumics` |
| Username | `nexumics` |
| Password | `nexumics` |
| Schemas | `gold_sra` |
| SSL | Off |

Important: use `postgres` as the host inside Metabase because Metabase and PostgreSQL run in the same Docker Compose network. Use `localhost` only from tools running on the Windows host, such as VS Code or PowerShell.

## Suggested First Questions

Start with:

- Samples by biological domain.
- Runs by biological domain.
- Unknown sample percentage.
- Top organisms by domain.
- Library strategies by domain.
- Attribute categories by domain.

These map directly to the Gold tables:

```text
gold_sra.sra_domain_summary
gold_sra.sra_context_summary
gold_sra.sra_domain_library_strategy_summary
gold_sra.sra_top_organisms_by_domain
gold_sra.sra_attribute_category_by_domain
gold_sra.sra_quality_summary
```

## Create Dashboards Programmatically

Nexumics includes a small Metabase API helper that creates the first dashboard collection from versioned definitions.

Set your Metabase admin credentials in the current PowerShell session:

```powershell
$env:METABASE_EMAIL = "your-metabase-admin-email@example.com"
$env:METABASE_PASSWORD = "your-metabase-password"
```

Then run:

```powershell
nexumics-create-metabase-dashboards
```

If PowerShell does not recognize the command yet, reinstall the editable package with `python -m pip install -e .` or run:

```powershell
python -m nexumics.cli.create_metabase_dashboards
```

By default, the command expects:

| Variable | Default |
| --- | --- |
| `METABASE_URL` | `http://localhost:3001` |
| `METABASE_DATABASE_NAME` | `Nexumics Gold` |
| `METABASE_COLLECTION_NAME` | `Nexumics SRA Gold` |

The command creates:

- `Nexumics Lake Overview`;
- `Biological Diversity Explorer`;
- `Sequencing Strategy & Metadata Quality`.

The dashboard cards use native SQL against the `gold_sra` schema. Re-running the command creates a new dashboard collection, which is useful while the dashboard design is still evolving.

## Local State

Metabase local application state is persisted in the Docker volume:

```text
metabase_data
```

This volume is local runtime state and is not versioned in Git.
