# omc_a2a_server.py

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

# Wrap the ADK root agent as an A2A-compatible FastAPI app.
a2a_app = to_a2a(root_agent, port=A2A_SERVER_PORT)


def main():
    uvicorn.run(a2a_app, host=A2A_SERVER_HOST, port=A2A_SERVER_PORT)


if __name__ == "__main__":
    main()
