# agents/orchestrator_agent/agent.py

from typing import List, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

from google.genai import types as genai_types
from google.adk.agents import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event

from schemas import (
    SCHEMA_VERSION,
    ListenerOutput,
    SafetyDecisionV2,
    TherapyPlan,
    ResourceResults,
)

from agents.utils import load_instruction

from agents.listener_agent.agent import listener_agent
from agents.safety_ethics_agent.agent import safety_ethics_agent
from agents.therapy_coach_agent.agent import therapy_coach_agent
from agents.resource_connector_agent.agent import resource_connector_agent

# -----------------------------------------------------------------------------
# Generic loader helper (fixes the bug)
# -----------------------------------------------------------------------------

T = TypeVar("T", bound=BaseModel)


def _coerce_model(raw: object, model_cls: Type[T]) -> Optional[T]:
    """
    Robustly convert a value from session.state into a Pydantic model.

    Handles:
      - already-a-model
      - dict
      - JSON string

    Returns None on any validation error.
    """
    if raw is None:
        return None

    # Already a model instance
    if isinstance(raw, model_cls):
        return raw

    # Dict -> validate as object
    if isinstance(raw, dict):
        try:
            return model_cls.model_validate(raw)
        except ValidationError:
            return None

    # JSON string
    if isinstance(raw, str):
        try:
            return model_cls.model_validate_json(raw)
        except ValidationError:
            return None

    # Anything else: give up
    return None


# -----------------------------------------------------------------------------
# Typed loaders using the helper
# -----------------------------------------------------------------------------


def _load_listener_output(state: dict) -> Optional[ListenerOutput]:
    return _coerce_model(state.get("listener_output"), ListenerOutput)


def _load_safety_decision(state: dict) -> Optional[SafetyDecisionV2]:
    return _coerce_model(state.get("safety_decision_v2"), SafetyDecisionV2)


def _load_therapy_plan(state: dict) -> Optional[TherapyPlan]:
    return _coerce_model(state.get("therapy_plan"), TherapyPlan)


def _load_resource_results(state: dict) -> Optional[ResourceResults]:
    return _coerce_model(state.get("resource_results"), ResourceResults)


# -----------------------------------------------------------------------------
# Final response assembly
# -----------------------------------------------------------------------------


def _assemble_final_response(state: dict) -> Optional[str]:
    """
    Assemble a single user-facing response from the current state.

    Priority:
    1) If safety.block_reply and user_message_override is set, return that.
    2) Otherwise, combine:
       - Reflection from Listener
       - TherapyPlan (if present and allowed)
       - Resources (if present)
       - A fixed safety disclaimer.
    """
    listener = _load_listener_output(state)
    safety = _load_safety_decision(state)
    plan = _load_therapy_plan(state)
    resources = _load_resource_results(state)

    # Safety override first
    if safety and safety.block_reply and safety.user_message_override:
        return safety.user_message_override.strip()

    # If nothing to assemble, bail
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


def _make_text_event(author: str, text: str) -> Event:
    content = genai_types.Content(
        role="model",
        parts=[genai_types.Part(text=text)],
    )
    return Event(author=author, content=content)


# -----------------------------------------------------------------------------
# Orchestrator agent
# -----------------------------------------------------------------------------


class MentalHealthOrchestrator(BaseAgent):
    """
    Root orchestrator for the Open Mental Health Collective system.

    Implements routing, state updates, and safety ceiling behavior.
    """

    model_config = {"arbitrary_types_allowed": True}

    listener_agent: BaseAgent = listener_agent
    safety_agent: BaseAgent = safety_ethics_agent
    therapy_coach_agent: BaseAgent = therapy_coach_agent
    resource_connector_agent: BaseAgent = resource_connector_agent
    instruction: str = ""


    async def _run_async_impl(self, ctx: CallbackContext):
        state = ctx.session.state

        # Ensure schema version
        if state.get("schema_version") != SCHEMA_VERSION:
            state["schema_version"] = SCHEMA_VERSION

        # 1) Listener always first
        async for event in self.listener_agent.run_async(ctx):
            # Listener's short empathic reply may go to the user
            yield event

        state = ctx.session.state
        listener = _load_listener_output(state)
        if not listener:
            # Fallback if listener_output is missing or invalid
            text = (
                "I’m having trouble understanding the details of what you shared, "
                "but I’m glad you reached out. This system cannot provide emergency "
                "help. If you are in immediate danger or think you might hurt "
                "yourself or someone else, please contact local emergency "
                "services or a crisis hotline right away."
            )
            yield _make_text_event(author=self.name, text=text)
            return

        must_run_safety = listener.risk.risk_level != "none" or (
            listener.user_intent == "crisis_support"
        )

        safety = None
        if must_run_safety:
            async for event in self.safety_agent.run_async(ctx):
                # Safety should only emit JSON, but we yield events for observability
                yield event

            state = ctx.session.state
            safety = _load_safety_decision(state)
            if not safety:
                text = (
                    "Something went wrong while checking safety. "
                    "To be cautious, I can’t provide self-help exercises right now. "
                    "If you are struggling, please consider reaching out to a "
                    "trusted person or a local health professional. "
                    "If you are in immediate danger, contact emergency services "
                    "or a crisis hotline right away."
                )
                yield _make_text_event(author=self.name, text=text)
                return

            # Safety ceiling: block all further content if block_reply is true
            if safety.block_reply:
                assembled = _assemble_final_response(state)
                if not assembled:
                    assembled = (
                        "Based on what you’ve shared, it’s really important to reach "
                        "out to real-world support right now. This system cannot "
                        "safely continue with self-help in this moment. "
                        "If you are in immediate danger or feel like you might hurt "
                        "yourself or someone else, please contact local emergency "
                        "services or a crisis hotline immediately."
                    )
                yield _make_text_event(author=self.name, text=assembled)
                return

        intent = listener.user_intent

        # Unknown intent -> clarify only (Listener's text is already sent)
        if intent == "unknown":
            return

        # Resource path (resource_navigation or crisis_support)
        if intent in ("resource_navigation", "crisis_support"):
            async for event in self.resource_connector_agent.run_async(ctx):
                yield event

            state = ctx.session.state
            assembled = _assemble_final_response(state)
            if assembled:
                yield _make_text_event(author=self.name, text=assembled)
            return

        # Therapy path (check_in, psychoeducation, skills_practice)
        if intent in ("check_in", "psychoeducation", "skills_practice"):
            allow_self_help = True
            if must_run_safety:
                safety = _load_safety_decision(ctx.session.state)
                allow_self_help = bool(
                    safety and safety.allow_self_help and not safety.block_reply
                )

            if allow_self_help:
                async for event in self.therapy_coach_agent.run_async(ctx):
                    yield event

            state = ctx.session.state
            assembled = _assemble_final_response(state)
            if assembled:
                yield _make_text_event(author=self.name, text=assembled)
            return

        # Fallback: unknown intent type (should not occur if schema is respected)
        return
        



root_agent = MentalHealthOrchestrator(
    name="open_mhc_orchestrator",
    instruction=load_instruction("orchestrator_instruction.md"),
)
