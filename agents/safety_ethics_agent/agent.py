# agents/safety_ethics_agent/agent.py

from __future__ import annotations

import os
from dotenv import load_dotenv, find_dotenv

from google.adk.agents import LlmAgent

from schemas import (
    SCHEMA_VERSION,
    ListenerOutput,
    SafetyDecisionV2,
    TherapyPlan,
    ResourceResults,
)

_ = load_dotenv(find_dotenv())

DEFAULT_MODEL = os.environ.get("OMHC_MODEL_NAME", "gemini-2.0-flash")

from agents.utils import load_instruction

safety_ethics_agent = LlmAgent(
    name="safety_ethics_agent",
    description=(
        "Performs conservative safety and policy checks. Uses Listener output "
        "and current turn to decide whether self-help is allowed, whether "
        "escalation to human support is needed, and whether replies should be "
        "blocked. Writes SafetyDecision JSON to session.state['safety_decision']."
    ),
    model=DEFAULT_MODEL,
    instruction=load_instruction("safety_instruction.md"),
    output_schema=SafetyDecisionV2,
    output_key="safety_decision_v2",
    include_contents="default",
)