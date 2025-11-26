# a2a_client/agent.py

import os
from dotenv import load_dotenv, find_dotenv

from google.adk.agents.remote_a2a_agent import (
    RemoteA2aAgent,
    AGENT_CARD_WELL_KNOWN_PATH,
)

"""
A sample A2A-consuming agent that calls the OMHC orchestrator
exposed via A2A.

Usage (after starting the OMHC A2A server):

  export OMHC_A2A_BASE_URL=http://127.0.0.1:8001
  uv run adk web --agent-module a2a_client.agent

Then interact with this client root agent via the ADK web UI.
"""

_ = load_dotenv(find_dotenv())

# Base URL for the OMHC A2A server; must match how you run `omhc_a2a_server.py`.
#
# Example:
#   OMHC_A2A_SERVER_HOST=127.0.0.1
#   OMHC_A2A_SERVER_PORT=8001
#   -> OMHC_A2A_BASE_URL=http://127.0.0.1:8001
#
OMHC_A2A_BASE_URL = os.getenv("OMHC_A2A_BASE_URL", "http://127.0.0.1:8001")
# The to_a2a(...) helper exposes the agent under:
#   /a2a/<agent_name>/.well-known/agent.json
#
omc_agent_card_url = (
    f"{OMHC_A2A_BASE_URL}/a2a/open_mhc_orchestrator{AGENT_CARD_WELL_KNOWN_PATH}"
)

root_agent = RemoteA2aAgent(
    name="omc_a2a_client",
    description=(
        "Client agent that delegates mental health support turns to the "
        "remote Open Mental Health Collective (OMHC) orchestrator via A2A."
    ),
    agent_card=omc_agent_card_url,
)

