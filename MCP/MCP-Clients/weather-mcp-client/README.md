# Weather MCP Client

A CLI for querying current weather, short-range forecasts, and evening rain likelihood in India. The client starts the MCP server over stdio and prints the tool response as JSON. No LLM is required.

## Prerequisites

- Python and the project virtual environment at `.venv`
- An OpenWeatherMap API key
- The project dependencies installed in `.venv`

## Configure the API key

Add this to the `.env` file in the repository root:

```dotenv
OPENWEATHER_API_KEY=your_openweathermap_api_key
```

This must be an OpenWeatherMap key, not an OpenAI key. Keep `.env` private and do not commit it.

## Start the client

Open PowerShell in the repository root and run:

```powershell
.\.venv\Scripts\python.exe "MCP\MCP-Clients\weather-mcp-client\client.py"
```

The client launches the stdio MCP server for you. Do not start the server in a separate terminal for normal use. Type `exit` or `quit` to stop the client.

## Example prompts

```text
What is the weather in Pune, Maharashtra?
Will it rain today evening in Bengaluru, Karnataka?
Show forecast for 560001
```

The client routes current-weather, forecast, and evening-rain prompts to the corresponding MCP tools. Locations can be provided by city, optional state, or six-digit Indian pincode.