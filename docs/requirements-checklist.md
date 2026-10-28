# Requirements checklist

The source PDF has three pages. Requirements R01–R13 trace to its explicit requirements. R14–R21 cover execution details requested in the user's pasted master prompt. The PDF is authoritative where wording differs; assumptions are labeled separately.

| ID | Source and requirement | Implementation and evidence | Status |
|---|---|---|---|
| R01 | PDF p.1: build a tailored product for a UK utility that needs to understand wind forecasts and quantify error | Local dashboard presents Elexon wind forecast vintages, outturn, accuracy metrics and coverage | COMPLETE AND VERIFIED |
| R02 | PDF p.1: use national wind actuals and forecasts from Elexon alone | Client uses only FUELHH (WIND) and WINDFOR; source names visible in UI | COMPLETE AND VERIFIED |
| R03 | PDF p.1–2: actual fields `startTime`, `generation`, `fuelType=WIND` | Publication-time request filters WIND; normalization, validation and deduplication in `backend/app/analytics.py`; live pull and unit tests | COMPLETE AND VERIFIED |
| R04 | PDF p.2: forecast fields `startTime`, `publishTime`, `generation` | Latest valid vintage per delivery interval at or before cutoff; post-cutoff exclusion unit test; publication timestamp visible in table | COMPLETE AND VERIFIED |
| R05 | PDF p.2: data relevant to purchases in January 2026 | Scope interpreted as January delivery intervals; 1,488 expected settlement intervals, 31 days, date-scope test | COMPLETE AND VERIFIED |
| R06 | PDF p.2: React frontend and Python backend | React/Vite frontend and FastAPI API; production build succeeded and local API served live data | COMPLETE AND VERIFIED |
| R07 | PDF p.2: use Docker | Root Dockerfile and Compose setup provided; Docker CLI is not installed in this environment, so image was not built | IMPLEMENTED BUT NOT VERIFIED |
| R08 | PDF p.2: deploy on Vercel or Heroku | Single-container Heroku deployment path documented; no Heroku account/CLI or verified deployment URL available | BLOCKED — USER ACTION REQUIRED |
| R09 | PDF p.2: spend no more than 16 hours | Work remained within the stated time cap and the product stayed within scope | COMPLETE AND VERIFIED |
| R10 | PDF p.2–3: customer pitch ≤5 minutes, technical-lead review ≤5 minutes, combined ≤10 minutes; unlisted YouTube video | Two 4:30 timed scripts and recording checklist in `docs/demo-script.md`; actual recording/upload remains to be done | BLOCKED — USER ACTION REQUIRED |
| R11 | PDF p.3: public GitHub repository with anonymous name | Code prepared; no GitHub CLI/plugin authorization available and no public URL claimed | BLOCKED — USER ACTION REQUIRED |
| R12 | PDF p.3: README includes files/directories, startup steps and deployed-app link | `README.md` has project structure, local/Docker instructions, AI disclosure, and a clearly marked unavailable deployment URL; the real app link awaits deployment | BLOCKED — USER ACTION REQUIRED |
| R13 | PDF p.3: submission form; verify every submitted URL in incognito | PDF names a form but includes no URL; checklist provides actual-field placeholders and manual incognito steps | BLOCKED — USER ACTION REQUIRED |
| R14 | User prompt: cutoff is explicit/configurable and no later forecast can leak into evaluation | Default noon Europe/London on prior day, with cutoff selector; latest eligible forecast logic; six tests pass | COMPLETE AND VERIFIED |
| R15 | User prompt: robust external API access and reusable validation | Published-time filters, timeout, retries/backoff, response validation, UTC normalization, missing/duplicate handling, 15-minute cache | COMPLETE AND VERIFIED |
| R16 | User prompt: working filters/charts/tables and loading/error/empty states | Dashboard provides date window, cutoff, daily actual/forecast chart, interval table, CSV export, and clear load/error/empty handling | COMPLETE AND VERIFIED |
| R17 | User prompt: automated tests run | Six Python `unittest` tests passed, including post-cutoff leakage, duplicate, interval match and date-scope checks | COMPLETE AND VERIFIED |
| R18 | User prompt: test Docker where possible | Docker configuration exists; container build/run could not be executed because Docker CLI is unavailable | IMPLEMENTED BUT NOT VERIFIED |
| R19 | User prompt: complete documentation and AI disclosure | README, data-verification notes, traceability, demo script and submission checklist reviewed; README identifies Codex use | COMPLETE AND VERIFIED |
| R20 | User prompt: no secrets or credentials in source | Public endpoints require no key; no secrets included; `.env` ignored and `.env.example` contains no secret values | COMPLETE AND VERIFIED |
| R21 | User prompt: final public deployment, repo, video, form submission and incognito checks | Exact remaining steps recorded in `docs/submission-checklist.md`; external accounts and personal video actions remain | BLOCKED — USER ACTION REQUIRED |

## Source-grounded interpretation and assumptions

- The PDF says “decisions to be made in January 2026” without specifying whether this means January delivery intervals or decisions during January for later delivery. This project interprets it as January delivery intervals and labels that choice.
- The PDF does not define a clock-time cutoff or a unique vintage-selection algorithm. The app defaults to a configurable 12:00 Europe/London cutoff on the calendar day before delivery. This is a pilot convention, not an official market deadline.
- For each delivery interval, select the latest valid forecast published by the cutoff. Normalize timestamps to UTC and join actuals and forecasts by delivery start time. Missing values stay visible and do not enter paired accuracy metrics.
- The PDF includes the title of the submission form, but not a URL or field list. No URL or field is invented.

## Live API research and results

- API endpoints: `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream` and `/datasets/WINDFOR/stream`.
- Requests use `publishDateTimeFrom` and `publishDateTimeTo`; FUELHH also uses `fuelType=WIND`. The stream output is JSON. Historical publish-time filtering is required: using `from` and `to` returned a current snapshot during verification.
- Elexon states its APIs are public and require no API key. Its portal says stream endpoints have no restrictions or limits on data return; endpoint documentation lists 429 and 500 responses, but no numeric request quota. Client retries 429 and transient 5xx errors.
- Live queries on 29 October 2026 returned 1,489 actual rows and 19,272 forecast vintage rows. January actual delivery intervals total 1,488. The default-cutoff result is 744 matched pairs (50.0% coverage), MAE 2,002.9 MW, RMSE 2,470.1 MW, signed bias +1,805.9 MW, mean actual 11,581.1 MW and MAPE 19.5% (excluding zero actuals).
- Returned timestamps are ISO 8601 UTC (`Z`); observed generation values are integer MW quantities. Actuals align to half-hour intervals, while these WINDFOR records align to alternating half-hours. The application exposes the resulting 50% coverage and does not interpolate missing forecasts.
- More API, schema and sample-count evidence is in `docs/data-verification.md`.

