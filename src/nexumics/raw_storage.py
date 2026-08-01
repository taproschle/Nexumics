"""Helpers for writing raw API responses to local disk."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from nexumics.entrez import EntrezResponse


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def slugify(value: str) -> str:
    lowered = value.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-") or "query"


def write_raw_response(
    response: EntrezResponse,
    *,
    output_dir: Path,
    stem: str,
    extension: str,
) -> Path:
    """Write response body and sidecar metadata for reproducible raw storage."""

    output_dir.mkdir(parents=True, exist_ok=True)
    body_path = output_dir / f"{stem}.{extension}"
    metadata_path = output_dir / f"{stem}.metadata.json"

    body_path.write_text(response.text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "utility": response.utility,
                "url": redact_url(response.url),
                "params": redact_params(response.params),
                "status_code": response.status_code,
                "content_type": response.content_type,
                "body_path": str(body_path),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return body_path


def redact_params(params: dict[str, object]) -> dict[str, object]:
    redacted = dict(params)
    if "api_key" in redacted:
        redacted["api_key"] = "[REDACTED]"
    return redacted


def redact_url(url: str) -> str:
    parts = urlsplit(url)
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        query.append((key, "[REDACTED]" if key == "api_key" else value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
