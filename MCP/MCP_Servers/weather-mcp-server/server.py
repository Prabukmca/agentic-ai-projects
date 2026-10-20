import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from weather_service import (
    check_rain_today_evening as check_rain_today_evening_service,
    get_current_weather as get_current_weather_service,
    get_weather_forecast as get_weather_forecast_service,
    parse_location_input,
)

mcp = FastMCP(
    "weather-mcp-server",
    instructions=(
        "Provide live weather data for India using city, state, and optional pincode. "
        "If OPENWEATHER_API_KEY is missing, return a clear error instead of using demo data."
    ),
)


@mcp.tool()
def get_current_weather(city: str, state: str | None = None, pincode: str | None = None) -> dict:
    """Get the current weather for a city, state, or pincode in India."""
    return get_current_weather_service(city, state, pincode)


@mcp.tool()
def get_weather_forecast(city: str, state: str | None = None, pincode: str | None = None, days: int = 3) -> dict:
    """Get a short forecast for a city or pincode in India."""
    return get_weather_forecast_service(city, state, pincode, days)


@mcp.tool()
def check_rain_today_evening(city: str, state: str | None = None, pincode: str | None = None) -> dict:
    """Check whether rain is likely this evening."""
    return check_rain_today_evening_service(city, state, pincode)


if __name__ == "__main__":
    mcp.run("stdio")
