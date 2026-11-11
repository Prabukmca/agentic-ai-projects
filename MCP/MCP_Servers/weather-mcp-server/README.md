# Weather MCP Server

This server exposes live weather tools through the MCP protocol for India-focused weather queries.

## Features

- Current weather lookup by city, state, or pincode
- Short-term forecast lookup
- Evening rain probability check
- OpenWeatherMap integration using the configured API key
- Clear error handling when the API key is missing

## Environment setup

1. Create or activate the project virtual environment.
2. Add your OpenWeatherMap API key in the project root .env file or shell environment:

```bash
export OPENWEATHER_API_KEY="your_openweather_key_here"
```

PowerShell:

```powershell
$env:OPENWEATHER_API_KEY="your_openweather_key_here"
```

> Important: OPENWEATHER_API_KEY is not the same as OPENAI_API_KEY. It is a separate service key for OpenWeatherMap.

## Run the server

From the project root:

```bash
python MCP/MCP_Servers/weather-mcp-server/server.py
```

This starts the MCP server in stdio mode for the CLI client.

## Available tools

- get_current_weather(city, state=None, pincode=None)
- get_weather_forecast(city, state=None, pincode=None, days=3)
- check_rain_today_evening(city, state=None, pincode=None)

## Example usage

```python
from weather_service import get_current_weather, check_rain_today_evening

print(get_current_weather("Pune", "Maharashtra", "411001"))
print(check_rain_today_evening("Pune", "Maharashtra", "411001"))
```

## Notes

- This is a real tool server, not a demo-only app.
- If the API key is absent, the server returns a structured error message instead of silently falling back to mock data.
- A separate LLM layer is optional and not required for the core tool flow.
