"""Dagster assets for the weather forecast pipeline."""
from dagster import AssetCheckResult, AssetExecutionContext, Definitions, asset, asset_check

from pipeline_weather.db import store_raw_forecasts, upsert_daily_forecasts
from pipeline_weather.source import CITIES, fetch_city_forecast, normalise_forecast


@asset(group_name="weather", description="Raw Open-Meteo API responses persisted in PostgreSQL.")
def raw_weather_forecasts(context: AssetExecutionContext) -> list[dict]:
    records = [fetch_city_forecast(city) for city in CITIES]
    stored = store_raw_forecasts(records)
    context.add_output_metadata({"cities": len(records), "raw_records_stored": stored})
    return records


@asset(group_name="weather", description="Three-day city-level forecast reporting table.")
def daily_weather_forecast(context: AssetExecutionContext, raw_weather_forecasts: list[dict]) -> int:
    rows = [row for record in raw_weather_forecasts for row in normalise_forecast(record)]
    loaded = upsert_daily_forecasts(rows)
    context.add_output_metadata({"rows_loaded": loaded})
    return loaded


@asset_check(asset=daily_weather_forecast, description="A successful load must create at least one report row.")
def daily_weather_forecast_has_rows(daily_weather_forecast: int) -> AssetCheckResult:
    return AssetCheckResult(passed=daily_weather_forecast > 0, metadata={"rows_loaded": daily_weather_forecast})


defs = Definitions(
    assets=[raw_weather_forecasts, daily_weather_forecast],
    asset_checks=[daily_weather_forecast_has_rows],
)
