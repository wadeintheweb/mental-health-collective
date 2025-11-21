# agents/__init__.py

"""
Top-level agents package.

Expose the root orchestrator and debug agent for convenience, e.g.:

    from agents import root_agent, debug_state_agent
"""

from .orchestrator.orchestrator_agent import root_agent
from .debug_state.debug_state_agent import debug_state_agent

__all__ = [
    "root_agent",
    "debug_state_agent",
]
