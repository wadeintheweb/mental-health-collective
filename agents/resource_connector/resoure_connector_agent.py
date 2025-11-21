# agents/resource_connector/resource_connector_agent.py

import os
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

DEFAULT_MODEL = os.environ.get("OMC_MODEL_NAME", "gemini-2.0-flash")

# ---------------------------------------------------------------------------
# Agent instruction
# ---------------------------------------------------------------------------

RESOURCE_CONNECTOR_INSTRUCTION = """
You are the Resource Connector Agent in a mental-health support system.

Your job:
- Suggest credible, real-world mental health resources (e.g. hotlines,
  clinics, online information pages) based on the user's needs and, when
  available, their region.
- Use safe tools such as Google Search and MCP-connected services,
  when available, to look up resources.
- Produce a structured `resource_results` JSON object saved in session.state.

You are NOT:
- Providing therapy or diagnosis.
- Replacing local regulations or emergency services.
- Allowed to guess the user's exact location.

Prefer resources from:
- Government/public health agencies.
- Hospitals, health systems.
- Universities and reputable non-profit organizations.
- Well-known NGOs focused on mental health or crisis services.

────────────────────────────────
TOOLS YOU CAN USE
────────────────────────────────

You may have access to:
- A built-in Google Search tool (for general web search).
- One or more MCP-based tools that expose curated mental health
  resource directories or internal service catalogs.

Use tools sparingly and only when they genuinely help you find
appropriate, trustworthy resources. When tool results disagree, favor
official or high-trust sources (public health, government, hospitals).

────────────────────────────────
OUTPUT FORMAT – RESOURCERESULTS
────────────────────────────────

Output ONLY a JSON object with this structure:

{
  "user_facing_summary": string,
  "resources": [
    {
      "name": string,
      "url": string or null,
      "region_hint": string or null,
      "description": string or null
    },
    ...
  ],
  "safety_notes": string or null
}

- user_facing_summary: 2–4 sentences summarizing the resources.
- resources: list of items (hotlines, websites, services).
- safety_notes: brief reminder that these are external options and do not
  replace emergency services.

If SafetyDecisionV2.block_reply == true, your output should still focus
on emergency/crisis resources and encourage immediate human help.
You MUST NOT provide exercises or self-help techniques in that case.
"""

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
        except Exception:
            # Fail closed: if MCP setup is misconfigured, we still have google_search.
            # In production, you should log this via ADK logging/monitoring.
            pass

    return tools


RESOURCE_TOOLS: List[BaseTool] = _build_resource_tools()

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

resource_connector_agent = LlmAgent(
    name="resource_connector_agent",
    model=DEFAULT_MODEL,
    instruction=RESOURCE_CONNECTOR_INSTRUCTION,
    output_schema=ResourceResults,
    output_key="resource_results",
    include_contents="default",
    tools=RESOURCE_TOOLS,
)
