import os
import re
from typing import Any

import requests

from config import (
    WEATHER_DATA_URL,
    WEATHER_GEO_URL,
    get_weather_api_key,
)


def parse_location_input(text: str | None) -> dict[str, str | None]:
    if not text:
        return {"city": None, "state": None, "pincode": None}

    cleaned = str(text).strip()
    if not cleaned:
        return {"city": None, "state": None, "pincode": None}

    pincode_match = re.search(r"\b(\d{6})\b", cleaned)
    pincode = pincode_match.group(1) if pincode_match else None
    if pincode:
        cleaned = cleaned.replace(pincode, "").strip()

    if " in " in cleaned.lower():
        cleaned = cleaned.split(" in ", 1)[1].strip()

    cleaned = re.sub(
        r"^(what is the|show|tell me|check|will it rain|forecast|current weather|weather)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = cleaned.strip(" ,.;?!")

    if not cleaned:
        return {"city": None, "state": None, "pincode": pincode}

    if "," in cleaned:
        city_part, state_part = cleaned.split(",", 1)
        city = city_part.strip()
        state = state_part.strip()
    else:
        parts = cleaned.split()
        if len(parts) >= 2:
            city = parts[0].strip()
            state = " ".join(parts[1:]).strip()
        else:
            city = cleaned.strip()
            state = None

    if state and state.lower() in {"india", "in"}:
        state = None

    return {"city": city or None, "state": state or None, "pincode": pincode}


def _build_location_query(city: str | None, state: str | None = None, pincode: str | None = None) -> tuple[str | None, str | None, str | None, str | None]:
    if pincode:
        return None, None, pincode, "IN"

    query_parts = []
    if city:
        query_parts.append(city.strip())
    if state:
        query_parts.append(state.strip())
    if query_parts:
        query_parts.append("India")
    query = ", ".join(query_parts)
    return query, city.strip() if city else None, state.strip() if state else None, "IN"


def _resolve_coordinates(city: str | None, state: str | None = None, pincode: str | None = None) -> dict[str, Any] | None:
    api_key = get_weather_api_key()
    if not api_key:
        return None

    if pincode:
        url = f"{WEATHER_GEO_URL}/zip"
        params = {"zip": f"{pincode},IN", "appid": api_key}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            return {
                "lat": float(payload.get("lat", 0)),
                "lon": float(payload.get("lon", 0)),
                "city": city or payload.get("name", "Unknown"),
                "state": state or payload.get("state", "India"),
                "country": payload.get("country", "IN"),
            }
        except (requests.RequestException, ValueError, TypeError):
            return None

    query, resolved_city, resolved_state, country = _build_location_query(city, state, pincode)
    if not query:
        return None

    url = f"{WEATHER_GEO_URL}/direct"
    params = {"q": query, "limit": 1, "appid": api_key}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if not payload:
            return None
        location = payload[0]
        return {
            "lat": float(location.get("lat", 0)),
            "lon": float(location.get("lon", 0)),
            "city": resolved_city or location.get("name", "Unknown"),
            "state": resolved_state or location.get("state", "India"),
            "country": location.get("country", country or "IN"),
        }
    except (requests.RequestException, ValueError, TypeError):
        return None


def get_current_weather(city: str, state: str | None = None, pincode: str | None = None) -> dict[str, Any]:
    api_key = get_weather_api_key()
    if not api_key:
        return {
            "status": "error",
            "message": "No valid API key found. Set OPENWEATHER_API_KEY in the project .env or environment before requesting weather data.",
        }

    resolved = _resolve_coordinates(city, state, pincode)
    if resolved is None:
        return {
            "status": "error",
            "message": "Unable to resolve the requested location. Please provide a valid Indian city, state, or pincode.",
        }

    params = {
        "lat": resolved["lat"],
        "lon": resolved["lon"],
        "units": "metric",
        "appid": api_key,
    }
    try:
        response = requests.get(f"{WEATHER_DATA_URL}/weather", params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return {
            "status": "success",
            "city": payload.get("name", resolved["city"]),
            "state": resolved["state"],
            "country": resolved["country"],
            "temperature_c": round(float(payload.get("main", {}).get("temp", 0))),
            "condition": payload.get("weather", [{}])[0].get("description", "Clear").title(),
            "humidity": int(payload.get("main", {}).get("humidity", 0)),
            "wind_speed_kmh": round(float(payload.get("wind", {}).get("speed", 0) * 3.6)),
            "source": "openweather",
        }
    except (requests.RequestException, ValueError, TypeError):
        return {
            "status": "error",
            "message": "Weather API request failed. Please try again later or verify the API key is valid.",
        }


def get_weather_forecast(city: str, state: str | None = None, pincode: str | None = None, days: int = 3) -> dict[str, Any]:
    api_key = get_weather_api_key()
    if not api_key:
        return {
            "status": "error",
            "message": "No valid API key found. Set OPENWEATHER_API_KEY in the project .env or environment before requesting forecast data.",
        }

    resolved = _resolve_coordinates(city, state, pincode)
    if resolved is None:
        return {
            "status": "error",
            "message": "Unable to resolve the requested location. Please provide a valid Indian city, state, or pincode.",
        }

    params = {
        "lat": resolved["lat"],
        "lon": resolved["lon"],
        "units": "metric",
        "cnt": max(days * 8, 8),
        "appid": api_key,
    }
    try:
        response = requests.get(f"{WEATHER_DATA_URL}/forecast", params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        forecast = []
        for item in payload.get("list", [])[: max(days * 8, 8)]:
            forecast.append(
                {
                    "timestamp": item.get("dt_txt", "n/a"),
                    "temperature_c": round(float(item.get("main", {}).get("temp", 0))),
                    "condition": item.get("weather", [{}])[0].get("description", "Clear").title(),
                    "rain_probability": round(float(item.get("pop", 0) * 100)),
                    "source": "openweather",
                }
            )
        return {
            "status": "success",
            "city": resolved["city"],
            "state": resolved["state"],
            "forecast": forecast[: max(days * 2, 2)],
            "source": "openweather",
        }
    except (requests.RequestException, ValueError, TypeError):
        return {
            "status": "error",
            "message": "Forecast API request failed. Please try again later or verify the API key is valid.",
        }


def check_rain_today_evening(city: str, state: str | None = None, pincode: str | None = None) -> dict[str, Any]:
    api_key = get_weather_api_key()
    if not api_key:
        return {
            "status": "error",
            "message": "No valid API key found. Set OPENWEATHER_API_KEY in the project .env or environment before checking rain probability.",
        }

    forecast_response = get_weather_forecast(city, state, pincode, days=1)
    if forecast_response.get("status") != "success":
        return forecast_response

    forecast = forecast_response.get("forecast", [])
    evening_slots = []
    for item in forecast:
        ts = str(item.get("timestamp", ""))
        if "15:00" in ts or "18:00" in ts or "21:00" in ts:
            evening_slots.append(item)

    if not evening_slots:
        evening_slots = forecast[:2]

    rain_probability = max(float(item.get("rain_probability", 0)) for item in evening_slots)
    will_rain = rain_probability >= 40
    summary = "Rain is likely this evening." if will_rain else "Rain is unlikely this evening."

    return {
        "status": "success",
        "location": f"{city.title()}" + (f", {state.title()}" if state else "") + (f" ({pincode})" if pincode else ""),
        "rain_probability": round(rain_probability, 1),
        "will_rain": will_rain,
        "summary": summary,
        "evening_forecast": evening_slots,
    }
