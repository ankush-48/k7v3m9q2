# Two-part demonstration script

The assignment asks for an unlisted YouTube video, with a customer-facing overview and technical review of no more than five minutes each (10 minutes total). This script is prepared for recording; no video has been recorded or uploaded.

## Part 1 — Customer overview (target: 4 minutes 30 seconds)

**0:00–0:30 | The procurement question**  
“Your team commits to day-ahead purchases with uncertainty in wind output. This view focuses on a specific decision question: what was the latest national wind forecast available at the cutoff, and how did it compare with actual generation?”

**0:30–1:15 | Scope and provenance**  
Point to the January 2026 scope and Elexon source. Explain that the analysis uses only FUELHH wind actuals and WINDFOR forecasts, with no other energy datasets. Point out the visible publication cutoff and explain that noon on the prior calendar day is a disclosed pilot assumption because the brief does not set an exact time.

**1:15–2:30 | Headline accuracy**  
Read the computed MAE, bias, RMSE and interval coverage from the running app. Explain MAE as the typical absolute MW miss, bias as over- or under-forecast tendency, RMSE as more sensitive to large misses, and coverage as the fraction of expected delivery intervals that could be paired. Do not quote a number unless it is visibly loaded from Elexon-derived data.

**2:30–3:30 | Profile and uncertainty**  
Use the daily chart to show when forecast and actual profiles diverge. Explain that a daily average makes the month easier to scan, while interval data remains available below. Frame the errors as uncertainty evidence; do not present them as trading advice or an unsupported procurement recommendation.

**3:30–4:30 | Detail and caveats**  
Show the selected forecast publication time beside its delivery interval and actual. Export the CSV if useful. Close by naming the cutoff assumption, missing-data coverage, and that actual and forecast must match on interval time before contributing to the metrics.

## Part 2 — Technical-lead review (target: 4 minutes 30 seconds)

**0:00–0:40 | Architecture**  
Show the source tree. The React/Vite frontend consumes a Python FastAPI endpoint. The Python service retrieves only FUELHH and WINDFOR from Elexon's Insights API and serves the built frontend in the same container.

**0:40–1:30 | Data flow and API**  
Show `backend/app/elexon.py`. Explain the publication-time query parameters, timeout, bounded retries for rate limits/transient server errors, response-shape checks, and the short in-process cache. Explain why a delivery-time filter is not enough when recovering superseded forecast vintages.

**1:30–2:30 | Selection and calculation**  
Show `backend/app/analytics.py`. Explain UTC normalization, previous-day Europe/London cutoff, latest eligible vintage, actual deduplication, deterministic joins on `startTime`, unmatched coverage, and error sign convention. State clearly that noon is configurable and is not asserted to be an official market deadline.

**2:30–3:20 | Tests and UI**  
Run the unittest command and show tests for post-cutoff exclusion, cutoff inclusivity, duplicates, interval matching, and date scope. Show the responsive dashboard, data-loading/error states and CSV export.

**3:20–4:30 | Delivery and limitations**  
Show `Dockerfile` and `docker-compose.yml`; explain Heroku Container Registry as the prepared single-container deployment target. State which deployment, GitHub, recording, and form steps still require account access and verification. Do not claim a public URL until each is live and checked.

## Recording checklist and screen-sharing sequence

1. Start with the application in a clean browser window and load the live Elexon data before recording.
2. Keep browser zoom high enough for the metric labels and cutoff to be readable.
3. Record Part 1 from the dashboard top through the interval table and methodology notes.
4. Switch to the code editor and terminal for Part 2; show only the data client, analytics module, tests, Dockerfile and README.
5. Run the tests during Part 2 if that does not push the recording past five minutes.
6. Keep each part under five minutes and the complete video under ten minutes.
7. Review audio, screen readability, and the final duration; remove terminal output containing local paths or credentials if any appear.
8. Upload to YouTube, set visibility to Unlisted, open the video in a signed-out/incognito window, and copy the actual video URL into the submission checklist.

