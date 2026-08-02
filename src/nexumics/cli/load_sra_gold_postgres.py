"""Load SRA Gold Parquet tables into PostgreSQL."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from nexumics.postgres_gold_loader import (
    PostgresConnectionConfig,
    load_sra_gold_to_postgres,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load SRA Gold Parquet tables into PostgreSQL.")
    parser.add_argument("--gold-dir", default="data/gold/sra/parquet")
    parser.add_argument("--schema-name", default="gold_sra")
    parser.add_argument("--host", default=os.getenv("POSTGRES_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("POSTGRES_PORT", "5432")))
    parser.add_argument("--dbname", default=os.getenv("POSTGRES_DB", "nexumics"))
    parser.add_argument("--user", default=os.getenv("POSTGRES_USER", "nexumics"))
    parser.add_argument("--password", default=os.getenv("POSTGRES_PASSWORD", "nexumics"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = load_sra_gold_to_postgres(
        gold_dir=Path(args.gold_dir),
        connection_config=PostgresConnectionConfig(
            host=args.host,
            port=args.port,
            dbname=args.dbname,
            user=args.user,
            password=args.password,
        ),
        schema_name=args.schema_name,
    )

    print(f"Schema: {result.schema_name}")
    for table_name, row_count in result.table_counts.items():
        print(f"{table_name}: {row_count}")


if __name__ == "__main__":
    main()
