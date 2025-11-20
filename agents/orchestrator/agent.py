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

# ============================================================================
# 4. Orchestrator (Custom BaseAgent) – root entrypoint for ADK CLI
# ============================================================================

ORCHESTRATOR_INSTRUCTION = """
You are the Orchestrator Agent for the Open Mental Health Collective system.

Your responsibilities:
- Route turns through the Listener, Safety & Ethics, Therapy Coach and
  Resource Connector agents.
- Maintain and update shared session.state.
- Enforce safety policies, including respecting SafetyDecisionV2.
- Optionally emit a final, consolidated text response based on state.

Behavioral highlights:
- Always run the Listener first for each user message.
- Run Safety & Ethics whenever risk_level != "none" or user_intent is
  "crisis_support".
- If SafetyDecisionV2.block_reply == true, do NOT allow self-help content and
  instead show a short crisis-oriented message (from user_message_override if
  available).
- If user_intent is "unknown", favor asking clarifying questions before
  invoking the Therapy Coach.
- The Therapy Coach should only be invoked when it is safe to do so according
  to SafetyDecisionV2.allow_self_help and block_reply.
- The Resource Connector may be used to surface crisis lines or other services,
  especially for "resource_navigation" or "crisis_support" intents.

You should use the helpers and schemas defined in code; you do NOT call
other agents directly from this instruction—you are implemented in Python.
"""

class MentalHealthOrchestrator(BaseAgent):
    """
    Custom orchestrator agent for the Open Mental Health Collective.

    - Always runs ListenerAgent first.
    - Then runs Safety & Ethics Agent to get a SafetyDecision.
    - If SafetyDecision.block_reply is true, stops after yielding safety events.
    - Otherwise:
        * Routes to Therapy Coach for self-help coaching when appropriate.
        * Routes to Resource Connector when resources or escalation are needed.
    - State handoff is via:
        * session.state["listener_output"]
        * session.state["safety_decision"]
        * session.state["therapy_plan"]
        * session.state["resource_results"]
    """

    listener_agent: LlmAgent
    safety_ethics_agent: LlmAgent
    therapy_coach_agent: LlmAgent
    resource_connector_agent: LlmAgent

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        session = ctx.session
        state = session.state

        # 1) Listener: empathic front door + intent/risk
        async for event in self.listener_agent.run_async(ctx):
            yield event

        listener_raw = state.get("listener_output")
        if not listener_raw:
            # If Listener didn't emit properly, bail gracefully.
            return

        listener_output = ListenerOutput.model_validate_json(listener_raw)

        # 2) Safety & Ethics: policy / risk gate
        async for event in self.safety_ethics_agent.run_async(ctx):
            yield event

        safety_raw = state.get("safety_decision")
        if not safety_raw:
            # If safety decision is missing, do NOT proceed with self-help.
            return

        safety_decision = SafetyDecision.model_validate_json(safety_raw)

        # If reply is blocked, do not fan out to other agents.
        if safety_decision.block_reply:
            return

        # 3) Routing logic based on intent + safety
        # Basic routing rules:
        # - If crisis or escalation recommended -> ResourceConnector first.
        # - If self-help allowed and user wants skills/info -> TherapyCoach.
        # - If both resources and self-help make sense, run both sequentially.

        need_resources = False
        need_coach = False

        if safety_decision.should_escalate_to_human:
            need_resources = True

        if listener_output.user_intent in {
            UserIntent.RESOURCE_NAVIGATION,
            UserIntent.CRISIS_SUPPORT,
        }:
            need_resources = True

        if (
            safety_decision.allow_self_help
            and listener_output.user_intent
            in {
                UserIntent.CHECK_IN,
                UserIntent.PSYCHOEDUCATION,
                UserIntent.SKILLS_PRACTICE,
            }
        ):
            need_coach = True

        # In ambiguous cases (UNKNOWN intent) but safe, prefer a gentle check-in
        if (
            safety_decision.allow_self_help
            and listener_output.user_intent == UserIntent.UNKNOWN
        ):
            need_coach = True

        # 3a) Resource connector (if needed)
        if need_resources:
            async for event in self.resource_connector_agent.run_async(ctx):
                yield event

        # 3b) Therapy coach (if needed)
        if need_coach:
            async for event in self.therapy_coach_agent.run_async(ctx):
                yield event


# Root agent exposed for `adk web`
root_agent = MentalHealthOrchestrator(
    name="open_mental_health_orchestrator",
    description=(
        "Root orchestrator for the Open Mental Health Collective multi-agent "
        "system. It routes between Listener, Safety & Ethics, Therapy Coach, "
        "and Resource Connector agents and coordinates shared state."
    ),
    listener_agent=listener_agent,
    safety_ethics_agent=safety_ethics_agent,
    therapy_coach_agent=therapy_coach_agent,
    resource_connector_agent=resource_connector_agent,
)

class MentalHealthOrchestrator(BaseAgent):
    model_config = {"arbitrary_types_allowed": True}

    listener_agent: LlmAgent = listener_agent
    safety_agent: LlmAgent = safety_agent
    therapy_coach_agent: LlmAgent = therapy_coach_agent
    resource_connector_agent: LlmAgent = resource_connector_agent

    async def _run_async_impl(self, ctx: CallbackContext):
        state = ctx.session.state

        if state.get("schema_version") != SCHEMA_VERSION:
            state["schema_version"] = SCHEMA_VERSION

        # 1) Listener
        async for event in self.listener_agent.run_async(ctx):
            yield event

        state = ctx.session.state
        listener = load_listener_output(state)
        if not listener:
            text = (
                "I’m having trouble understanding the details of what you shared, "
                "but I’m glad you reached out. This system cannot provide emergency "
                "help. If you are in immediate danger or think you might hurt "
                "yourself or someone else, please contact local emergency "
                "services or a crisis hotline right away."
            )
            yield make_text_event(author=self.name, text=text)
            return

        must_run_safety = listener.risk.risk_level != "none" or (
            listener.user_intent == "crisis_support"
        )

        safety = None
        if must_run_safety:
            async for event in self.safety_agent.run_async(ctx):
                yield event
            state = ctx.session.state
            safety = load_safety_decision(state)

            if not safety:
                text = (
                    "Something went wrong while checking safety. "
                    "To be cautious, I can’t provide self-help exercises right now. "
                    "If you are struggling, please consider reaching out to a "
                    "trusted person or a local health professional. "
                    "If you are in immediate danger, contact emergency services "
                    "or a crisis hotline right away."
                )
                yield make_text_event(author=self.name, text=text)
                return

            if safety.block_reply:
                assembled = assemble_final_response(state)
                if not assembled:
                    assembled = (
                        "Based on what you’ve shared, it’s really important to reach "
                        "out to real-world support right now. This system cannot "
                        "safely continue with self-help in this moment. "
                        "If you are in immediate danger or feel like you might hurt "
                        "yourself or someone else, please contact local emergency "
                        "services or a crisis hotline immediately."
                    )
                yield make_text_event(author=self.name, text=assembled)
                return

        # UNKNOWN intent → clarify only
        intent = listener.user_intent
        if intent == "unknown":
            return

        # Resource path
        if intent in ("resource_navigation", "crisis_support"):
            async for event in self.resource_connector_agent.run_async(ctx):
                yield event
            state = ctx.session.state
            assembled = assemble_final_response(state)
            if assembled:
                yield make_text_event(author=self.name, text=assembled)
            return

        # Therapy path
        allow_self_help = True
        if must_run_safety:
            safety = load_safety_decision(ctx.session.state)
            allow_self_help = bool(safety and safety.allow_self_help and not safety.block_reply)

        if allow_self_help:
            async for event in self.therapy_coach_agent.run_async(ctx):
                yield event

        state = ctx.session.state
        assembled = assemble_final_response(state)
        if assembled:
            yield make_text_event(author=self.name, text=assembled)


root_agent = MentalHealthOrchestrator(
    name="open_mhc_orchestrator",
    instruction=ORCHESTRATOR_INSTRUCTION,
)
