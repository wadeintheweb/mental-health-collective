from __future__ import annotations

from enum import Enum
from typing import AsyncGenerator, List, Optional

from typing_extensions import override
from pydantic import BaseModel, Field

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools import google_search  # built-in Google Search tool

# ============================================================================
# 4. Orchestrator (Custom BaseAgent) – root entrypoint for ADK CLI
# ============================================================================


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


