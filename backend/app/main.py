from __future__ import annotations

import os
import time
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analytics import build_analysis
from .elexon import ElexonError, fetch_january_2026

app = FastAPI(title="Wind Vintage", version="1.0.0", description="Elexon wind forecast vintages and accuracy for January 2026")
_source_cache: dict[str, Any] = {"at": 0.0, "actuals": None, "forecasts": None}
_analysis_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_lock = Lock()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "wind-vintage-api"}


@app.get("/api/analysis")
def analysis(cutoff: str = Query("12:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")):
    hour, minute = map(int, cutoff.split(":"))
    with _lock:
        cached = _analysis_cache.get(cutoff)
        if cached is not None and time.time() - cached[0] < 900:
            return cached[1]
        if _source_cache["actuals"] is None or time.time() - _source_cache["at"] >= 900:
            try:
                actuals, forecasts = fetch_january_2026()
            except ElexonError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            _source_cache.update({"at": time.time(), "actuals": actuals, "forecasts": forecasts})
        actuals, forecasts = _source_cache["actuals"], _source_cache["forecasts"]
        result = build_analysis(actuals, forecasts, hour, minute)
        _analysis_cache[cutoff] = (time.time(), result)
        return result


static_dir = Path(os.getenv("STATIC_DIR", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
if static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        requested = static_dir / path
        if path and requested.is_file() and static_dir in requested.resolve().parents:
            return FileResponse(requested)
        index = static_dir / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend build is unavailable")

