import os
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)

OPENWEATHER_API_KEY_ENV = "OPENWEATHER_API_KEY"
WEATHER_GEO_URL = "https://api.openweathermap.org/geo/1.0"
WEATHER_DATA_URL = "https://api.openweathermap.org/data/2.5"


def get_weather_api_key() -> str:
    return os.getenv(OPENWEATHER_API_KEY_ENV, "").strip()
