# src/alfred/tools/test_task.py
"""Test task using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
test_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.TEST_TASK])


async def test_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the test_task tool."""
    return await test_task_handler.execute(task_id)
