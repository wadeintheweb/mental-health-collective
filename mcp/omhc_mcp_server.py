# mcp/omhc_mcp_server.py

from typing import List, Dict
from mcp.server.fastmcp import FastMCP

# Initialize MCP server with a descriptive name
mcp = FastMCP("omc-mental-health-resources")


@mcp.tool()
def list_crisis_hotlines(country_code: str) -> List[Dict[str, str]]:
    """
    Return a small list of general crisis hotline resources for the given
    ISO country code (e.g., 'US', 'CA').

    This is a MOCK / DEMO implementation. You MUST validate and expand this
    list for real deployments, and ideally drive it from a maintained data
    source or vetted API.

    The returned objects are intentionally simple so they can be mapped
    easily into the ResourceResults schema in the OMHC Resource Connector.
    """
    code = country_code.upper().strip()
    hotlines: List[Dict[str, str]] = []

    # Very small illustrative sample; extend with real data before production.
    if code in ("US", "USA"):
        hotlines.append(
            {
                "name": "988 Suicide & Crisis Lifeline (United States)",
                "region_hint": "United States",
                "url": "https://988lifeline.org",
                "description": (
                    "Call or text 988, or use chat via website, to reach trained "
                    "crisis counselors 24/7."
                ),
            }
        )
    if code in ("CA", "CAN"):
        hotlines.append(
            {
                "name": "Talk Suicide Canada",
                "region_hint": "Canada",
                "url": "https://talksuicide.ca",
                "description": (
                    "Call or text 988 or use online chat to reach support for "
                    "people in Canada thinking about suicide."
                ),
            }
        )

    # Fallback / generic suggestions
    if not hotlines:
        hotlines.append(
            {
                "name": "Local emergency number",
                "region_hint": code,
                "url": "",
                "description": (
                    "If you are in immediate danger, call your local emergency "
                    "number (for example 911 in North America or 112 in many "
                    "European countries)."
                ),
            }
        )

    return hotlines


if __name__ == "__main__":
    # Run the MCP server. With FastMCP, you'll typically run via CLI:
    #   fastmcp run mcp/omhc_mcp_server.py --host 0.0.0.0 --port 8002 --transport sse
    #
    # This bare call is often enough for local stdio-based testing; see MCP
    # docs for transport details.
    mcp.run()
