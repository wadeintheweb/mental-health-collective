# tests/test_e2e_mcp_resource_flow.py

import asyncio
import os
import shutil
import signal
import subprocess
import time

import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.orchestrator.orchestrator_agent import root_agent

APP_NAME = "omc_e2e_app"
USER_ID = "omc_e2e_user"
MCP_PORT = int(os.getenv("OMC_MCP_PORT", "8002"))
MCP_URL = f"http://127.0.0.1:{MCP_PORT}/sse"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_resource_flow_via_mcp_crisis_hotline():
    """
    End-to-end integration test that:

    1. Starts the MCP mental-health resource server via `fastmcp`.
    2. Sets MENTAL_HEALTH_MCP_URL so the Resource Connector Agent uses MCP tools.
    3. Runs the OMHC orchestrator root_agent with a crisis-resource prompt.
    4. Verifies that the final response includes a hotline name that our
       MCP server provides ("Talk Suicide Canada"), showing that the
       response flowed through MCP-backed resources.
    """

    # Skip cleanly if fastmcp CLI is not installed.
    if shutil.which("fastmcp") is None:
        pytest.skip("fastmcp CLI not found on PATH; skipping MCP E2E test.")

    # 1) Start MCP server as subprocess
    mcp_cmd = [
        "fastmcp",
        "run",
        "mcp/mhc_mcp_server.py",
        "--host",
        "127.0.0.1",
        "--port",
        str(MCP_PORT),
        "--transport",
        "sse",
    ]

    mcp_proc = subprocess.Popen(
        mcp_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Give MCP server a moment to start
        time.sleep(2.0)

        # 2) Point Resource Connector Agent at this MCP server
        os.environ["MENTAL_HEALTH_MCP_URL"] = MCP_URL

        # 3) Set up ADK runner + session
        session_service = InMemorySessionService()
        runner = Runner(session_service=session_service)

        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            state={},
        )

        user_content = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        "I live in Canada and I'm feeling really unsafe. "
                        "Can you give me suicide crisis hotlines I can call?"
                    )
                )
            ],
        )

        # 4) Run orchestrator; collect last model event
        last_event = None
        async for event in runner.run(agent=root_agent, session=session, content=user_content):
            last_event = event

        assert last_event is not None, "No events emitted by root_agent."

        # Extract final text from the last event's content
        parts = getattr(last_event.content, "parts", []) or []
        texts = [getattr(p, "text", "") for p in parts if hasattr(p, "text")]
        full_text = "\n".join(t for t in texts if t)

        # 5) Assert that the response includes our MCP-provided hotline
        #
        # The mhc_mcp_server.py stub returns "Talk Suicide Canada" for CA/CAN.
        # If that appears in the final assembled response, we know that:
        # - Resource Connector Agent ran
        # - It used the MCP-backed tool results in ResourceResults
        # - The Orchestrator assembled those into the final text
        #
        assert "Talk Suicide Canada" in full_text

    finally:
        # Clean up MCP server process
        if mcp_proc.poll() is None:
            # Try gentle terminate first
            mcp_proc.terminate()
            try:
                mcp_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                mcp_proc.kill()
