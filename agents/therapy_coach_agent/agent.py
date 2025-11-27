# agents/therapy_coach_agent/agent.py

import os
from dotenv import load_dotenv, find_dotenv

from google.adk.agents import LlmAgent

from schemas import TherapyPlan

_ = load_dotenv(find_dotenv())

DEFAULT_MODEL = os.environ.get("OMHC_MODEL_NAME", "gemini-2.0-flash")

from agents.utils import load_instruction

therapy_coach_agent = LlmAgent(
    name="therapy_coach_agent",
    model=DEFAULT_MODEL,
    instruction=load_instruction("therapy_coach_instruction.md"),
    output_schema=TherapyPlan,
    output_key="therapy_plan",
    include_contents="default",
)
