"""
Epic Task Manager MCP Prompts
"""

from pathlib import Path


async def implement_next_task(task_id: str | None = None) -> str:
    """
    Load and return the implementation prompt for the Epic Task Manager workflow.

    This prompt guides users through the complete Epic Task Manager workflow
    for implementing a Jira ticket through all phases.

    Args:
        task_id: Optional task ID to include in the prompt. If provided,
                 the prompt will be customized with this specific task ID.

    Returns:
        str: The formatted prompt content from the markdown template
    """
    # Get the path to the prompt template
    prompt_path = Path(__file__).parent.parent / "templates" / "prompts" / "client" / "implement_next_task.md"

    # Read the prompt content
    with prompt_path.open(encoding="utf-8") as f:
        content = f.read()

    # If a task_id is provided, replace the placeholder
    if task_id:
        content = content.replace("TASK_ID", task_id)

    return content
