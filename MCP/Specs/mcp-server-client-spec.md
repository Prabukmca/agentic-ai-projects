## Requirement

-- Need to build a MCP server and client for weather forecast, it should check current weather condition, and forecast.
-- If user ask, will rain today evening, the server able to collect the data.
-- I would like to focus the indian region, if any region is possible, should user mention the main city name? or pin code?
-- Add files in these paths - MCP\MCP_Servers and - MCP\MCP_clients creating folder called weather-mcp-server, weather-mcp-client.
-- Integrate the server with client.
-- the client should be cli? or could be Streamlit UI?
-- If it is UI, will it become RAG?
-- for now, I would like to go with CLI client.
-- Create ReadMe.md, feed with the details, what this mcp server and client do, how to start this mcp server and client.
-- Create one more md for tech explanation, what we done in the server and client, how integrated, details should be their.
-- Do we need LLM?


-- Changes required.

Remove demo weather, I'm having valid api key,
Can we add, optional pincode as well along with city and state?
In this workspace in .env, I have valid key, use properly in the logic.
If key is not available in the logic, instead return none, return no valid api key found message.
-- I have doubt, OPENWEATHER_API_KEY means open AI api key? or this is different key I supposed to buy?
-- If it is different key I need to buy means, do we have any other opensource free api available to explore?
-- if not open source api is not available do not remove the demo data.
-- In mcp client, why did you hardcoded 'pune'?
-- If we use valid weather forecast api URL? then keep the URL in constant file, like real time project.
-- follow all the patterns and priciples, rules, regulations, folder structure excatly like real time project.
-- do not consider this is POC, testing app.

