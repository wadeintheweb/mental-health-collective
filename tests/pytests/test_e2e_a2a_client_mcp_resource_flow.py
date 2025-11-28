# tests/test_e2e_a2a_client_mcp_resource_flow.py

import os
import shutil
import signal
import subprocess
import time

import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from a2a_client.client_agent import root_agent as a2a_client_root


APP_NAME = "omc_e2e_a2a_app"
USER_ID = "omc_e2e_a2a_user"

MCP_PORT = int(os.getenv("OMC_MCP_PORT", "8202"))
MCP_URL = f"http://127.0.0.1:{MCP_PORT}/sse"

A2A_PORT = int(os.getenv("OMC_A2A_SERVER_PORT", "8101"))
A2A_BASE_URL = f"http://127.0.0.1:{A2A_PORT}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_a2a_client_resource_flow_via_mcp():
    """
    End-to-end integration test that exercises:

    - MCP-backed resource lookup via the Resource Connector Agent.
    - Agent2Agent path: a2a_client -> remote OMHC orchestrator.

    Steps:
      1. Start MCP mental-health resource server via `fastmcp`.
      2. Start OMHC A2A server (`omhc_a2a_server.py`).
      3. Set MENTAL_HEALTH_MCP_URL + OMC_A2A_BASE_URL.
      4. Run the A2A client root agent with a crisis-resource prompt.
      5. Verify the final response includes an MCP-provided hotline
         ("Talk Suicide Canada").
    """

    # Skip cleanly if fastmcp CLI is not installed.
    if shutil.which("fastmcp") is None:
        pytest.skip("fastmcp CLI not found on PATH; skipping MCP E2E A2A test.")

    # 1) Start MCP server as subprocess
    mcp_cmd = [
        "fastmcp",
        "run",
        "mcp/omhc_mcp_server.py",
        "--host",
        "127.0.0.1",
        "--port",
        str(MCP_PORT),
        "--transport",
        "sse",
    ]
    mcp_proc = subprocess.Popen(
        mcp_cmd,
        text=True,
    )

    # 2) Start OMHC A2A server as subprocess
    a2a_env = os.environ.copy()
    a2a_env["OMC_A2A_SERVER_HOST"] = "127.0.0.1"
    a2a_env["OMC_A2A_SERVER_PORT"] = str(A2A_PORT)
    # Pass MCP URL to the A2A server so it can connect to the MCP server
    a2a_env["MENTAL_HEALTH_MCP_URL"] = MCP_URL

    import sys
    a2a_cmd = [sys.executable, "omhc_a2a_server.py"]
    a2a_proc = subprocess.Popen(
        a2a_cmd,
        text=True,
        env=a2a_env,
    )

    try:
        # Give MCP + A2A some time to start (increased to 10s for slower envs)
        time.sleep(10.0)

        # Check if processes are still running
        if mcp_proc.poll() is not None:
            pytest.fail(f"MCP server failed to start. RC={mcp_proc.returncode}")

        if a2a_proc.poll() is not None:
            pytest.fail(f"A2A server failed to start. RC={a2a_proc.returncode}")

        # 3) Point Resource Connector Agent + A2A client at these endpoints
        os.environ["MENTAL_HEALTH_MCP_URL"] = MCP_URL
        os.environ["OMHC_A2A_BASE_URL"] = A2A_BASE_URL

        # Reload client agent to pick up the new env var
        import importlib
        import a2a_client.client_agent
        importlib.reload(a2a_client.client_agent)
        from a2a_client.client_agent import root_agent as a2a_client_root

        # DEBUG: Verify connectivity from within test
        print(f"DEBUG: Curling {A2A_BASE_URL}/a2a/open_mhc_orchestrator/.well-known/agent-card.json")
        curl_res = subprocess.run(
            ["curl", "-v", f"{A2A_BASE_URL}/a2a/open_mhc_orchestrator/.well-known/agent-card.json"],
            capture_output=True,
            text=True
        )
        print(f"DEBUG: Curl RC={curl_res.returncode}")
        print(f"DEBUG: Curl stdout: {curl_res.stdout}")
        print(f"DEBUG: Curl stderr: {curl_res.stderr}")

        # 4) Set up ADK runner + session
        session_service = InMemorySessionService()
        runner = Runner(
            agent=a2a_client_root,
            app_name=APP_NAME,
            session_service=session_service
        )

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

        # Run the A2A client root agent; it will call OMHC orchestrator remotely.
        full_text = ""
        last_event = None
        try:
            async for event in runner.run_async(
                session_id=session.id, user_id=USER_ID, new_message=user_content
            ):
                print(f"DEBUG: Event: {event}")
                last_event = event
                parts = getattr(event.content, "parts", []) or []
                for p in parts:
                    if hasattr(p, "text") and p.text:
                        full_text += p.text
        except Exception as e:
            if "Tool use with function calling is unsupported" in str(e):
                pytest.skip(f"Skipping E2E A2A test due to environment tool support issue: {e}")
            raise e

        assert last_event is not None, "No events emitted by A2A client root agent."
        print(f"DEBUG: Full Text: {full_text}")

        # 5) Assert that the response includes our MCP-provided hotline
        assert "Talk Suicide Canada" in full_text

    finally:
        # Clean up MCP server
        if mcp_proc.poll() is None:
            mcp_proc.terminate()
            try:
                mcp_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                mcp_proc.kill()

        # Clean up A2A server
        if a2a_proc.poll() is None:
            a2a_proc.terminate()
            try:
                a2a_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                a2a_proc.kill()
