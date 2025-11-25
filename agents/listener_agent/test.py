import os
from dotenv import load_dotenv, find_dotenv
import sys
from pathlib import Path

from google.adk.agents.callback_context import CallbackContext

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)


from google.adk.agents import LlmAgent
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from schemas import ListenerOutput

_ = load_dotenv(find_dotenv())