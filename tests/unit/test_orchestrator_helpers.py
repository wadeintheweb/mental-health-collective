"""Unit tests for orchestrator helper functions.

Tests cover:
- _assemble_final_response: Response assembly with various state permutations
- _coerce_model: Model validation scenarios
- State loaders: _load_listener_output, _load_safety_decision, etc.
- _make_text_event: Event creation
"""

import pytest
from unittest.mock import patch

from agents.orchestrator_agent.agent import (
    _assemble_final_response,
    _coerce_model,
    _load_listener_output,
    _load_safety_decision,
    _load_therapy_plan,
    _load_resource_results,
    _make_text_event,
)
from schemas import (
    ListenerOutput,
    SafetyDecisionV2,
    TherapyPlan,
    ResourceResults,
    ListenerRisk,
    ResourceItem,
    TherapyStep,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def valid_listener_output():
    """Valid ListenerOutput instance."""
    return ListenerOutput(
        normalized_utterance="I'm feeling stressed about work",
        detected_emotion="anxious",
        user_intent="check_in",
        risk=ListenerRisk(
            risk_level="low",
            risk_reasons=[],
            immediate_escalation_required=False,
            crisis_keywords=[],
        ),
        notes_for_downstream=None,
    )


@pytest.fixture
def valid_safety_decision():
    """Valid SafetyDecisionV2 instance with allow_self_help=True."""
    return SafetyDecisionV2(
        version="v2",
        overall_risk_level="low",
        allow_self_help=True,
        block_reply=False,
        user_message_override=None,
        rationale="User is experiencing normal work stress without safety concerns.",
        recommended_agent=None,
    )


@pytest.fixture
def blocking_safety_decision():
    """SafetyDecisionV2 with block_reply=True and override message."""
    return SafetyDecisionV2(
        version="v2",
        overall_risk_level="high",
        allow_self_help=False,
        block_reply=True,
        user_message_override="Please contact emergency services immediately.",
        rationale="High risk of self-harm detected.",
        recommended_agent=None,
    )


@pytest.fixture
def valid_therapy_plan():
    """Valid TherapyPlan instance."""
    return TherapyPlan(
        approach="CBT",
        focus="stress",
        coach_message="Let's work through some stress management techniques.",
        steps=[
            TherapyStep(
                label="Deep breathing",
                description="Take 3 slow, deep breaths",
            ),
            TherapyStep(
                label="Identify triggers",
                description="Write down what's causing stress",
            ),
        ],
        safety_notes="Stop if you feel overwhelmed and seek professional help.",
    )


@pytest.fixture
def valid_resource_results():
    """Valid ResourceResults instance."""
    return ResourceResults(
        user_facing_summary="Here are some mental health resources:",
        resources=[
            ResourceItem(
                name="NAMI Helpline",
                url="https://www.nami.org/help",
                region_hint="USA",
                description="National Alliance on Mental Illness support",
            ),
            ResourceItem(
                name="Crisis Text Line",
                url="https://www.crisistextline.org",
                region_hint=None,
                description="Text HOME to 741741",
            ),
        ],
        safety_notes="If in crisis, call 988 or local emergency services.",
    )


# =============================================================================
# Tests for _assemble_final_response
# =============================================================================

class TestAssembleFinalResponse:
    """Tests for _assemble_final_response function."""

    def test_assemble_safety_override(self, blocking_safety_decision):
        """Returns override message when block_reply=true."""
        state = {"safety_decision_v2": blocking_safety_decision}
        
        result = _assemble_final_response(state)
        
        assert result == "Please contact emergency services immediately."

    def test_assemble_no_override_when_block_reply_false(self, valid_safety_decision):
        """Ignores override if block_reply is false."""
        safety = valid_safety_decision
        safety.user_message_override = "This should be ignored"
        state = {"safety_decision_v2": safety}
        
        result = _assemble_final_response(state)
        
        # Should return None since no therapy plan or resources
        assert result is None

    def test_assemble_empty_state(self):
        """Returns None when no plan or resources."""
        result = _assemble_final_response({})
        assert result is None

    def test_assemble_with_therapy_plan(self, valid_therapy_plan):
        """Includes coach message and steps."""
        state = {"therapy_plan": valid_therapy_plan}
        
        result = _assemble_final_response(state)
        
        assert "Let's work through some stress management techniques" in result
        assert "1) Deep breathing: Take 3 slow, deep breaths" in result
        assert "2) Identify triggers: Write down what's causing stress" in result
        assert "Stop if you feel overwhelmed" in result
        assert "not a diagnosis or a substitute" in result  # Disclaimer

    def test_assemble_therapy_plan_blocked_by_safety(
        self, valid_therapy_plan, valid_safety_decision
    ):
        """Omits plan when allow_self_help=false."""
        safety = valid_safety_decision
        safety.allow_self_help = False
        state = {
            "therapy_plan": valid_therapy_plan,
            "safety_decision_v2": safety,
        }
        
        result = _assemble_final_response(state)
        
        # Plan should be omitted, but still returns disclaimer
        assert result is not None
        assert "Let's work through some stress management" not in result
        assert "not a diagnosis or a substitute" in result  # Disclaimer present

    def test_assemble_with_resources(self, valid_resource_results):
        """Includes resources with URLs and descriptions."""
        state = {"resource_results": valid_resource_results}
        
        result = _assemble_final_response(state)
        
        assert "Here are some mental health resources" in result
        assert "NAMI Helpline (USA) – https://www.nami.org/help" in result
        assert "Crisis Text Line – https://www.crisistextline.org" in result
        assert "If in crisis, call 988" in result
        assert "not a diagnosis or a substitute" in result

    def test_assemble_with_listener_and_therapy(
        self, valid_listener_output, valid_therapy_plan
    ):
        """Includes listener reflection + therapy."""
        state = {
            "listener_output": valid_listener_output,
            "therapy_plan": valid_therapy_plan,
        }
        
        result = _assemble_final_response(state)
        
        assert "Thank you for sharing" in result
        assert "I'm feeling stressed about work" in result
        assert "Let's work through some stress management" in result

    def test_assemble_with_all_components(
        self,
        valid_listener_output,
        valid_safety_decision,
        valid_therapy_plan,
        valid_resource_results,
    ):
        """Full response with all state components."""
        state = {
            "listener_output": valid_listener_output,
            "safety_decision_v2": valid_safety_decision,
            "therapy_plan": valid_therapy_plan,
            "resource_results": valid_resource_results,
        }
        
        result = _assemble_final_response(state)
        
        # Should include all components
        assert "Thank you for sharing" in result
        assert "I'm feeling stressed about work" in result
        assert "Let's work through some stress management" in result
        assert "Here are some mental health resources" in result
        assert "not a diagnosis or a substitute" in result

    def test_assemble_with_listener_and_resources(
        self, valid_listener_output, valid_resource_results
    ):
        """Listener + resources without therapy."""
        state = {
            "listener_output": valid_listener_output,
            "resource_results": valid_resource_results,
        }
        
        result = _assemble_final_response(state)
        
        assert "Thank you for sharing" in result
        assert "Here are some mental health resources" in result
        assert "not a diagnosis or a substitute" in result


# =============================================================================
# Tests for _coerce_model
# =============================================================================

class TestCoerceModel:
    """Tests for _coerce_model function."""

    def test_coerce_model_with_none(self):
        """None input returns None."""
        result = _coerce_model(None, ListenerOutput)
        assert result is None

    def test_coerce_model_with_model_instance(self, valid_listener_output):
        """Already a model instance returns as-is."""
        result = _coerce_model(valid_listener_output, ListenerOutput)
        assert result is valid_listener_output

    def test_coerce_model_with_valid_dict(self):
        """Valid dict validates to model."""
        data = {
            "normalized_utterance": "I need help",
            "detected_emotion": "distressed",
            "user_intent": "crisis_support",
            "risk": {
                "risk_level": "high",
                "risk_reasons": ["mentions harm"],
                "immediate_escalation_required": True,
                "crisis_keywords": ["help"],
            },
        }
        
        result = _coerce_model(data, ListenerOutput)
        
        assert isinstance(result, ListenerOutput)
        assert result.normalized_utterance == "I need help"
        assert result.user_intent == "crisis_support"

    def test_coerce_model_with_valid_json_string(self):
        """Valid JSON string validates to model."""
        json_str = '''
        {
            "normalized_utterance": "I need help",
            "detected_emotion": "distressed",
            "user_intent": "crisis_support",
            "risk": {
                "risk_level": "high",
                "risk_reasons": ["mentions harm"],
                "immediate_escalation_required": true,
                "crisis_keywords": ["help"]
            }
        }
        '''
        
        result = _coerce_model(json_str, ListenerOutput)
        
        assert isinstance(result, ListenerOutput)
        assert result.normalized_utterance == "I need help"

    @patch('agents.orchestrator_agent.agent.logger')
    def test_coerce_model_with_invalid_dict(self, mock_logger):
        """Invalid dict returns None and logs warning."""
        invalid_data = {"invalid": "data"}
        
        result = _coerce_model(invalid_data, ListenerOutput)
        
        assert result is None
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "Failed to validate dict as ListenerOutput" in warning_msg

    @patch('agents.orchestrator_agent.agent.logger')
    def test_coerce_model_with_invalid_json(self, mock_logger):
        """Malformed JSON returns None and logs warning."""
        invalid_json = '{"incomplete": '
        
        result = _coerce_model(invalid_json, ListenerOutput)
        
        assert result is None
        mock_logger.warning.assert_called_once()

    @patch('agents.orchestrator_agent.agent.logger')
    def test_coerce_model_with_invalid_type(self, mock_logger):
        """Wrong type returns None and logs warning."""
        result = _coerce_model(12345, ListenerOutput)
        
        assert result is None
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "Cannot coerce int to ListenerOutput" in warning_msg


# =============================================================================
# Tests for State Loaders
# =============================================================================

class TestStateLoaders:
    """Tests for state loader functions."""

    def test_load_listener_output_success(self, valid_listener_output):
        """Valid state returns ListenerOutput."""
        state = {"listener_output": valid_listener_output}
        
        result = _load_listener_output(state)
        
        assert result is valid_listener_output

    def test_load_listener_output_missing(self):
        """Missing key returns None."""
        result = _load_listener_output({})
        assert result is None

    def test_load_safety_decision_success(self, valid_safety_decision):
        """Valid state returns SafetyDecisionV2."""
        state = {"safety_decision_v2": valid_safety_decision}
        
        result = _load_safety_decision(state)
        
        assert result is valid_safety_decision

    def test_load_safety_decision_missing(self):
        """Missing key returns None."""
        result = _load_safety_decision({})
        assert result is None

    def test_load_therapy_plan_success(self, valid_therapy_plan):
        """Valid state returns TherapyPlan."""
        state = {"therapy_plan": valid_therapy_plan}
        
        result = _load_therapy_plan(state)
        
        assert result is valid_therapy_plan

    def test_load_therapy_plan_missing(self):
        """Missing key returns None."""
        result = _load_therapy_plan({})
        assert result is None

    def test_load_resource_results_success(self, valid_resource_results):
        """Valid state returns ResourceResults."""
        state = {"resource_results": valid_resource_results}
        
        result = _load_resource_results(state)
        
        assert result is valid_resource_results

    def test_load_resource_results_missing(self):
        """Missing key returns None."""
        result = _load_resource_results({})
        assert result is None


# =============================================================================
# Tests for _make_text_event
# =============================================================================

class TestMakeTextEvent:
    """Tests for _make_text_event function."""

    def test_make_text_event_creates_valid_event(self):
        """Event with correct author and content."""
        author = "test_agent"
        text = "This is a test message"
        
        event = _make_text_event(author, text)
        
        assert event.author == author
        assert event.content is not None
        assert event.content.role == "model"

    def test_make_text_event_content_structure(self):
        """Verifies Content/Part structure."""
        text = "Test message"
        
        event = _make_text_event("agent", text)
        
        assert len(event.content.parts) == 1
        assert event.content.parts[0].text == text
