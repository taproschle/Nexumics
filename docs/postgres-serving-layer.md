# PostgreSQL Serving Layer

This document describes the first PostgreSQL serving layer for Nexumics.

## Purpose

The local file lake remains the source of truth for raw, Bronze, Silver, and Gold artifacts. PostgreSQL is introduced as a serving layer for downstream tools such as Metabase, dashboards, and lightweight applications.

The first PostgreSQL scope is intentionally narrow: publish only SRA Gold tables.

## Local Database

Start PostgreSQL with Docker Compose:

```powershell
docker compose up -d postgres
```

Default local connection settings are:

| Setting | Value |
| --- | --- |
| Host | `localhost` |
| Port | `5432` |
| Database | `nexumics` |
| User | `nexumics` |
| Password | `nexumics` |

For local overrides, create a `.env` file from `.env.example`. Do not commit `.env`.

## Load Command

After building the local Gold layer:

```powershell
nexumics-build-sra-local-lake
```

Load Gold tables into PostgreSQL:

```powershell
nexumics-load-sra-gold-postgres
```

The command reads:

```text
data/gold/sra/parquet/
```

And writes to:

```text
gold_sra
```

The load is idempotent at table level: tables are created if needed, truncated, and reloaded from the current Gold Parquet files.

## Published Tables

| PostgreSQL table | Source Parquet |
| --- | --- |
| `gold_sra.sra_domain_summary` | `sra_domain_summary.parquet` |
| `gold_sra.sra_context_summary` | `sra_context_summary.parquet` |
| `gold_sra.sra_domain_library_strategy_summary` | `sra_domain_library_strategy_summary.parquet` |
| `gold_sra.sra_top_organisms_by_domain` | `sra_top_organisms_by_domain.parquet` |
| `gold_sra.sra_attribute_category_by_domain` | `sra_attribute_category_by_domain.parquet` |
| `gold_sra.sra_quality_summary` | `sra_quality_summary.parquet` |

## Verification

Connect with `psql`, a database client, or Metabase and run:

```sql
SELECT *
FROM gold_sra.sra_domain_summary
ORDER BY sample_count DESC;
```

Or verify row counts:

```sql
SELECT 'sra_domain_summary' AS table_name, COUNT(*) FROM gold_sra.sra_domain_summary
UNION ALL
SELECT 'sra_context_summary', COUNT(*) FROM gold_sra.sra_context_summary
UNION ALL
SELECT 'sra_domain_library_strategy_summary', COUNT(*) FROM gold_sra.sra_domain_library_strategy_summary
UNION ALL
SELECT 'sra_top_organisms_by_domain', COUNT(*) FROM gold_sra.sra_top_organisms_by_domain
UNION ALL
SELECT 'sra_attribute_category_by_domain', COUNT(*) FROM gold_sra.sra_attribute_category_by_domain
UNION ALL
SELECT 'sra_quality_summary', COUNT(*) FROM gold_sra.sra_quality_summary;
```

Current expected row counts are documented in `docs/local-sra-pipeline.md`.

## Versioned PostgreSQL Queries

PostgreSQL-ready SQL files live under:

```text
sql/postgres/gold_sra/
```

These queries read directly from PostgreSQL tables such as `gold_sra.sra_domain_summary`.

This is separate from:

```text
sql/gold/sra/
```

Those DuckDB-oriented queries read local Parquet files directly.
