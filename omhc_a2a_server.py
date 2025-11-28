# omhc_a2a_server.py

import os

import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from agents import root_agent

"""
Expose the OMHC orchestrator as an Agent2Agent (A2A) endpoint.

This lets external agent systems discover and call the OMHC agent
using the A2A protocol, without needing to know anything about ADK
internals.
"""

# Server-side host/port for uvicorn
A2A_SERVER_HOST = os.getenv("OMC_A2A_SERVER_HOST", "0.0.0.0")
A2A_SERVER_PORT = int(os.getenv("OMC_A2A_SERVER_PORT", "8001"))

from starlette.applications import Starlette
from starlette.routing import Mount

import asyncio
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

# Wrap the ADK root agent as an A2A-compatible FastAPI app.
# to_a2a returns an app serving at root. We mount it under /a2a/{agent_name}
# to match the client expectation.
# We must also manually build the AgentCard with the correct URL because to_a2a
# assumes root mounting by default.
builder = AgentCardBuilder(
    agent=root_agent,
    rpc_url=f"http://{A2A_SERVER_HOST}:{A2A_SERVER_PORT}/a2a/{root_agent.name}/"
)
# Build the card synchronously before starting the app
card = asyncio.run(builder.build())
# Force trailing slash on the card URL to avoid 307 Redirects
# (AgentCardBuilder strips it by default)
card.url = f"http://{A2A_SERVER_HOST}:{A2A_SERVER_PORT}/a2a/{root_agent.name}/"

_agent_app = to_a2a(root_agent, port=A2A_SERVER_PORT, agent_card=card)
a2a_app = Starlette(routes=[
    Mount(f"/a2a/{root_agent.name}", app=_agent_app)
])

# Propagate startup events from the inner app to the outer app
# This is necessary if Starlette/Uvicorn doesn't automatically trigger mounted app startup
if hasattr(_agent_app, "router") and hasattr(_agent_app.router, "on_startup"):
    for handler in _agent_app.router.on_startup:
        a2a_app.add_event_handler("startup", handler)

# Initialize MCP tools on startup (lazy initialization to avoid pickle errors)
from agents.resource_connector_agent.agent import resource_connector_agent, configure_mcp_tools

async def startup_mcp():
    await configure_mcp_tools(resource_connector_agent)

a2a_app.add_event_handler("startup", startup_mcp)


def main():
    uvicorn.run(a2a_app, host=A2A_SERVER_HOST, port=A2A_SERVER_PORT)


if __name__ == "__main__":
    main()
