# Debug State Test

import json
import pytest
from google.adk.context import CallbackContext
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from open_mhc_app.agent import (
    root_agent,
    debug_state_agent,
    SCHEMA_VERSION,
)


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

    ctx = CallbackContext(session=session, app_name=runner.app_name)
    debug_events = [e async for e in debug_state_agent.run_async(ctx)]

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

    assert snapshot.get("schema_version") == SCHEMA_VERSION

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
