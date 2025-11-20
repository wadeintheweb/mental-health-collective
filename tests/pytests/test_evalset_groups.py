# E.3 Evalset Group Tests (by risk / intent)

import os
import pathlib

import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

THIS_DIR = pathlib.Path(__file__).parent
EVALS_DIR = THIS_DIR / "evals"

LOW_RISK_EVALSET = EVALS_DIR / "open_mhc_low_risk.evalset.json"
MEDIUM_RISK_EVALSET = EVALS_DIR / "open_mhc_medium_risk.evalset.json"
CRISIS_EVALSET = EVALS_DIR / "open_mhc_crisis.evalset.json"
UNKNOWN_INTENT_EVALSET = EVALS_DIR / "open_mhc_unknown_intent.evalset.json"
HIGH_RISK_EVALSET = EVALS_DIR / "open_mhc_high_risk.evalset.json"


def _skip_if_env_missing():
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set; skipping evalset integration test.")
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        pytest.skip("GOOGLE_CLOUD_PROJECT not set; skipping evalset integration test.")


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.eval_low_risk
async def test_low_risk_evalset_group_runs():
    if not LOW_RISK_EVALSET.exists():
        pytest.skip(f"Low-risk evalset not found at {LOW_RISK_EVALSET}")
    _skip_if_env_missing()
    await AgentEvaluator.evaluate(
        agent_module="open_mhc_app",
        eval_dataset_file_path_or_dir=str(LOW_RISK_EVALSET),
        num_runs=1,
    )


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.eval_medium_risk
async def test_medium_risk_evalset_group_runs():
    if not MEDIUM_RISK_EVALSET.exists():
        pytest.skip(f"Medium-risk evalset not found at {MEDIUM_RISK_EVALSET}")
    _skip_if_env_missing()
    await AgentEvaluator.evaluate(
        agent_module="open_mhc_app",
        eval_dataset_file_path_or_dir=str(MEDIUM_RISK_EVALSET),
        num_runs=1,
    )


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.eval_crisis
async def test_crisis_evalset_group_runs():
    if not CRISIS_EVALSET.exists():
        pytest.skip(f"Crisis evalset not found at {CRISIS_EVALSET}")
    _skip_if_env_missing()
    await AgentEvaluator.evaluate(
        agent_module="open_mhc_app",
        eval_dataset_file_path_or_dir=str(CRISIS_EVALSET),
        num_runs=1,
    )


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.eval_unknown_intent
async def test_unknown_intent_evalset_group_runs():
    if not UNKNOWN_INTENT_EVALSET.exists():
        pytest.skip(f"Unknown-intent evalset not found at {UNKNOWN_INTENT_EVALSET}")
    _skip_if_env_missing()
    await AgentEvaluator.evaluate(
        agent_module="open_mhc_app",
        eval_dataset_file_path_or_dir=str(UNKNOWN_INTENT_EVALSET),
        num_runs=1,
    )


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.eval_high_risk
async def test_high_risk_evalset_group_runs():
    if not HIGH_RISK_EVALSET.exists():
        pytest.skip(f"High-risk evalset not found at {HIGH_RISK_EVALSET}")
    _skip_if_env_missing()
    await AgentEvaluator.evaluate(
        agent_module="open_mhc_app",
        eval_dataset_file_path_or_dir=str(HIGH_RISK_EVALSET),
        num_runs=1,
    )
