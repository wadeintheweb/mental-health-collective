# tests/test_open_mhc_eval.py

import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator


@pytest.mark.asyncio
async def test_open_mhc_smoke_eval():
    """
    Run a small smoke-test eval set against the Open Mental Health Collective root agent.

    This uses the ADK "test file" approach with one eval set that contains three
    single-turn sessions. Criteria are configured in tests/evals/test_config.json.
    """
    await AgentEvaluator.evaluate(
        agent_module="agents.orchestrator_agent.agent",  # package containing __init__.py with root_agent
        eval_dataset_file_path_or_dir="tests/evals/open_mhc_smoke.test.json",
        # config_file_path="tests/evals/test_config.json",
    )
