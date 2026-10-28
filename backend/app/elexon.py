from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE = os.getenv("ELEXON_API_BASE", "https://data.elexon.co.uk/bmrs/api/v1")
TIMEOUT = float(os.getenv("ELEXON_TIMEOUT_SECONDS", "25"))


class ElexonError(RuntimeError):
    pass


def _get(path: str, params: dict[str, str]) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(params)
    url = f"{BASE.rstrip('/')}/{path}?{query}"
    last_error = "unknown error"
    for attempt in range(4):
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "wind-vintage-dashboard/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
            rows = payload.get("data", []) if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise ElexonError(f"Unexpected response shape from {path}")
            return rows
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}"
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                break
            retry = exc.headers.get("Retry-After")
            delay = min(float(retry), 8) if retry and retry.isdigit() else 0.5 * (2 ** attempt)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            if attempt == 3:
                break
            time.sleep(0.5 * (2 ** attempt))
    raise ElexonError(f"Elexon request failed for {path}: {last_error}")


def fetch_january_2026() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Retrieve superseded vintages by publication time and actuals for January."""
    actuals = _get("datasets/FUELHH/stream", {
        "publishDateTimeFrom": "2026-01-01T00:00:00Z",
        "publishDateTimeTo": "2026-02-01T00:00:00Z",
        "fuelType": "WIND",
    })
    forecasts = _get("datasets/WINDFOR/stream", {
        "publishDateTimeFrom": "2025-12-30T00:00:00Z",
        "publishDateTimeTo": "2026-02-01T00:00:00Z",
    })
    return actuals, forecasts

