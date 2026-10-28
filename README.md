# Wind Vintage

A national UK wind generation forecast and forecast-accuracy portal for day-ahead procurement analysis. The dashboard uses actual generation from Elexon BMRS `FUELHH` filtered to `fuelType=WIND` and forecast vintages from `WINDFOR`.

## Project structure

```text
backend/app/main.py                 FastAPI endpoints and React static-file serving
backend/app/elexon.py               Elexon HTTP client, timeouts, retries and source queries
backend/app/analytics.py            Timestamp cleanup, vintage selection and error metrics
backend/tests/test_analytics.py     Forecast cutoff and calculation unit tests
backend/requirements.txt            Python API dependencies
frontend/index.html                 Frontend document and page metadata
frontend/src/main.jsx               React dashboard, metrics, chart, controls and CSV export
frontend/src/styles.css             Responsive dashboard styles
frontend/package.json               Frontend scripts and dependencies
frontend/pnpm-lock.yaml             Pinned frontend dependency graph
frontend/pnpm-workspace.yaml        pnpm install/build-script policy
frontend/vite.config.js             React build settings and local API proxy
docs/requirements-checklist.md      PDF and user-prompt requirement traceability
docs/data-verification.md           Live API schema, availability and metric evidence
docs/demo-script.md                 Two-part timed demo and recording checklist
docs/submission-checklist.md        URL fields, publication steps and incognito checklist
Dockerfile                          Multi-stage frontend and Python API container
docker-compose.yml                  Local container setup
.dockerignore                       Container build exclusions
.env.example                        Non-secret configurable API settings
.gitignore                          Local environment/build exclusions
README.md                           Setup, methodology, deployment and AI disclosure
```

## Run locally

Requirements: Python 3.12+, Node.js 20+, and pnpm 11.

1. Install the backend dependencies and start the API:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. In another terminal, install and start the React frontend:

   ```powershell
   cd frontend
   pnpm install --frozen-lockfile
   pnpm run dev
   ```

   Open the Vite URL printed in the terminal. Requests to `/api` are proxied to `localhost:8000`.

The backend calls Elexon's public API directly. No API key is required for the tested endpoints. `ELEXON_API_BASE` and `ELEXON_TIMEOUT_SECONDS` can be set from the environment; see `.env.example`. Elexon access failures are shown as errors instead of substituting sample data.

## Docker

From the project root:

```powershell
docker compose up --build
```

Open `http://localhost:8000`. To stop the service, press `Ctrl+C` and run `docker compose down`.

## Deployment

This is a single-container React + Python application and is prepared for Heroku Container Registry deployment. After installing Docker and the Heroku CLI and signing in, from the project root:

```powershell
heroku create <anonymous-app-name> --stack container
heroku container:login
heroku container:push web -a <anonymous-app-name>
heroku container:release web -a <anonymous-app-name>
heroku open -a <anonymous-app-name>
```

Heroku supplies `PORT`, which the container uses. A public deployment has **not** been created or verified; replace this line with the real accessible URL after deployment: **Not deployed yet.**

Public source repository: https://github.com/ankush-48/k7v3m9q2 (public; the repository slug is randomly generated). See `docs/submission-checklist.md` for the remaining deployment, video, and form steps.

## Business interpretation and methodology

- **Scope:** delivery intervals from 1 January through 31 January 2026; only national wind generation data from Elexon.
- **Actuals:** `FUELHH` filtered to `WIND`; interval key `startTime`, value `generation`.
- **Forecasts:** `WINDFOR`; interval key `startTime`, publication timestamp `publishTime`, value `generation`.
- **Cutoff assumption:** the brief does not define a clock-time cutoff. The app defaults to 12:00 Europe/London on the calendar day before delivery, with selectable 10:00, 12:00, 16:00 and 18:00 cutoffs. This is a transparent pilot convention, not an official market rule.
- For each delivery interval, the latest valid forecast with `publishTime <= cutoff` is selected. Later publications are excluded. Timestamps are normalized to UTC; actuals are deduplicated by latest publication; forecasts and actuals are joined on delivery interval. Duplicate forecast publication timestamps are resolved by keeping the first valid row in API order.
- An interval missing either value is retained in detail and excluded from paired accuracy metrics. Coverage is measured against 1,488 expected half-hourly intervals.
- Metrics: MAE and RMSE in MW; signed bias is forecast minus actual (positive means over-forecast); MAPE excludes zero-actual intervals. The daily chart shows mean MW over matched intervals, not summed energy.

## API and data notes

The Elexon stream endpoints are queried by `publishDateTimeFrom` / `publishDateTimeTo`. Using `from` / `to` returned the latest snapshot during investigation, not the requested historical period; publication-time filtering is necessary to retrieve superseded WINDFOR vintages. The app requests FUELHH publication records for 1 Jan–1 Feb 2026 and WINDFOR publications from 30 Dec 2025 through 1 Feb 2026 so eligible vintages for 1 January delivery can be considered.

Live verification on 29 October 2026 returned HTTP 200 for both stream endpoints without credentials: 1,489 FUELHH WIND rows for the January publication window and 19,272 WINDFOR rows for the forecast window. The 12:00 cutoff produced 744 paired intervals out of 1,488 (50.0%), MAE 2,002.9 MW, RMSE 2,470.1 MW, and signed bias +1,805.9 MW. The Elexon developer portal says streams return JSON and have no restrictions or limits on data return; endpoint docs list 429 and 500 errors but no numeric rate quota. The client retries 429 and transient 5xx responses. See `docs/data-verification.md` for full details and assumptions.

## Verification

Run the backend unit tests with:

```powershell
cd backend
py -m unittest discover -s tests -v
```

Build the React interface with:

```powershell
cd frontend
pnpm run build
```

## AI disclosure

OpenAI Codex was used to assist with requirements analysis, implementation, and documentation. The application code and reported data results were reviewed against the available requirements and API evidence. Tests and deployment claims are reported only after execution/verification.

## Demo and handoff

- Two-part, timed video presentation script and recording checklist: `docs/demo-script.md`.
- Challenge requirement-by-requirement traceability: `docs/requirements-checklist.md`.
- Submission URLs and manual incognito checklist: `docs/submission-checklist.md`.

