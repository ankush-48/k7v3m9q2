# Elexon API and January 2026 data verification

Verification date: 29 October 2026. The application calls only the official Elexon BMRS Insights API datasets named in the assignment.

## Requests and returned records

- Base: `https://data.elexon.co.uk/bmrs/api/v1`
- Official references: [FUELHH stream API documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream), [WINDFOR stream API documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream), and [Elexon Insights API developer portal](https://developer.data.elexon.co.uk/).
- Actuals: `GET /datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-02-01T00:00:00Z&fuelType=WIND`
- Forecasts: `GET /datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-02-01T00:00:00Z`
- `format` is omitted because stream endpoints return JSON only. The stream responses are JSON arrays of records; the non-stream dataset endpoint may wrap records in a `data` property, which the client also accepts.
- Both live requests returned HTTP 200 without an API key. Elexon states its APIs are public and do not require an API key.
- The actual publication window returned 1,489 rows: it includes the interval immediately before January and captures the final January interval when it is published at the February boundary. Filtering on delivery `startTime` yields all 1,488 January actual intervals.
- The forecast publication window returned 19,272 vintage records. The analysis selected 744 delivery intervals with a valid forecast by the default cutoff; paired actual/forecast coverage was 744/1,488 (50%). This directly shows historical superseded WINDFOR versions are available through the publication-time-filtered dataset endpoint.
- At the default cutoff, verified January metrics are: MAE 2,002.9 MW; RMSE 2,470.1 MW; signed bias +1,805.9 MW; mean actual generation on paired intervals 11,581.1 MW; MAPE 19.5% with zero-actual intervals excluded. These values reflect this API snapshot and selection convention; they are not trading recommendations.

## Schema, interval and validation observations

- The response records include `publishTime`, `startTime`, `generation`; FUELHH also includes `fuelType`, `settlementDate` and `settlementPeriod`.
- Timestamps are ISO 8601 values with `Z` (UTC) in the observed stream response. The processing layer normalizes timestamps to UTC and assumes UTC only if an input timestamp lacks a timezone.
- Generation values are integer MW quantities in the observed records. The [Elexon wind generation view](https://bmrs.elexon.co.uk/wind-generation) labels generation totals in MW; the dashboard labels all values and errors in MW.
- Actual FUELHH has half-hourly January records. The WINDFOR vintage data only aligns to every other half-hour interval in this evaluation, leaving the alternating intervals unmatched. The UI exposes the 50% coverage and leaves unmatched intervals visible instead of interpolating or copying values.
- Invalid timestamps, missing or non-finite generation values, and negative generation values are rejected. FUELHH is filtered to WIND even though the request also carries the filter. Duplicated actuals are resolved by latest `publishTime`; duplicated forecast publication times are resolved by first valid row in API order.
- Forecast vintages are ranked per exact `startTime`; any forecast published after the interval's previous-day Europe/London cutoff is excluded.

## API constraints and limitations

- Elexon's developer portal states that stream endpoints return JSON, support published-time retrieval of superseded dataset records, and have no restrictions or limits on data return. Endpoint documentation lists HTTP 400, 429 and 500 responses. No numeric request-rate quota was found; the client uses a timeout and retries 429 and transient 5xx responses with backoff.
- Historical `from`/`to` request parameters returned a current snapshot during the live check. `publishDateTimeFrom` and `publishDateTimeTo` are necessary for historical vintage extraction.
- The stream service returns all available records for the bounded window in one response. There is no cursor/page token in the observed stream format.
- The documentation describes the wind forecast as updated up to eight times daily. This schedule is not used as the decision cutoff.
- The assignment provides no exact meaning for “decisions to be made in January 2026,” decision time, or official selection algorithm. The app interprets this as January delivery intervals and offers a configurable 12:00 previous-day default, clearly labeled as a pilot convention.
- `from`/`to` behavior, response size and record counts were verified live. No age-based retention cutoff was published; the requested January 2026 period was demonstrably queryable on 29 October 2026.

