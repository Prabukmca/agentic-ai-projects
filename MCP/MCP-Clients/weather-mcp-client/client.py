import asyncio
import json
import os
import re
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER_PATH = Path(__file__).resolve().parents[2] / "MCP_Servers" / "weather-mcp-server" / "server.py"
VENV_PYTHON = Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "python.exe"


def parse_location_input(text: str) -> dict:
    cleaned = (text or "").strip()
    if not cleaned:
        return {"city": None, "state": None, "pincode": None}

    match = re.search(r"\b(\d{6})\b", cleaned)
    pincode = match.group(1) if match else None
    if pincode:
        cleaned = cleaned.replace(match.group(1), "").strip()

    if " in " in cleaned.lower():
        cleaned = cleaned.split(" in ", 1)[1].strip()

    cleaned = re.sub(
        r"^(what is the|show|tell me|check|will it rain|forecast|current weather|weather)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = cleaned.strip(" ,.;?!")

    if "," in cleaned:
        city, state = cleaned.split(",", 1)
        city = city.strip()
        state = state.strip() or None
    else:
        parts = cleaned.split()
        if len(parts) >= 2:
            city = parts[0].strip()
            state = " ".join(parts[1:]).strip() or None
        else:
            city = cleaned.strip() or None
            state = None

    if city and city.lower() in {"today", "evening", "forecast"}:
        city = None

    return {"city": city or None, "state": state or None, "pincode": pincode}


def _normalize_tool_result(result):
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "content"):
        content = []
        for item in result.content:
            if hasattr(item, "model_dump"):
                content.append(item.model_dump())
            else:
                content.append(item)
        return content
    if isinstance(result, dict):
        return result
    return str(result)


async def list_tools(session):
    response = await session.list_tools()
    return [tool.name for tool in response.tools]


async def call_weather_tool(session, tool_name: str, **kwargs):
    result = await session.call_tool(tool_name, kwargs)
    return _normalize_tool_result(result)


async def interactive_cli():
    server_params = StdioServerParameters(
        command=str(VENV_PYTHON),
        args=[str(SERVER_PATH)],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await list_tools(session)
            print("Connected to weather MCP server.")
            print(f"Available tools: {tools}")
            print("Type 'exit' to quit.")

            while True:
                user_input = input("\nWeather prompt> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"exit", "quit"}:
                    print("Goodbye.")
                    break

                location = parse_location_input(user_input)
                city = location.get("city")
                state = location.get("state")
                pincode = location.get("pincode")

                if not city and not pincode:
                    print(json.dumps({"status": "error", "message": "Please provide a valid city, state, or pincode."}, ensure_ascii=False))
                    continue

                if "rain" in user_input.lower() and "evening" in user_input.lower():
                    response = await call_weather_tool(session, "check_rain_today_evening", city=city, state=state, pincode=pincode)
                    print(json.dumps(response, indent=2, ensure_ascii=False))
                    continue

                if "forecast" in user_input.lower() or "tomorrow" in user_input.lower():
                    response = await call_weather_tool(session, "get_weather_forecast", city=city, state=state, pincode=pincode, days=3)
                    print(json.dumps(response, indent=2, ensure_ascii=False))
                    continue

                response = await call_weather_tool(session, "get_current_weather", city=city, state=state, pincode=pincode)
                print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(interactive_cli())
