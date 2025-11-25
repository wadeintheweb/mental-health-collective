# agents/debug_state_agent/agent.py

import json
from typing import Optional

from pydantic import ValidationError
from dotenv import load_dotenv, find_dotenv

from google.genai import types as genai_types
from google.adk.agents import BaseAgent
from google.adk.context import CallbackContext
from google.adk.events import Event

from schemas import ListenerOutput, SafetyDecisionV2, SCHEMA_VERSION

_ = load_dotenv(find_dotenv())

def _load_listener_output(state: dict) -> Optional[ListenerOutput]:
    raw = state.get("listener_output")
    if not raw:
        return None
    try:
        return ListenerOutput.model_validate_json(raw)
    except ValidationError:
        return None


def _load_safety_decision(state: dict) -> Optional[SafetyDecisionV2]:
    raw = state.get("safety_decision_v2")
    if not raw:
        return None
    try:
        return SafetyDecisionV2.model_validate_json(raw)
    except ValidationError:
        return None


def _format_debug_state(state: dict) -> str:
    listener = _load_listener_output(state)
    safety = _load_safety_decision(state)

    payload = {
        "schema_version": state.get("schema_version"),
        "expected_schema_version": SCHEMA_VERSION,
        "listener_output": (
            json.loads(listener.model_dump_json()) if listener else None
        ),
        "safety_decision_v2": (
            json.loads(safety.model_dump_json()) if safety else None
        ),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _make_text_event(author: str, text: str) -> Event:
    content = genai_types.Content(
        role="model",
        parts=[genai_types.Part(text=text)],
    )
    return Event(author=author, content=content)


class DebugStateAgent(BaseAgent):
    """
    Tiny debug agent that dumps selected session.state fields.

    Intended for developers using ADK web or CLI, NOT for end users.
    """

    async def _run_async_impl(self, ctx: CallbackContext):
        state = ctx.session.state
        text = _format_debug_state(state)
        yield _make_text_event(author=self.name, text=text)


debug_state_agent = DebugStateAgent(name="debug_state_agent")
