from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc


def as_utc(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (TypeError, ValueError):
        return None


def finite_generation(value: Any) -> float | None:
    try:
        result = float(value)
        return result if result >= 0 and result < float("inf") else None
    except (TypeError, ValueError):
        return None


def normalize_actuals(records: list[dict[str, Any]]) -> dict[datetime, dict[str, Any]]:
    """Keep one deterministic, latest-published actual per delivery start."""
    result: dict[datetime, dict[str, Any]] = {}
    for row in records:
        if str(row.get("fuelType", "")).upper() != "WIND":
            continue
        delivery, published = as_utc(row.get("startTime")), as_utc(row.get("publishTime"))
        value = finite_generation(row.get("generation"))
        if delivery is None or published is None or value is None:
            continue
        prior = result.get(delivery)
        if prior is None or published > prior["publishTime"]:
            result[delivery] = {"generation": value, "publishTime": published}
    return result


def select_forecasts(records: list[dict[str, Any]], cutoff_hour: int = 12, cutoff_minute: int = 0) -> dict[datetime, dict[str, Any]]:
    """Select latest valid vintage published by D-1 cutoff (Europe/London).

    This is an explicit pilot convention; it is not represented as an official
    market deadline. A forecast is eligible when publishTime <= cutoff.
    """
    result: dict[datetime, dict[str, Any]] = {}
    for row in records:
        delivery, published = as_utc(row.get("startTime")), as_utc(row.get("publishTime"))
        value = finite_generation(row.get("generation"))
        if delivery is None or published is None or value is None:
            continue
        delivery_day = delivery.astimezone(LONDON).date()
        cutoff_local = datetime.combine(delivery_day - timedelta(days=1), time(cutoff_hour, cutoff_minute), tzinfo=LONDON)
        cutoff = cutoff_local.astimezone(UTC)
        if published > cutoff:
            continue
        prior = result.get(delivery)
        # Stable winner for duplicate publication timestamps: first valid row.
        if prior is None or published > prior["publishTime"]:
            result[delivery] = {"generation": value, "publishTime": published}
    return result


def build_analysis(actual_rows: list[dict[str, Any]], forecast_rows: list[dict[str, Any]], cutoff_hour: int = 12, cutoff_minute: int = 0) -> dict[str, Any]:
    actuals = normalize_actuals(actual_rows)
    forecasts = select_forecasts(forecast_rows, cutoff_hour, cutoff_minute)
    month_start = datetime(2026, 1, 1, tzinfo=UTC)
    month_end = datetime(2026, 2, 1, tzinfo=UTC)
    intervals: list[dict[str, Any]] = []
    errors: list[float] = []
    actual_values: list[float] = []
    for delivery in sorted(set(actuals) | set(forecasts)):
        if not (month_start <= delivery < month_end):
            continue
        actual, forecast = actuals.get(delivery), forecasts.get(delivery)
        matched = actual is not None and forecast is not None
        error = forecast["generation"] - actual["generation"] if matched else None
        if matched:
            errors.append(error)
            actual_values.append(actual["generation"])
        intervals.append({
            "startTime": delivery.isoformat().replace("+00:00", "Z"),
            "actualMw": actual["generation"] if actual else None,
            "forecastMw": forecast["generation"] if forecast else None,
            "forecastPublishedAt": forecast["publishTime"].isoformat().replace("+00:00", "Z") if forecast else None,
            "actualPublishedAt": actual["publishTime"].isoformat().replace("+00:00", "Z") if actual else None,
            "errorMw": error,
            "absoluteErrorMw": abs(error) if error is not None else None,
            "matched": matched,
        })
    pairs = len(errors)
    abs_errors = [abs(v) for v in errors]
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in intervals:
        buckets[row["startTime"][:10]].append(row)
    daily = []
    for day, rows in sorted(buckets.items()):
        paired = [r for r in rows if r["matched"]]
        daily.append({
            "date": day,
            "actualMw": round(sum(r["actualMw"] for r in paired) / len(paired), 1) if paired else None,
            "forecastMw": round(sum(r["forecastMw"] for r in paired) / len(paired), 1) if paired else None,
            "matchedIntervals": len(paired),
        })
    nonzero = [(e, a) for e, a in zip(errors, actual_values) if a > 0]
    return {
        "period": {"from": "2026-01-01", "toExclusive": "2026-02-01"},
        "cutoff": {"time": f"{cutoff_hour:02d}:{cutoff_minute:02d}", "timezone": "Europe/London", "rule": "previous calendar day; configurable pilot assumption, not an official market deadline"},
        "metrics": {
            "matchedIntervals": pairs,
            "expectedIntervals": 31 * 48,
            "coveragePct": round(pairs / (31 * 48) * 100, 1),
            "maeMw": round(sum(abs_errors) / pairs, 1) if pairs else None,
            "rmseMw": round((sum(v * v for v in errors) / pairs) ** 0.5, 1) if pairs else None,
            "biasMw": round(sum(errors) / pairs, 1) if pairs else None,
            "meanActualMw": round(sum(actual_values) / pairs, 1) if pairs else None,
            "meanAbsolutePercentError": round(sum(abs(e) / a for e, a in nonzero) / len(nonzero) * 100, 1) if nonzero else None,
        },
        "daily": daily,
        "intervals": intervals,
        "sources": {"actuals": "Elexon BMRS FUELHH (fuelType=WIND)", "forecasts": "Elexon BMRS WINDFOR", "units": "MW", "actualRecordCount": len(actuals), "forecastVintageCount": len(forecasts)},
        "limitations": ["January 2026 is interpreted as delivery intervals in January.", "The cutoff is a pilot assumption because the brief gives no decision time.", "Only matched delivery intervals contribute to accuracy metrics; coverage is shown.", "MAPE excludes zero-actual intervals; MAE, RMSE and signed bias remain in MW."],
    }

