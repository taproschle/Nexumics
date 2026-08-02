"""Build first-pass Gold SRA analytical tables with DuckDB."""

from __future__ import annotations

from pathlib import Path

from nexumics.sra_parquet import load_duckdb, sql_string_literal


SRA_GOLD_TABLES = (
    "sra_domain_summary",
    "sra_context_summary",
    "sra_domain_library_strategy_summary",
    "sra_top_organisms_by_domain",
    "sra_attribute_category_by_domain",
    "sra_quality_summary",
)


def build_sra_gold_tables(*, input_dir: Path, output_dir: Path) -> dict[str, int]:
    duckdb = load_duckdb()
    validate_silver_parquet_inputs(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    with duckdb.connect(":memory:") as connection:
        create_silver_views(connection, input_dir)
        gold_queries = {
            "sra_domain_summary": domain_summary_query(),
            "sra_context_summary": context_summary_query(),
            "sra_domain_library_strategy_summary": domain_library_strategy_summary_query(),
            "sra_top_organisms_by_domain": top_organisms_by_domain_query(),
            "sra_attribute_category_by_domain": attribute_category_by_domain_query(),
            "sra_quality_summary": quality_summary_query(),
        }
        for table_name, query in gold_queries.items():
            output_path = output_dir / f"{table_name}.parquet"
            connection.execute(
                f"""
                COPY ({query})
                TO {sql_string_literal(output_path)}
                (FORMAT PARQUET)
                """
            )
            counts[table_name] = count_table_rows(connection, output_path)
    return counts


def validate_silver_parquet_inputs(input_dir: Path) -> None:
    required_files = (
        "sra_run.parquet",
        "sra_sample.parquet",
        "sra_sample_attribute.parquet",
        "sra_sample_classification.parquet",
    )
    for filename in required_files:
        path = input_dir / filename
        if not path.exists():
            raise ValueError(f"Missing required Silver Parquet table: {path}")


def create_silver_views(connection: object, input_dir: Path) -> None:
    connection.execute(
        f"""
        CREATE VIEW sra_run AS
        SELECT * FROM read_parquet({sql_string_literal(input_dir / "sra_run.parquet")});

        CREATE VIEW sra_sample AS
        SELECT * FROM read_parquet({sql_string_literal(input_dir / "sra_sample.parquet")});

        CREATE VIEW sra_sample_attribute AS
        SELECT * FROM read_parquet({sql_string_literal(input_dir / "sra_sample_attribute.parquet")});

        CREATE VIEW sra_sample_classification AS
        SELECT * FROM read_parquet({sql_string_literal(input_dir / "sra_sample_classification.parquet")});
        """
    )


def domain_summary_query() -> str:
    return """
        WITH run_counts AS (
            SELECT sample_accession, COUNT(*) AS run_count
            FROM sra_run
            GROUP BY sample_accession
        ),
        attribute_counts AS (
            SELECT sample_accession, COUNT(*) AS attribute_count
            FROM sra_sample_attribute
            GROUP BY sample_accession
        )
        SELECT
            c.sample_domain,
            COUNT(*) AS sample_count,
            CAST(COALESCE(SUM(r.run_count), 0) AS BIGINT) AS run_count,
            CAST(COALESCE(SUM(a.attribute_count), 0) AS BIGINT) AS attribute_count,
            COUNT(DISTINCT c.organism_group) AS organism_group_count,
            CAST(SUM(CASE WHEN c.host_present = 'True' THEN 1 ELSE 0 END) AS BIGINT) AS host_present_sample_count,
            CAST(SUM(CASE WHEN c.environment_present = 'True' THEN 1 ELSE 0 END) AS BIGINT) AS environment_present_sample_count,
            CAST(SUM(CASE WHEN c.clinical_present = 'True' THEN 1 ELSE 0 END) AS BIGINT) AS clinical_present_sample_count,
            CAST(SUM(CASE WHEN c.metagenome_present = 'True' THEN 1 ELSE 0 END) AS BIGINT) AS metagenome_present_sample_count
        FROM sra_sample_classification AS c
        LEFT JOIN run_counts AS r
            ON c.sample_accession = r.sample_accession
        LEFT JOIN attribute_counts AS a
            ON c.sample_accession = a.sample_accession
        GROUP BY c.sample_domain
        ORDER BY sample_count DESC, c.sample_domain
    """


def context_summary_query() -> str:
    return """
        WITH run_counts AS (
            SELECT sample_accession, COUNT(*) AS run_count
            FROM sra_run
            GROUP BY sample_accession
        ),
        attribute_counts AS (
            SELECT sample_accession, COUNT(*) AS attribute_count
            FROM sra_sample_attribute
            GROUP BY sample_accession
        )
        SELECT
            c.sample_context,
            COUNT(*) AS sample_count,
            CAST(COALESCE(SUM(r.run_count), 0) AS BIGINT) AS run_count,
            CAST(COALESCE(SUM(a.attribute_count), 0) AS BIGINT) AS attribute_count,
            COUNT(DISTINCT c.sample_domain) AS sample_domain_count
        FROM sra_sample_classification AS c
        LEFT JOIN run_counts AS r
            ON c.sample_accession = r.sample_accession
        LEFT JOIN attribute_counts AS a
            ON c.sample_accession = a.sample_accession
        GROUP BY c.sample_context
        ORDER BY sample_count DESC, c.sample_context
    """


def domain_library_strategy_summary_query() -> str:
    return """
        SELECT
            c.sample_domain,
            r.library_strategy,
            COUNT(*) AS run_count,
            COUNT(DISTINCT r.sample_accession) AS sample_count,
            COUNT(DISTINCT r.experiment_accession) AS experiment_count,
            CAST(SUM(CAST(NULLIF(r.total_spots, '') AS BIGINT)) AS BIGINT) AS total_spots,
            CAST(SUM(CAST(NULLIF(r.total_bases, '') AS BIGINT)) AS BIGINT) AS total_bases
        FROM sra_run AS r
        JOIN sra_sample_classification AS c
            ON r.sample_accession = c.sample_accession
        GROUP BY c.sample_domain, r.library_strategy
        ORDER BY run_count DESC, c.sample_domain, r.library_strategy
    """


def top_organisms_by_domain_query() -> str:
    return """
        WITH organism_counts AS (
            SELECT
                c.sample_domain,
                COALESCE(NULLIF(s.organism, ''), 'missing') AS organism,
                COALESCE(NULLIF(s.taxon_id, ''), 'missing') AS taxon_id,
                COUNT(*) AS sample_count,
                ROW_NUMBER() OVER (
                    PARTITION BY c.sample_domain
                    ORDER BY COUNT(*) DESC, COALESCE(NULLIF(s.organism, ''), 'missing')
                ) AS organism_rank
            FROM sra_sample AS s
            JOIN sra_sample_classification AS c
                ON s.sample_accession = c.sample_accession
            GROUP BY c.sample_domain, organism, taxon_id
        )
        SELECT
            sample_domain,
            organism_rank,
            organism,
            taxon_id,
            sample_count
        FROM organism_counts
        WHERE organism_rank <= 10
        ORDER BY sample_domain, organism_rank
    """


def attribute_category_by_domain_query() -> str:
    return """
        SELECT
            c.sample_domain,
            a.attribute_category,
            COUNT(*) AS attribute_count,
            COUNT(DISTINCT a.sample_accession) AS sample_count
        FROM sra_sample_attribute AS a
        JOIN sra_sample_classification AS c
            ON a.sample_accession = c.sample_accession
        GROUP BY c.sample_domain, a.attribute_category
        ORDER BY c.sample_domain, attribute_count DESC, a.attribute_category
    """


def quality_summary_query() -> str:
    return """
        WITH domain_counts AS (
            SELECT
                COUNT(*) AS sample_count,
                SUM(CASE WHEN sample_domain = 'unknown' THEN 1 ELSE 0 END) AS unknown_sample_count
            FROM sra_sample_classification
        ),
        run_counts AS (
            SELECT COUNT(*) AS run_count
            FROM sra_run
        ),
        attribute_counts AS (
            SELECT COUNT(*) AS attribute_count
            FROM sra_sample_attribute
        )
        SELECT
            CAST(domain_counts.sample_count AS BIGINT) AS sample_count,
            CAST(run_counts.run_count AS BIGINT) AS run_count,
            CAST(attribute_counts.attribute_count AS BIGINT) AS attribute_count,
            CAST(domain_counts.unknown_sample_count AS BIGINT) AS unknown_sample_count,
            CAST(ROUND((domain_counts.unknown_sample_count::DOUBLE / domain_counts.sample_count::DOUBLE) * 100, 4) AS DOUBLE) AS unknown_sample_pct
        FROM domain_counts, run_counts, attribute_counts
    """


def count_table_rows(connection: object, parquet_path: Path) -> int:
    result = connection.execute("SELECT COUNT(*) FROM read_parquet(?)", [str(parquet_path)]).fetchone()
    return int(result[0])
