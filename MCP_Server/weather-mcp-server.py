from mcp import FastMCP

# Initialize the MCP server
mcp = FastMCP()

# Define the weather tool function
@mcp.tool
def city_weather(city: str) -> dict:
    """
    Get the weather information for a specific city.
    
    Args:
        city: The name of the city to get weather for
    
    Returns:
        A dictionary containing weather information
    """
    # In a real implementation, this would call a weather API
    # This is a simplified example with hardcoded responses
    weather_data = {
        "New York": {"temperature": 72, "condition": "Sunny", "humidity": 45},
        "London": {"temperature": 65, "condition": "Rainy", "humidity": 80},
        "Tokyo": {"temperature": 85, "condition": "Clear", "humidity": 60}
    }
    
    if city in weather_data:
        return weather_data[city]
    else:
        return {"error": f"Weather data not available for {city}"}

# Define a resource for available cities
@mcp.resource
def available_cities() -> list:
    """List cities for which weather data is available"""
    return ["New York", "London", "Tokyo"]

# Add a prompt template to help models use the weather tool
@mcp.prompt
def weather_query_template() -> str:
    return """
    To get weather information, you should:
    1. Check available cities using the available_cities resource
    2. Call the city_weather tool with a valid city name
    3. Format your response to include temperature, condition, and humidity
    """

# For HTTP/SSE transport (optional)
if __name__ == "__main__":
    import asyncio
    from mcp.server import serve_http
    
    async def main():
        await serve_http(mcp, host="localhost", port=8000)
    
    asyncio.run(main())