# Weather MCP Server Technical Explanation

## Goal

The weather MCP server adds an external capability layer to a client application. Instead of embedding weather logic directly in the client, the server exposes structured tools that can be called from a CLI or any MCP-compatible agent.

## Architecture

The server follows a simple MCP pattern:

1. The server defines tools using `FastMCP`.
2. Each tool accepts a small, constrained set of arguments.
3. The client connects to the server through the MCP stdio transport.
4. The client calls a tool such as `check_rain_today_evening` and receives structured JSON-like results.

## Tool design

### get_current_weather

- Accepts `city` and optional `state`
- Resolves the location using OpenWeatherMap geocoding when an API key is present
- Returns temperature, humidity, condition, and wind speed
- Falls back to demo values when the API key is missing

### get_weather_forecast

- Returns forecast entries with timestamp, temperature, condition, and rain probability
- Keeps the function focused on short-term updates for the same city

### check_rain_today_evening

- Pulls the nearest evening forecast slots
- Compares the rain probability against a threshold
- Returns a clear summary like "Rain is likely this evening."

## Integration flow

A CLI client starts the server process in stdio mode and opens an MCP session. The session then calls one of the server tools. The server responds with structured payloads that can be printed or routed into a chat workflow.

## Why no LLM is required here

This app is a pure tool-calling system. The user asks a weather question, the client identifies the intent and calls the correct weather tool, and the server returns the data. An LLM is useful only if the client or orchestrator needs to interpret free-form natural language at a higher layer.

## Operational notes

- Use a real OpenWeatherMap key for production weather accuracy.
- Without an API key, the app still works in demo mode.
- The design is intentionally simple for learning and extension.
