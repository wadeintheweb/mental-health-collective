# Debug State Test

import json
import pytest
from google.adk.agents.callback_context import CallbackContext
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from agents.orchestrator_agent.agent import root_agent
from agents.debug_state_agent.agent import debug_state_agent
from schemas import SCHEMA_VERSION


@pytest.mark.asyncio
async def test_debug_state_agent_outputs_valid_snapshot():
    runner = InMemoryRunner(agent=root_agent, app_name="open_mhc_app")
    session_service = runner.session_service

    user_id = "test_debug_user"
    session = await session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
    )

    user_message = genai_types.Content(
        role="user",
        parts=[
            genai_types.Part(
                text=(
                    "I've been feeling pretty down and tired lately. "
                    "I don't want to hurt myself, but I feel stuck."
                )
            )
        ],
    )

    async for _event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=user_message,
    ):
        pass

    # Run debug agent using a fresh runner to handle context creation
    debug_runner = InMemoryRunner(agent=debug_state_agent, app_name="open_mhc_app")
    debug_runner.session_service = session_service
    # We need to share the session state. The session object is the same.
    # But runner.run_async takes user_id and session_id.
    # We can just run it.
    
    debug_events = []
    async for e in debug_runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        # No new message needed for debug agent, but run_async might require it or we can pass empty
        # Actually debug agent ignores input.
        new_message=genai_types.Content(role="user", parts=[genai_types.Part(text="debug")]),
    ):
        debug_events.append(e)

    assert debug_events, "DebugStateAgent produced no events"

    text_parts = []
    for ev in debug_events:
        if ev.content:
            for part in ev.content.parts:
                if getattr(part, "text", None):
                    text_parts.append(part.text)

    assert text_parts, "DebugStateAgent produced no text content"

    snapshot_text = "\n".join(text_parts)
    snapshot = json.loads(snapshot_text)

    assert "listener_output" in snapshot
    assert "safety_decision_v2" in snapshot

    listener_output = snapshot["listener_output"]
    safety_decision = snapshot["safety_decision_v2"]

    if listener_output is not None:
        assert isinstance(listener_output, dict)
        assert "risk" in listener_output
        assert "user_intent" in listener_output

    if safety_decision is not None:
        assert isinstance(safety_decision, dict)
        assert safety_decision.get("version") == "v2"
        assert "overall_risk_level" in safety_decision
        assert "allow_self_help" in safety_decision
        assert "block_reply" in safety_decision
