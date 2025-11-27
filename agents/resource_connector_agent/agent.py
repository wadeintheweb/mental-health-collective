# agents/resource_connector_agent/agent.py

import os
from dotenv import load_dotenv, find_dotenv
from typing import List

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools.base_tool import BaseTool

# MCP integration (optional, guarded so code still runs if not configured)
try:
    from google.adk.tools.mcp_tool import MCPToolset, SseConnectionParams  # type: ignore[import]
except ImportError:  # Older ADK without MCP support
    MCPToolset = None  # type: ignore[assignment]
    SseConnectionParams = None  # type: ignore[assignment]

from schemas import ResourceResults

_ = load_dotenv(find_dotenv())

DEFAULT_MODEL = os.environ.get("OMHC_MODEL_NAME", "gemini-2.0-flash")

# ---------------------------------------------------------------------------
# Agent instruction
# ---------------------------------------------------------------------------

from agents.utils import load_instruction

# ---------------------------------------------------------------------------
# Tool wiring: Google Search + optional MCP toolset
# ---------------------------------------------------------------------------


def _build_resource_tools() -> List[BaseTool]:
    """
    Build the list of tools for the Resource Connector Agent.

    - Always includes the built-in `google_search` tool.
    - Optionally adds tools from an MCPToolset if `MENTAL_HEALTH_MCP_URL`
      is set and MCP support is available in this ADK install.
    """
    tools: List[BaseTool] = []

    # 1) Built-in Google Search (always available)
    tools.append(google_search)

    # 2) Optional MCP Toolset: connect to a mental health resource MCP server
    mcp_url = os.getenv("MENTAL_HEALTH_MCP_URL")
    if mcp_url and MCPToolset is not None and SseConnectionParams is not None:
        try:
            params = SseConnectionParams(url=mcp_url)
            mcp_toolset = MCPToolset.from_config(params)
            tools.extend(mcp_toolset.get_tools())
        except Exception as e:
            # Fail closed: if MCP setup is misconfigured, we still have google_search.
            # Log the error for debugging but continue with available tools.
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"MCP toolset initialization failed: {e}")
            pass

    return tools


RESOURCE_TOOLS: List[BaseTool] = _build_resource_tools()

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

resource_connector_agent = LlmAgent(
    name="resource_connector_agent",
    model=DEFAULT_MODEL,
    instruction=(
        "You are a helpful assistant that finds mental health resources. "
        "You MUST return the result as a raw JSON object with a 'user_facing_summary' string and a 'resources' list of objects. "
        "Each resource object must have 'name', 'url', 'region_hint', and 'description'. "
        "Do not use Markdown formatting (no ```json blocks). Just the raw JSON string."
    ),
    # output_schema=ResourceResults,  # Removed to avoid "Tool use with function calling is unsupported" error
    output_key="resource_results",
    include_contents="default",
    tools=RESOURCE_TOOLS,
)
