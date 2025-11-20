from __future__ import annotations

from enum import Enum
from typing import AsyncGenerator, List, Optional

from typing_extensions import override
from pydantic import BaseModel, Field

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools import google_search  # built-in Google Search tool

from .schemas.shared import (
    SCHEMA_VERSION,
    ListenerOutput,
    SafetyDecisionV2,
    TherapyPlan,
    ResourceResults,
)

class DebugStateAgent(BaseAgent):
    """
    Tiny debug agent that dumps selected session.state fields.
    Intended for developers (ADK web/CLI), not end users.
    """

    async def _run_async_impl(self, ctx: CallbackContext):
        state = ctx.session.state
        text = format_debug_state(state)
        yield make_text_event(author=self.name, text=text)


debug_state_agent = DebugStateAgent(name="debug_state_agent")