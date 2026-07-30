from pipeline_weather.source import normalise_forecast


def test_normalise_forecast_creates_one_row_per_date():
    raw = {
        "city": {"city": "Bangkok"},
        "fetched_at": "2026-07-30T00:00:00+00:00",
        "payload": {"daily": {
            "time": ["2026-07-30", "2026-07-31"],
            "temperature_2m_max": [33.2, 34.1],
            "temperature_2m_min": [26.0, 26.5],
            "precipitation_sum": [1.1, 0.0],
            "weather_code": [61, 2],
        }},
    }

    rows = normalise_forecast(raw)

    assert len(rows) == 2
    assert rows[0]["city"] == "Bangkok"
    assert rows[1]["temperature_max_c"] == 34.1


def test_normalise_forecast_keeps_raw_timestamp():
    raw = {
        "city": {"city": "Phuket"}, "fetched_at": "2026-07-30T00:00:00+00:00",
        "payload": {"daily": {"time": ["2026-07-30"], "temperature_2m_max": [31],
        "temperature_2m_min": [25], "precipitation_sum": [3], "weather_code": [80]}},
    }
    assert normalise_forecast(raw)[0]["source_fetched_at"] == raw["fetched_at"]
