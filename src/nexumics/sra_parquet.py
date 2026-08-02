"""Export local SRA Silver CSV tables to Parquet with DuckDB."""

from __future__ import annotations

from pathlib import Path


SRA_SILVER_TABLES = (
    "sra_run",
    "sra_sample",
    "sra_sample_attribute",
    "sra_sample_classification",
)


def export_sra_silver_parquet(*, input_dir: Path, output_dir: Path) -> dict[str, int]:
    duckdb = load_duckdb()
    output_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    with duckdb.connect(":memory:") as connection:
        for table_name in SRA_SILVER_TABLES:
            csv_path = input_dir / f"{table_name}.csv"
            parquet_path = output_dir / f"{table_name}.parquet"
            if not csv_path.exists():
                raise ValueError(f"Missing required Silver CSV table: {csv_path}")

            connection.execute(
                f"""
                COPY (
                    SELECT *
                    FROM read_csv_auto(
                        {sql_string_literal(csv_path)},
                        header = true,
                        all_varchar = true,
                        delim = ',',
                        quote = '"',
                        escape = '"'
                    )
                )
                TO {sql_string_literal(parquet_path)}
                (FORMAT PARQUET)
                """
            )
            counts[table_name] = count_parquet_rows(connection, parquet_path)
    return counts


def count_parquet_rows(connection: object, parquet_path: Path) -> int:
    result = connection.execute("SELECT COUNT(*) FROM read_parquet(?)", [str(parquet_path)]).fetchone()
    return int(result[0])


def sql_string_literal(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def load_duckdb() -> object:
    try:
        import duckdb
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "DuckDB is required to export SRA Silver tables to Parquet. "
            "Install project dependencies with `python -m pip install -e .`."
        ) from exc
    return duckdb
