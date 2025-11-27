# agents/utils.py

"""Utility functions for agent modules."""

from pathlib import Path


def load_instruction(filename: str) -> str:
    """
    Load an agent instruction from a markdown file in the prompts directory.
    
    Args:
        filename: Name of the instruction file (e.g., "orchestrator_instruction.md")
        
    Returns:
        The instruction text as a string
        
    Raises:
        FileNotFoundError: If the instruction file does not exist
        IOError: If there's an error reading the file
    """
    # Get the repository root (parent of agents directory)
    agents_dir = Path(__file__).parent
    repo_root = agents_dir.parent
    prompts_dir = repo_root / "prompts"
    
    instruction_file = prompts_dir / filename
    
    if not instruction_file.exists():
        raise FileNotFoundError(
            f"Instruction file not found: {instruction_file}\n"
            f"Expected location: {prompts_dir}"
        )
    
    try:
        return instruction_file.read_text(encoding="utf-8")
    except Exception as e:
        raise IOError(
            f"Error reading instruction file {instruction_file}: {e}"
        ) from e
