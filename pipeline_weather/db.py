"""PostgreSQL persistence for raw and curated weather data."""
from __future__ import annotations

import json
import os
from collections.abc import Iterable

import psycopg


def database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://weather:weather@localhost:5432/weather")


def _setup(connection: psycopg.Connection) -> None:
    connection.execute("CREATE SCHEMA IF NOT EXISTS weather")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS weather.raw_forecast_ingestions (
          city TEXT NOT NULL,
          fetched_at TIMESTAMPTZ NOT NULL,
          payload JSONB NOT NULL,
          PRIMARY KEY (city, fetched_at)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS weather.daily_forecast (
          city TEXT NOT NULL,
          forecast_date DATE NOT NULL,
          temperature_max_c DOUBLE PRECISION NOT NULL,
          temperature_min_c DOUBLE PRECISION NOT NULL,
          precipitation_mm DOUBLE PRECISION NOT NULL,
          weather_code INTEGER NOT NULL,
          source_fetched_at TIMESTAMPTZ NOT NULL,
          loaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          PRIMARY KEY (city, forecast_date)
        )
    """)


def store_raw_forecasts(records: Iterable[dict]) -> int:
    records = list(records)
    with psycopg.connect(database_url(), autocommit=True) as connection:
        _setup(connection)
        for record in records:
            connection.execute(
                """INSERT INTO weather.raw_forecast_ingestions (city, fetched_at, payload)
                   VALUES (%s, %s, %s::jsonb) ON CONFLICT DO NOTHING""",
                (record["city"]["city"], record["fetched_at"], json.dumps(record["payload"])),
            )
    return len(records)


def upsert_daily_forecasts(rows: Iterable[dict]) -> int:
    rows = list(rows)
    with psycopg.connect(database_url(), autocommit=True) as connection:
        _setup(connection)
        for row in rows:
            connection.execute(
                """INSERT INTO weather.daily_forecast
                (city, forecast_date, temperature_max_c, temperature_min_c, precipitation_mm, weather_code, source_fetched_at)
                VALUES (%(city)s, %(forecast_date)s, %(temperature_max_c)s, %(temperature_min_c)s,
                        %(precipitation_mm)s, %(weather_code)s, %(source_fetched_at)s)
                ON CONFLICT (city, forecast_date) DO UPDATE SET
                  temperature_max_c = EXCLUDED.temperature_max_c,
                  temperature_min_c = EXCLUDED.temperature_min_c,
                  precipitation_mm = EXCLUDED.precipitation_mm,
                  weather_code = EXCLUDED.weather_code,
                  source_fetched_at = EXCLUDED.source_fetched_at,
                  loaded_at = now()""",
                row,
            )
    return len(rows)
