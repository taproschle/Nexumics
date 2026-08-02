"""Small NCBI Entrez E-utilities client.

The first pipeline milestone intentionally uses the Python standard library.
That keeps the API behavior visible before we add orchestration or storage
frameworks around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from http.client import IncompleteRead
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class EntrezClientError(RuntimeError):
    """Raised when an Entrez request fails after retries."""


@dataclass(frozen=True)
class EntrezConfig:
    """Configuration required for responsible Entrez usage."""

    email: str
    tool: str = "nexumics"
    api_key: str | None = None
    requests_per_second: float = 3.0
    timeout_seconds: float = 30.0
    max_retries: int = 3
    user_agent: str = "nexumics/0.1.0"


@dataclass(frozen=True)
class EntrezResponse:
    """Raw response plus request metadata for the raw layer."""

    utility: str
    url: str
    params: dict[str, Any]
    status_code: int
    content_type: str
    text: str


@dataclass(frozen=True)
class EntrezSearchHistory:
    """Parsed ESearch result with Entrez History metadata."""

    count: int
    query_key: str
    webenv: str
    ids: list[str]


class EntrezClient:
    """Minimal Entrez client with rate limiting, retries, and raw responses."""

    def __init__(self, config: EntrezConfig) -> None:
        if not config.email:
            raise ValueError("EntrezConfig.email is required")
        if config.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if config.max_retries < 1:
            raise ValueError("max_retries must be at least 1")

        self.config = config
        self._last_request_at = 0.0

    def esearch(
        self,
        *,
        db: str,
        term: str,
        retmax: int = 20,
        usehistory: bool = False,
        retmode: str = "json",
    ) -> EntrezResponse:
        params: dict[str, Any] = {
            "db": db,
            "term": term,
            "retmax": retmax,
            "retmode": retmode,
        }
        if usehistory:
            params["usehistory"] = "y"
        return self.request(
            "esearch",
            params,
        )

    def efetch(
        self,
        *,
        db: str,
        ids: list[str],
        retmode: str = "xml",
    ) -> EntrezResponse:
        if not ids:
            raise ValueError("ids must not be empty")
        return self.request(
            "efetch",
            {
                "db": db,
                "id": ",".join(ids),
                "retmode": retmode,
            },
        )

    def efetch_history(
        self,
        *,
        db: str,
        query_key: str,
        webenv: str,
        retstart: int,
        retmax: int,
        retmode: str = "xml",
    ) -> EntrezResponse:
        if retstart < 0:
            raise ValueError("retstart must be non-negative")
        if retmax <= 0:
            raise ValueError("retmax must be positive")
        if not query_key:
            raise ValueError("query_key is required")
        if not webenv:
            raise ValueError("webenv is required")
        return self.request(
            "efetch",
            {
                "db": db,
                "query_key": query_key,
                "WebEnv": webenv,
                "retstart": retstart,
                "retmax": retmax,
                "retmode": retmode,
            },
        )

    def request(self, utility: str, params: dict[str, Any]) -> EntrezResponse:
        endpoint = f"{BASE_URL}/{utility}.fcgi"
        full_params = {
            **params,
            "tool": self.config.tool,
            "email": self.config.email,
        }
        if self.config.api_key:
            full_params["api_key"] = self.config.api_key

        url = f"{endpoint}?{urlencode(full_params)}"
        last_error: Exception | None = None

        for attempt in range(1, self.config.max_retries + 1):
            self._wait_for_rate_limit()
            try:
                request = Request(url, headers={"User-Agent": self.config.user_agent})
                with urlopen(request, timeout=self.config.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                    return EntrezResponse(
                        utility=utility,
                        url=url,
                        params=full_params,
                        status_code=response.status,
                        content_type=response.headers.get("Content-Type", ""),
                        text=body,
                    )
            except (HTTPError, URLError, TimeoutError, IncompleteRead) as exc:
                last_error = exc
                if attempt == self.config.max_retries:
                    break
                time.sleep(min(2**attempt, 30))

        raise EntrezClientError(f"Entrez {utility} request failed: {last_error}") from last_error

    def _wait_for_rate_limit(self) -> None:
        min_interval = 1.0 / self.config.requests_per_second
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_at = time.monotonic()


def parse_esearch_ids(response: EntrezResponse) -> list[str]:
    """Extract Entrez UIDs from an ESearch JSON response."""

    payload = json.loads(response.text)
    idlist = payload.get("esearchresult", {}).get("idlist", [])
    return [str(uid) for uid in idlist]


def parse_esearch_history(response: EntrezResponse) -> EntrezSearchHistory:
    """Extract count and History server handles from an ESearch JSON response."""

    payload = json.loads(response.text)
    result = payload.get("esearchresult", {})
    return EntrezSearchHistory(
        count=int(result.get("count", 0)),
        query_key=str(result.get("querykey", "")),
        webenv=str(result.get("webenv", "")),
        ids=[str(uid) for uid in result.get("idlist", [])],
    )
