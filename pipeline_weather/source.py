"""Open-Meteo API client and pure transformations for the weather pipeline."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CITIES = (
    {"city": "Bangkok", "latitude": 13.7563, "longitude": 100.5018},
    {"city": "Chiang Mai", "latitude": 18.7883, "longitude": 98.9853},
    {"city": "Phuket", "latitude": 7.8804, "longitude": 98.3923},
)


def fetch_city_forecast(city: dict[str, Any], session: Any = requests) -> dict[str, Any]:
    """Fetch a three-day daily forecast from the free Open-Meteo endpoint."""
    response = session.get(
        OPEN_METEO_URL,
        params={
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "Asia/Bangkok",
            "forecast_days": 3,
        },
        timeout=20,
    )
    response.raise_for_status()
    return {"city": city, "fetched_at": datetime.now(UTC).isoformat(), "payload": response.json()}


def normalise_forecast(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert one raw API response into rows for the reporting table."""
    daily = raw["payload"]["daily"]
    return [
        {
            "city": raw["city"]["city"],
            "forecast_date": date,
            "temperature_max_c": daily["temperature_2m_max"][index],
            "temperature_min_c": daily["temperature_2m_min"][index],
            "precipitation_mm": daily["precipitation_sum"][index],
            "weather_code": daily["weather_code"][index],
            "source_fetched_at": raw["fetched_at"],
        }
        for index, date in enumerate(daily["time"])
    ]
