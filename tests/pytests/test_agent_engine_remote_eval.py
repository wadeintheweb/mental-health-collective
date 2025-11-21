# tests/test_agent_engine_remote_eval.py

import pytest
from agent_engine_eval import run_eval

@pytest.mark.remote
def test_agent_engine_smoke_eval():
    result = run_eval()
    summary = result["summary"]
    assert summary["pass_rate"] >= 1.0
