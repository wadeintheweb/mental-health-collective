# ============================================================================
# Shared schemas for JSON IO between agents (saved in session.state)
# ============================================================================
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


SCHEMA_VERSION = "omhc_v2_0_0"


class ListenerRisk(BaseModel):
    risk_level: Literal["none", "low", "medium", "high", "crisis"] = "none"
    risk_reasons: List[str] = Field(default_factory=list)
    immediate_escalation_required: bool = False
    crisis_keywords: List[str] = Field(default_factory=list)


class ListenerOutput(BaseModel):
    normalized_utterance: str
    detected_emotion: str
    user_intent: Literal[
        "check_in",
        "psychoeducation",
        "skills_practice",
        "resource_navigation",
        "crisis_support",
        "unknown",
    ]
    risk: ListenerRisk
    notes_for_downstream: Optional[str] = None


POLICY_TAG = Literal[
    "suicidality_imminent",
    "suicidality_non_imminent",
    "self_harm_non_suicidal",
    "violence_risk",
    "psychosis_or_reality_loss",
    "substance_intoxication_or_overdose",
    "minor_or_child",
    "abuse_or_domestic_violence",
    "medical_emergency",
    "other_high_risk",
]


class SafetyDecisionV2(BaseModel):
    """
    v2 safety decision model, designed to be:
    - Machine-actionable (clear booleans, enums).
    - Operator-friendly (policy_tags, notes_for_operators).
    """

    version: Literal["v2"] = "v2"

    overall_risk_level: Literal["none", "low", "medium", "high", "crisis"] = "none"

    # Core behavioral gates
    allow_self_help: bool = True
    block_reply: bool = False
    should_escalate_to_human: bool = False

    escalation_channel: Optional[
        Literal[
            "crisis_hotline",
            "primary_care",
            "therapist",
            "emergency_services",
            "peer_support",
            "unknown",
        ]
    ] = None

    # Policy classification for analytics / review
    policy_tags: List[POLICY_TAG] = Field(default_factory=list)

    # Optional user message override for hard block
    user_message_override: Optional[str] = None

    # Explanation / operator notes
    reasons: List[str] = Field(default_factory=list)
    notes_for_operators: Optional[str] = None

    @field_validator("allow_self_help")
    @classmethod
    def enforce_block_reply_implies_no_self_help(cls, v, info):  # noqa: D417
        data = info.data
        if data.get("block_reply") and v:
            raise ValueError("block_reply=True implies allow_self_help=False")
        return v

    @field_validator("escalation_channel")
    @classmethod
    def escalation_requires_flag(cls, v, info):  # noqa: D417
        if v is not None and not info.data.get("should_escalate_to_human"):
            raise ValueError(
                "escalation_channel set but should_escalate_to_human is False"
            )
        return v


class TherapyStep(BaseModel):
    label: str
    description: str


class TherapyPlan(BaseModel):
    approach: Literal["CBT", "MBSR", "mixed", "other"] = "CBT"
    focus: Literal["stress", "mood", "anxiety", "grounding", "other"] = "stress"
    coach_message: str
    steps: List[TherapyStep] = Field(default_factory=list)
    safety_notes: Optional[str] = None


class ResourceItem(BaseModel):
    name: str
    url: Optional[str] = None
    region_hint: Optional[str] = None
    description: Optional[str] = None


class ResourceResults(BaseModel):
    user_facing_summary: str
    resources: List[ResourceItem] = Field(default_factory=list)
    safety_notes: Optional[str] = None
