"""
Factory for creating tools from definitions.
"""

from typing import Dict, Any, Optional

from alfred.tools.tool_definitions import TOOL_DEFINITIONS, ToolDefinition
from alfred.tools.generic_handler import GenericWorkflowHandler
from alfred.tools.workflow_config import WorkflowToolConfig
from alfred.models.schemas import ToolResponse
from alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ToolFactory:
    """Factory for creating tool handlers from definitions."""

    @staticmethod
    def create_handler(tool_name: str) -> GenericWorkflowHandler:
        """Create a handler for the given tool."""
        definition = TOOL_DEFINITIONS.get(tool_name)
        if not definition:
            raise ValueError(f"No definition found for tool: {tool_name}")

        # Convert ToolDefinition to WorkflowToolConfig
        config = WorkflowToolConfig(
            tool_name=definition.name,
            tool_class=definition.tool_class,
            required_status=definition.required_status,
            entry_status_map=definition.get_entry_status_map(),
            dispatch_on_init=definition.dispatch_on_init,
            dispatch_state_attr=(definition.dispatch_state.value if definition.dispatch_state and hasattr(definition.dispatch_state, "value") else None),
            context_loader=definition.context_loader,
            requires_artifact_from=definition.requires_artifact_from,
        )

        return GenericWorkflowHandler(config)

    @staticmethod
    async def execute_tool(tool_name: str, **kwargs) -> ToolResponse:
        """Execute a tool by name with the given arguments."""
        try:
            handler = ToolFactory.create_handler(tool_name)
            return await handler.execute(**kwargs)
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {e}", exc_info=True)
            return ToolResponse(status="error", message=f"Failed to execute tool {tool_name}: {str(e)}")

    @staticmethod
    def get_tool_info(tool_name: str) -> Dict[str, Any]:
        """Get information about a tool."""
        definition = TOOL_DEFINITIONS.get(tool_name)
        if not definition:
            return {"error": f"Unknown tool: {tool_name}"}

        return {
            "name": definition.name,
            "description": definition.description,
            "entry_statuses": [s.value for s in definition.entry_statuses],
            "required_status": definition.required_status.value if definition.required_status else None,
            "produces_artifacts": definition.produces_artifacts,
            "work_states": [s.value for s in definition.work_states],
            "dispatch_on_init": definition.dispatch_on_init,
        }


# Create singleton handlers for backward compatibility
_tool_handlers: Dict[str, GenericWorkflowHandler] = {}


def get_tool_handler(tool_name: str) -> GenericWorkflowHandler:
    """Get or create a singleton handler for a tool."""
    if tool_name not in _tool_handlers:
        _tool_handlers[tool_name] = ToolFactory.create_handler(tool_name)
    return _tool_handlers[tool_name]
