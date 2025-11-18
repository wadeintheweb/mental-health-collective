# ============================================================================
# 1. Shared schemas for JSON IO between agents (saved in session.state)
# ============================================================================
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskAssessment(BaseModel):
    """Structured view of risk that the Listener & Safety agents share."""

    risk_level: RiskLevel = Field(
        description="Overall clinical / safety risk: none, low, medium, high."
    )
    risk_reasons: List[str] = Field(
        default_factory=list,
        description="Plain-language reasons for the risk rating."
    )
    immediate_escalation_required: bool = Field(
        description=(
            "True if there is any indication of imminent self-harm, "
            "harm to others, or inability to care for basic needs."
        )
    )
    crisis_keywords: List[str] = Field(
        default_factory=list,
        description="Any high-salience phrases the model used to justify risk."
    )


class UserIntent(str, Enum):
    """High-level intent classification produced by ListenerAgent."""

    CHECK_IN = "check_in"                # general emotional check-in
    PSYCHOEDUCATION = "psychoeducation"  # wants info/education
    SKILLS_PRACTICE = "skills_practice"  # wants a CBT/MBSR-style exercise
    RESOURCE_NAVIGATION = "resource_navigation"  # wants services/resources
    CRISIS_SUPPORT = "crisis_support"    # in clear crisis / distress
    UNKNOWN = "unknown"                  # fall-back


class ListenerOutput(BaseModel):
    """Output schema for Listener Agent (stored at state['listener_output'])."""

    normalized_utterance: str = Field(
        description="Cleaned-up, concise paraphrase of what the user said."
    )
    detected_emotion: str = Field(
        description="Primary emotion(s) inferred from the user message."
    )
    user_intent: UserIntent = Field(
        description="The inferred high-level intent for routing."
    )
    risk: RiskAssessment = Field(
        description="Initial risk screen based only on the current user turn."
    )
    notes_for_downstream: Optional[str] = Field(
        default=None,
        description=(
            "Short note for downstream agents about context, constraints, "
            "or user preferences. Avoid PHI and identifiers."
        )
    )


class SafetyDecision(BaseModel):
    """Output schema for Safety & Ethics Agent (state['safety_decision'])."""

    allow_self_help: bool = Field(
        description="True if it is appropriate to continue with automated self-help."
    )
    should_escalate_to_human: bool = Field(
        description=(
            "True if user should be encouraged to contact human/urgent support "
            "based on policy & model-armor checks."
        )
    )
    block_reply: bool = Field(
        description=(
            "If true, downstream conversational agents must NOT respond, and "
            "the system should only show a safety / escalation message."
        )
    )
    rationale: str = Field(
        description="Short explanation in plain language of this decision."
    )
    user_message_override: Optional[str] = Field(
        default=None,
        description=(
            "If present, a user-facing message that should replace any other "
            "agent responses for this turn (e.g., crisis + escalation guidance)."
        )
    )
    policy_tags: List[str] = Field(
        default_factory=list,
        description=(
            "Optional machine-readable tags explaining which policies or "
            "risk patterns were triggered."
        )
    )


class TherapyCoachOutput(BaseModel):
    """Output schema for Therapy Coach Agent (state['therapy_plan'])."""

    coach_message: str = Field(
        description="Warm, brief, user-facing message for this turn."
    )
    technique_label: str = Field(
        description="Name of the main CBT/MBSR micro-skill used."
    )
    steps: List[str] = Field(
        description=(
            "Numbered, digestible steps the user can follow right now."
        )
    )
    optional_home_practice: Optional[str] = Field(
        default=None,
        description="Optional small homework between sessions, if appropriate."
    )
    safety_reminder: str = Field(
        description=(
            "Short reminder that this is NOT therapy and cannot handle crises."
        )
    )


class ResourceSummary(BaseModel):
    """One structured resource recommendation."""

    name: str = Field(description="Name of the resource/service/hotline/app.")
    url: Optional[str] = Field(
        default=None,
        description="Web URL if applicable. Leave null if not available."
    )
    category: str = Field(
        description="High-level category, e.g., 'crisis hotline', 'peer support'."
    )
    jurisdiction_or_region: Optional[str] = Field(
        default=None,
        description="Geographic region or country the resource covers, if known."
    )
    access_notes: Optional[str] = Field(
        default=None,
        description="How to access it, eligibility, or costs (if known)."
    )


class ResourceConnectorOutput(BaseModel):
    """Output schema for Resource Connector Agent (state['resource_results'])."""

    resources: List[ResourceSummary] = Field(
        description="A small, high-quality set of resources (2–6 items)."
    )
    user_facing_summary: str = Field(
        description=(
            "Short narrative explanation of the resources and how to use them."
        )
    )
    disclaimer: str = Field(
        description=(
            "Explicit reminder to verify details and that this is not emergency care."
        )
    )