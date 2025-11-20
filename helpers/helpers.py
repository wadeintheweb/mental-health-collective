# open_mhc_app/agent.py

import os
import json
from typing import List, Optional

from pydantic import ValidationError
from google.genai import types as genai_types
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.context import CallbackContext
from google.adk.events import Event

from .schemas import (
    SCHEMA_VERSION,
    ListenerOutput,
    SafetyDecisionV2,
    TherapyPlan,
    ResourceResults,
)


DEFAULT_MODEL = os.environ.get("OMC_MODEL_NAME", "gemini-2.0-flash")


def load_listener_output(state: dict) -> Optional[ListenerOutput]:
    raw = state.get("listener_output")
    if not raw:
        return None
    try:
        return ListenerOutput.model_validate_json(raw)
    except ValidationError:
        return None


def load_safety_decision(state: dict) -> Optional[SafetyDecisionV2]:
    raw = state.get("safety_decision_v2")
    if not raw:
        return None
    try:
        return SafetyDecisionV2.model_validate_json(raw)
    except ValidationError:
        return None


def load_therapy_plan(state: dict) -> Optional[TherapyPlan]:
    raw = state.get("therapy_plan")
    if not raw:
        return None
    try:
        return TherapyPlan.model_validate_json(raw)
    except ValidationError:
        return None


def load_resource_results(state: dict) -> Optional[ResourceResults]:
    raw = state.get("resource_results")
    if not raw:
        return None
    try:
        return ResourceResults.model_validate_json(raw)
    except ValidationError:
        return None


def safety_ceiling_blocks(state: dict) -> bool:
    sd = load_safety_decision(state)
    return bool(sd and sd.block_reply)


def assemble_final_response(state: dict) -> Optional[str]:
    listener = load_listener_output(state)
    safety = load_safety_decision(state)
    plan = load_therapy_plan(state)
    resources = load_resource_results(state)

    if safety and safety.block_reply and safety.user_message_override:
        return safety.user_message_override.strip()

    if plan is None and resources is None:
        return None

    parts: List[str] = []

    if listener:
        parts.append(
            "Thank you for sharing what you’re going through. "
            f"From what I understand, {listener.normalized_utterance.strip()}"
        )

    if plan and (not safety or safety.allow_self_help):
        therapy_block_parts: List[str] = [plan.coach_message.strip()]
        if plan.steps:
            step_lines = []
            for idx, step in enumerate(plan.steps, start=1):
                step_lines.append(f"{idx}) {step.label}: {step.description}")
            therapy_block_parts.append("\n".join(step_lines))
        if plan.safety_notes:
            therapy_block_parts.append(plan.safety_notes.strip())
        parts.append("\n\n".join(therapy_block_parts))

    if resources:
        res_block_parts: List[str] = [resources.user_facing_summary.strip()]
        if resources.resources:
            res_lines = []
            for item in resources.resources:
                line = f"- {item.name}"
                if item.region_hint:
                    line += f" ({item.region_hint})"
                if item.url:
                    line += f" – {item.url}"
                if item.description:
                    line += f": {item.description}"
                res_lines.append(line)
            res_block_parts.append("\n".join(res_lines))
        if resources.safety_notes:
            res_block_parts.append(resources.safety_notes.strip())
        parts.append("\n\n".join(res_block_parts))

    parts.append(
        "This is general, self-help–oriented information from an AI system, "
        "not a diagnosis or a substitute for professional or emergency care. "
        "If you ever feel like you might hurt yourself or someone else, or "
        "you’re in immediate danger, please contact local emergency services "
        "or a crisis hotline right away."
    )

    final = "\n\n".join(p for p in parts if p.strip())
    return final if final.strip() else None


def make_text_event(author: str, text: str) -> Event:
    content = genai_types.Content(
        role="model",
        parts=[genai_types.Part(text=text)],
    )
    return Event(author=author, content=content)


def format_debug_state(state: dict) -> str:
    listener = load_listener_output(state)
    safety = load_safety_decision(state)

    payload = {
        "schema_version": state.get("schema_version"),
        "listener_output": (
            json.loads(listener.model_dump_json()) if listener else None
        ),
        "safety_decision_v2": (
            json.loads(safety.model_dump_json()) if safety else None
        ),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
