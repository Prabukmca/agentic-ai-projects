import importlib.util
from pathlib import Path

import weather_service

SERVER_PATH = Path(__file__).with_name("server.py")

spec = importlib.util.spec_from_file_location("weather_mcp_server", SERVER_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_location_parser_accepts_city_state_and_pincode():
    location = module.parse_location_input("Will it rain today evening in Pune, Maharashtra 411001?")
    assert location["city"] == "Pune"
    assert location["state"] == "Maharashtra"
    assert location["pincode"] == "411001"


def test_missing_weather_key_returns_clear_error():
    module.os.environ.pop("OPENWEATHER_API_KEY", None)
    response = module.get_current_weather("Pune", "Maharashtra", "411001")
    assert response["status"] == "error"
    assert "No valid API key" in response["message"]


def test_rain_check_handles_evening_rain(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test_key")

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, params=None, timeout=10):
        if "/geo/1.0/zip" in url:
            return MockResponse({"lat": 18.5204, "lon": 73.8567, "name": "Pune", "state": "Maharashtra", "country": "IN"})
        if "/data/2.5/forecast" in url:
            return MockResponse({
                "list": [
                    {"dt_txt": "2026-10-20 18:00:00", "main": {"temp": 26}, "weather": [{"description": "rain"}], "pop": 0.8}
                ]
            })
        if "/data/2.5/weather" in url:
            return MockResponse({"name": "Pune", "main": {"temp": 27, "humidity": 72}, "weather": [{"description": "light rain"}], "wind": {"speed": 4.4}})
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(weather_service.requests, "get", fake_get)
    result = module.check_rain_today_evening("Pune", "Maharashtra", "411001")
    assert result["status"] == "success"
    assert "location" in result
    assert "summary" in result
    assert "rain_probability" in result
