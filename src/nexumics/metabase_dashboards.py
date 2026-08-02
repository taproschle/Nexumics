"""Metabase dashboard definitions and API helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


DEFAULT_METABASE_URL = "http://localhost:3001"
DEFAULT_DATABASE_NAME = "Nexumics Gold"
DEFAULT_COLLECTION_NAME = "Nexumics SRA Gold"


@dataclass(frozen=True)
class CardDefinition:
    name: str
    description: str
    query: str
    display: str
    visualization_settings: dict[str, Any]
    col: int
    row: int
    size_x: int
    size_y: int


@dataclass(frozen=True)
class DashboardDefinition:
    name: str
    description: str
    cards: tuple[CardDefinition, ...]


def scalar_card(name: str, description: str, query: str, col: int, row: int) -> CardDefinition:
    return CardDefinition(
        name=name,
        description=description,
        query=query,
        display="scalar",
        visualization_settings={},
        col=col,
        row=row,
        size_x=6,
        size_y=4,
    )


def bar_card(
    name: str,
    description: str,
    query: str,
    dimension: str,
    metric: str,
    col: int,
    row: int,
    size_x: int = 12,
    size_y: int = 8,
) -> CardDefinition:
    return CardDefinition(
        name=name,
        description=description,
        query=query,
        display="bar",
        visualization_settings={
            "graph.dimensions": [dimension],
            "graph.metrics": [metric],
        },
        col=col,
        row=row,
        size_x=size_x,
        size_y=size_y,
    )


def table_card(
    name: str,
    description: str,
    query: str,
    col: int,
    row: int,
    size_x: int = 24,
    size_y: int = 10,
) -> CardDefinition:
    return CardDefinition(
        name=name,
        description=description,
        query=query,
        display="table",
        visualization_settings={},
        col=col,
        row=row,
        size_x=size_x,
        size_y=size_y,
    )


DASHBOARDS: tuple[DashboardDefinition, ...] = (
    DashboardDefinition(
        name="Nexumics Lake Overview",
        description="Portfolio-level overview of SRA Gold coverage, scale, and quality.",
        cards=(
            scalar_card(
                "Total Samples",
                "Total classified SRA samples in the local Gold layer.",
                "SELECT sample_count FROM gold_sra.sra_quality_summary;",
                0,
                0,
            ),
            scalar_card(
                "Total Runs",
                "Total SRA runs in the local Gold layer.",
                "SELECT run_count FROM gold_sra.sra_quality_summary;",
                6,
                0,
            ),
            scalar_card(
                "Unknown Sample Percentage",
                "Percentage of samples still classified as unknown.",
                "SELECT unknown_sample_pct FROM gold_sra.sra_quality_summary;",
                12,
                0,
            ),
            scalar_card(
                "Total Sample Attributes",
                "Total flexible sample attribute records retained in the lake.",
                "SELECT attribute_count FROM gold_sra.sra_quality_summary;",
                18,
                0,
            ),
            bar_card(
                "Samples By Biological Domain",
                "Sample coverage by conservative biological domain classification.",
                """
                SELECT sample_domain, sample_count
                FROM gold_sra.sra_domain_summary
                ORDER BY sample_count DESC, sample_domain;
                """,
                "sample_domain",
                "sample_count",
                0,
                4,
            ),
            bar_card(
                "Runs By Biological Domain",
                "Run coverage by conservative biological domain classification.",
                """
                SELECT sample_domain, run_count
                FROM gold_sra.sra_domain_summary
                ORDER BY run_count DESC, sample_domain;
                """,
                "sample_domain",
                "run_count",
                12,
                4,
            ),
            table_card(
                "Domain Summary Table",
                "Full SRA Gold domain summary.",
                """
                SELECT
                    sample_domain,
                    sample_count,
                    run_count,
                    attribute_count,
                    host_present_sample_count,
                    environment_present_sample_count,
                    clinical_present_sample_count,
                    metagenome_present_sample_count
                FROM gold_sra.sra_domain_summary
                ORDER BY sample_count DESC, sample_domain;
                """,
                0,
                12,
            ),
        ),
    ),
    DashboardDefinition(
        name="Biological Diversity Explorer",
        description="Top organisms and biological diversity signals across SRA Gold domains.",
        cards=(
            table_card(
                "Top Organisms By Domain",
                "Top ranked organisms per biological domain.",
                """
                SELECT
                    sample_domain,
                    organism_rank,
                    organism,
                    taxon_id,
                    sample_count
                FROM gold_sra.sra_top_organisms_by_domain
                ORDER BY sample_domain, organism_rank;
                """,
                0,
                0,
                24,
                10,
            ),
            bar_card(
                "Top Organisms Overall",
                "Most frequent organisms in the local SRA Gold layer.",
                """
                SELECT
                    organism,
                    SUM(sample_count) AS sample_count
                FROM gold_sra.sra_top_organisms_by_domain
                GROUP BY organism
                ORDER BY sample_count DESC, organism
                LIMIT 20;
                """,
                "organism",
                "sample_count",
                0,
                10,
                24,
                10,
            ),
            bar_card(
                "Domains By Sample Count",
                "Domain balance across the current lake.",
                """
                SELECT sample_domain, sample_count
                FROM gold_sra.sra_domain_summary
                ORDER BY sample_count DESC, sample_domain;
                """,
                "sample_domain",
                "sample_count",
                0,
                20,
                12,
                8,
            ),
            bar_card(
                "Domains By Attribute Count",
                "Metadata richness by biological domain.",
                """
                SELECT sample_domain, attribute_count
                FROM gold_sra.sra_domain_summary
                ORDER BY attribute_count DESC, sample_domain;
                """,
                "sample_domain",
                "attribute_count",
                12,
                20,
                12,
                8,
            ),
        ),
    ),
    DashboardDefinition(
        name="Sequencing Strategy & Metadata Quality",
        description="Library strategy coverage and metadata category richness across SRA Gold.",
        cards=(
            table_card(
                "Domain And Library Strategy Summary",
                "Run, sample, experiment, spot, and base counts by domain and library strategy.",
                """
                SELECT
                    sample_domain,
                    library_strategy,
                    run_count,
                    sample_count,
                    experiment_count,
                    total_spots,
                    total_bases
                FROM gold_sra.sra_domain_library_strategy_summary
                ORDER BY run_count DESC, sample_domain, library_strategy;
                """,
                0,
                0,
                24,
                10,
            ),
            bar_card(
                "Top Library Strategies",
                "Most represented sequencing library strategies.",
                """
                SELECT
                    library_strategy,
                    SUM(run_count) AS run_count
                FROM gold_sra.sra_domain_library_strategy_summary
                GROUP BY library_strategy
                ORDER BY run_count DESC, library_strategy
                LIMIT 15;
                """,
                "library_strategy",
                "run_count",
                0,
                10,
                12,
                8,
            ),
            bar_card(
                "Attribute Categories Overall",
                "Most frequent normalized sample attribute categories.",
                """
                SELECT
                    attribute_category,
                    SUM(attribute_count) AS attribute_count
                FROM gold_sra.sra_attribute_category_by_domain
                GROUP BY attribute_category
                ORDER BY attribute_count DESC, attribute_category
                LIMIT 20;
                """,
                "attribute_category",
                "attribute_count",
                12,
                10,
                12,
                8,
            ),
            table_card(
                "Attribute Categories By Domain",
                "Attribute category coverage by biological domain.",
                """
                SELECT
                    sample_domain,
                    attribute_category,
                    attribute_count,
                    sample_count
                FROM gold_sra.sra_attribute_category_by_domain
                ORDER BY sample_domain, attribute_count DESC, attribute_category;
                """,
                0,
                18,
                24,
                10,
            ),
        ),
    ),
)


class MetabaseApiError(RuntimeError):
    """Raised when Metabase returns an unsuccessful API response."""


class MetabaseClient:
    def __init__(self, base_url: str, email: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.session_id: str | None = None

    def login(self) -> None:
        response = self._request(
            "POST",
            "/api/session",
            {"username": self.email, "password": self.password},
            authenticated=False,
        )
        self.session_id = response["id"]

    def get_databases(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/database")
        return response.get("data", [])

    def find_database_id(self, database_name: str) -> int:
        for database in self.get_databases():
            if database.get("name") == database_name:
                return int(database["id"])
        available = ", ".join(sorted(str(db.get("name")) for db in self.get_databases()))
        raise MetabaseApiError(
            f"Metabase database '{database_name}' was not found. Available databases: {available}"
        )

    def create_collection(self, name: str, description: str) -> int:
        response = self._request(
            "POST",
            "/api/collection",
            {
                "name": name,
                "description": description,
                "color": "#2D6CDF",
            },
        )
        return int(response["id"])

    def create_card(self, collection_id: int, database_id: int, card: CardDefinition) -> int:
        response = self._request(
            "POST",
            "/api/card",
            {
                "name": card.name,
                "description": card.description,
                "collection_id": collection_id,
                "dataset_query": {
                    "database": database_id,
                    "type": "native",
                    "native": {
                        "query": normalize_sql(card.query),
                        "template-tags": {},
                    },
                },
                "display": card.display,
                "visualization_settings": card.visualization_settings,
            },
        )
        return int(response["id"])

    def create_dashboard(self, collection_id: int, dashboard: DashboardDefinition) -> int:
        response = self._request(
            "POST",
            "/api/dashboard",
            {
                "name": dashboard.name,
                "description": dashboard.description,
                "collection_id": collection_id,
            },
        )
        return int(response["id"])

    def add_card_to_dashboard(self, dashboard_id: int, card_id: int, card: CardDefinition) -> None:
        payload = {
            "cardId": card_id,
            "row": card.row,
            "col": card.col,
            "size_x": card.size_x,
            "size_y": card.size_y,
            "parameter_mappings": [],
            "visualization_settings": card.visualization_settings,
        }
        self._request("POST", f"/api/dashboard/{dashboard_id}/cards", payload)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if authenticated:
            if not self.session_id:
                raise MetabaseApiError("Metabase session is not initialized.")
            headers["X-Metabase-Session"] = self.session_id

        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise MetabaseApiError(f"{method} {path} failed with HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise MetabaseApiError(f"{method} {path} failed: {exc}") from exc


def normalize_sql(query: str) -> str:
    return "\n".join(line.strip() for line in query.strip().splitlines())


def create_dashboards(
    base_url: str,
    email: str,
    password: str,
    database_name: str = DEFAULT_DATABASE_NAME,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> list[tuple[str, int]]:
    client = MetabaseClient(base_url, email, password)
    client.login()
    database_id = client.find_database_id(database_name)
    collection_id = client.create_collection(
        collection_name,
        "Generated Nexumics dashboards for the SRA Gold serving layer.",
    )

    created: list[tuple[str, int]] = []
    for dashboard in DASHBOARDS:
        dashboard_id = client.create_dashboard(collection_id, dashboard)
        for card in dashboard.cards:
            card_id = client.create_card(collection_id, database_id, card)
            client.add_card_to_dashboard(dashboard_id, card_id, card)
        created.append((dashboard.name, dashboard_id))

    return created


def load_metabase_config_from_env() -> dict[str, str]:
    email = os.getenv("METABASE_EMAIL")
    password = os.getenv("METABASE_PASSWORD")
    if not email or not password:
        raise MetabaseApiError(
            "Set METABASE_EMAIL and METABASE_PASSWORD with your Metabase admin credentials."
        )

    return {
        "base_url": os.getenv("METABASE_URL", DEFAULT_METABASE_URL),
        "email": email,
        "password": password,
        "database_name": os.getenv("METABASE_DATABASE_NAME", DEFAULT_DATABASE_NAME),
        "collection_name": os.getenv("METABASE_COLLECTION_NAME", DEFAULT_COLLECTION_NAME),
    }


def dashboard_url(base_url: str, dashboard_id: int, dashboard_name: str) -> str:
    slug = parse.quote(dashboard_name.lower().replace(" ", "-").replace("&", "and"))
    return f"{base_url.rstrip('/')}/dashboard/{dashboard_id}-{slug}"
