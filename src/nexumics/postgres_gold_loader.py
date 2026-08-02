"""Load SRA Gold Parquet tables into PostgreSQL."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nexumics.sra_gold import SRA_GOLD_TABLES
from nexumics.sra_parquet import load_duckdb


SRA_GOLD_POSTGRES_SCHEMA: dict[str, list[tuple[str, str]]] = {
    "sra_domain_summary": [
        ("sample_domain", "text"),
        ("sample_count", "bigint"),
        ("run_count", "bigint"),
        ("attribute_count", "bigint"),
        ("organism_group_count", "bigint"),
        ("host_present_sample_count", "bigint"),
        ("environment_present_sample_count", "bigint"),
        ("clinical_present_sample_count", "bigint"),
        ("metagenome_present_sample_count", "bigint"),
    ],
    "sra_context_summary": [
        ("sample_context", "text"),
        ("sample_count", "bigint"),
        ("run_count", "bigint"),
        ("attribute_count", "bigint"),
        ("sample_domain_count", "bigint"),
    ],
    "sra_domain_library_strategy_summary": [
        ("sample_domain", "text"),
        ("library_strategy", "text"),
        ("run_count", "bigint"),
        ("sample_count", "bigint"),
        ("experiment_count", "bigint"),
        ("total_spots", "bigint"),
        ("total_bases", "bigint"),
    ],
    "sra_top_organisms_by_domain": [
        ("sample_domain", "text"),
        ("organism_rank", "bigint"),
        ("organism", "text"),
        ("taxon_id", "text"),
        ("sample_count", "bigint"),
    ],
    "sra_attribute_category_by_domain": [
        ("sample_domain", "text"),
        ("attribute_category", "text"),
        ("attribute_count", "bigint"),
        ("sample_count", "bigint"),
    ],
    "sra_quality_summary": [
        ("sample_count", "bigint"),
        ("run_count", "bigint"),
        ("attribute_count", "bigint"),
        ("unknown_sample_count", "bigint"),
        ("unknown_sample_pct", "double precision"),
    ],
}


@dataclass(frozen=True)
class PostgresConnectionConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "nexumics"
    user: str = "nexumics"
    password: str = "nexumics"


@dataclass(frozen=True)
class GoldPostgresLoadResult:
    schema_name: str
    table_counts: dict[str, int]


def load_sra_gold_to_postgres(
    *,
    gold_dir: Path,
    connection_config: PostgresConnectionConfig,
    schema_name: str = "gold_sra",
) -> GoldPostgresLoadResult:
    psycopg = load_psycopg()
    validate_gold_inputs(gold_dir)
    table_rows = read_gold_parquet_rows(gold_dir)

    with psycopg.connect(
        host=connection_config.host,
        port=connection_config.port,
        dbname=connection_config.dbname,
        user=connection_config.user,
        password=connection_config.password,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {quote_identifier(schema_name)}")
            for table_name in SRA_GOLD_TABLES:
                create_table(cursor, schema_name=schema_name, table_name=table_name)
                cursor.execute(
                    f"TRUNCATE TABLE {qualified_table_name(schema_name, table_name)}"
                )
                insert_rows(
                    cursor,
                    schema_name=schema_name,
                    table_name=table_name,
                    rows=table_rows[table_name],
                )
        connection.commit()

    return GoldPostgresLoadResult(
        schema_name=schema_name,
        table_counts={table_name: len(rows) for table_name, rows in table_rows.items()},
    )


def validate_gold_inputs(gold_dir: Path) -> None:
    for table_name in SRA_GOLD_TABLES:
        path = gold_dir / f"{table_name}.parquet"
        if not path.exists():
            raise ValueError(f"Missing required Gold Parquet table: {path}")


def read_gold_parquet_rows(gold_dir: Path) -> dict[str, list[dict[str, object]]]:
    duckdb = load_duckdb()
    rows: dict[str, list[dict[str, object]]] = {}
    with duckdb.connect(":memory:") as connection:
        for table_name in SRA_GOLD_TABLES:
            path = gold_dir / f"{table_name}.parquet"
            columns = [column for column, _postgres_type in SRA_GOLD_POSTGRES_SCHEMA[table_name]]
            select_list = ", ".join(columns)
            result = connection.execute(f"SELECT {select_list} FROM read_parquet(?)", [str(path)])
            rows[table_name] = [
                dict(zip(columns, row, strict=True))
                for row in result.fetchall()
            ]
    return rows


def create_table(cursor: object, *, schema_name: str, table_name: str) -> None:
    columns_sql = ", ".join(
        f"{quote_identifier(column_name)} {postgres_type}"
        for column_name, postgres_type in SRA_GOLD_POSTGRES_SCHEMA[table_name]
    )
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {qualified_table_name(schema_name, table_name)} (
            {columns_sql}
        )
        """
    )


def insert_rows(
    cursor: object,
    *,
    schema_name: str,
    table_name: str,
    rows: list[dict[str, object]],
) -> None:
    if not rows:
        return
    columns = [column for column, _postgres_type in SRA_GOLD_POSTGRES_SCHEMA[table_name]]
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(quote_identifier(column) for column in columns)
    values = [tuple(row.get(column) for column in columns) for row in rows]
    cursor.executemany(
        f"""
        INSERT INTO {qualified_table_name(schema_name, table_name)} ({column_sql})
        VALUES ({placeholders})
        """,
        values,
    )


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def qualified_table_name(schema_name: str, table_name: str) -> str:
    return f"{quote_identifier(schema_name)}.{quote_identifier(table_name)}"


def load_psycopg() -> object:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required to load Gold tables into PostgreSQL. "
            "Install project dependencies with `python -m pip install -e .`."
        ) from exc
    return psycopg
