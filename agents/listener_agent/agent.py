# agents/listener_agent/agent.py

import os
from dotenv import load_dotenv, find_dotenv

from google.adk.agents import LlmAgent

from pydantic import BaseModel, Field, field_validator

from schemas import ListenerOutput
from agents.utils import load_instruction

_ = load_dotenv(find_dotenv())

DEFAULT_MODEL = os.environ.get("OMHC_MODEL_NAME", "gemini-2.0-flash")

listener_agent = LlmAgent(
    name="listener_agent",
    model=DEFAULT_MODEL,
    instruction=load_instruction("listener_instruction.md"),
    output_schema=ListenerOutput,
    output_key="listener_output",
    include_contents="default",
)

