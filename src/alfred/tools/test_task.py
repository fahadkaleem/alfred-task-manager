"""Test task implementation."""

from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName

# Get the handler from factory
test_task_handler = get_tool_handler(ToolName.TEST_TASK)


async def test_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the test_task tool."""
    return await test_task_handler.execute(task_id)
