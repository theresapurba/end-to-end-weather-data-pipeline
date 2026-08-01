# Pipeline_Analytics

A Dagster data pipeline that fetches three-day weather forecasts for **Bangkok**, **Chiang Mai**, and **Phuket** from the free [Open-Meteo API](https://open-meteo.com/), stores the raw API responses, and loads a clean reporting table into PostgreSQL.

Built as a capstone portfolio project to show end-to-end pipeline design: ingestion, persistence, transformation, and data quality checks.
---

## What it does

1. **Fetches** daily forecast data (temperature, precipitation, weather code) for three Thai cities.
2. **Stores raw responses** in PostgreSQL as JSON for audit and replay.
3. **Builds a reporting table** with one row per city and forecast date.
4. **Runs a quality check** to confirm at least one row was loaded.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- (Optional, for local tests only) Python 3.11

---

## Quick start

From the repository root:

```bash
docker compose up --build
```

When all containers are healthy:

1. Open **http://localhost:3000** in your browser.
2. Go to **Deployment → Code Locations** and confirm `pipeline_weather` is listed.
3. Go to **Assets** and click **Materialize all**.
4. When the run finishes, the asset check `daily_weather_forecast_has_rows` should show as **passed**.

To stop the stack:

```bash
docker compose down
```

---

## Project structure

```text
.
├── docker-compose.yml          # Postgres, Dagster UI, and the weather pipeline
├── workspace.yaml              # Registers pipeline_weather as a code location
├── Dockerfile_dagster          # Dagster webserver and daemon image
└── pipeline_weather/
    ├── Dockerfile              # User-code container (gRPC server)
    ├── main.py                 # Dagster assets and asset checks
    ├── source.py               # Open-Meteo API client and transformations
    ├── db.py                   # PostgreSQL read/write helpers
    ├── requirements.txt
    └── tests/
        └── test_source.py      # Unit tests for forecast normalization
```

---

## Architecture

```text
Open-Meteo API
      │
      ▼
raw_weather_forecasts ──► weather.raw_forecast_ingestions  (JSONB, append-only)
      │
      ▼
daily_weather_forecast ──► weather.daily_forecast          (curated reporting table)
      │
      ▼
daily_weather_forecast_has_rows                            (Dagster asset check)
```

### Docker services

| Service | Role |
|---|---|
| `postgres` | Stores raw and curated weather data |
| `pipeline-weather` | Runs the Dagster gRPC server with pipeline code |
| `dagster-webserver` | Web UI at port 3000 |
| `dagster-daemon` | Background process for schedules and sensors |

---

## Database output

After a successful run, PostgreSQL contains two tables in the `weather` schema:

**`weather.raw_forecast_ingestions`** — full API payloads, keyed by `(city, fetched_at)`.

**`weather.daily_forecast`** — one row per `(city, forecast_date)` with:

| Column | Description |
|---|---|
| `temperature_max_c` / `temperature_min_c` | Daily high and low (°C) |
| `precipitation_mm` | Total precipitation |
| `weather_code` | WMO weather code from Open-Meteo |
| `source_fetched_at` | When the API was called |
| `loaded_at` | When the row was written |

Re-running the pipeline upserts by `(city, forecast_date)`, so repeated materializations are safe.

Example query (inside the Postgres container):

```bash
docker exec -it bigdataproject-postgres-1 psql -U weather -d weather \
  -c "SELECT city, forecast_date, temperature_max_c FROM weather.daily_forecast ORDER BY city, forecast_date;"
```

---

## Run tests

Tests cover the forecast normalization logic and do not require Docker or network access.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r pipeline_weather/requirements.txt
pytest pipeline_weather/tests -v
```

---

## Troubleshooting

### `DagsterRunNotFoundError: gRPC server could not load run ...`

This happens when the Dagster UI (webserver) creates a run, but the pipeline container cannot read the shared run history.

**Fix:** Recreate the stack so all services share `dagster_home`:

```bash
docker compose down
docker compose up --build
```

The `pipeline-weather` service must have both:

- `DAGSTER_HOME=/opt/dagster/dagster_home`
- `./dagster_home` mounted at `/opt/dagster/dagster_home`

If the error persists after recreating containers, remove stale local state and start fresh:

```bash
docker compose down -v
docker compose up --build
```

> **Note:** `docker compose down -v` deletes the Postgres volume and any loaded forecast data.

---

## Production notes

This setup is intentionally small and local. For a production deployment I would add:

- Managed PostgreSQL and object storage for raw archives
- Secrets management for database credentials
- Retries, alerting, and API rate-limit monitoring
- Scheduled materialization and freshness checks
- An append-only history table instead of upserts only
- Broader data-quality checks (temperature ranges, null checks, row counts per city)

---

## Tech stack

- **Orchestration:** [Dagster](https://dagster.io/) 1.8
- **Database:** PostgreSQL 16
- **Data source:** [Open-Meteo Forecast API](https://open-meteo.com/)
- **Language:** Python 3.11
"# end-to-end-weather-data-pipeline" 
