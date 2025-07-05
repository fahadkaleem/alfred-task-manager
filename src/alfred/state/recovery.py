# src/alfred/state/recovery.py
"""
Tool recovery functionality for Alfred workflow tools.
Handles reconstruction of workflow tools from persisted state.
"""

from typing import Dict, Optional, Type

from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.structured_logger import get_logger
from alfred.state.manager import state_manager
from alfred.constants import ToolName

logger = get_logger(__name__)


class ToolRecovery:
    """Handles recovery of workflow tools from persisted state."""

    # Lazy-loaded registry to avoid circular imports
    _TOOL_REGISTRY: Optional[Dict[str, Type[BaseWorkflowTool]]] = None

    @classmethod
    def _get_tool_registry(cls) -> Dict[str, Type[BaseWorkflowTool]]:
        """Lazy-load the tool registry to avoid circular imports."""
        if cls._TOOL_REGISTRY is None:
            from alfred.tools.tool_definitions import TOOL_DEFINITIONS

            cls._TOOL_REGISTRY = {name: definition.tool_class for name, definition in TOOL_DEFINITIONS.items() if definition.tool_class is not None}
        return cls._TOOL_REGISTRY

    @classmethod
    def recover_tool(cls, task_id: str) -> Optional[BaseWorkflowTool]:
        """Attempt to recover a tool from the unified persisted state."""
        task_state = state_manager.load_or_create_task_state(task_id)
        persisted_tool_state = task_state.active_tool_state

        if not persisted_tool_state:
            logger.debug(f"No active tool state found for task {task_id} to recover.")
            return None

        tool_name = persisted_tool_state.tool_name
        tool_class = cls._get_tool_registry().get(tool_name)
        if not tool_class:
            logger.error(f"Unknown tool type: {tool_name}. Cannot recover.")
            return None

        try:
            tool = tool_class(task_id=task_id)
            tool.state = persisted_tool_state.current_state
            tool.context_store = persisted_tool_state.context_store

            logger.info(f"Successfully recovered {tool_name} for task {task_id} in state {tool.state}")
            return tool
        except Exception as e:
            logger.error(f"Failed to recover tool for task {task_id}: {e}", exc_info=True)
            return None

    @classmethod
    def register_tool(cls, tool_name: str, tool_class: Type[BaseWorkflowTool]) -> None:
        """Register a new tool type for recovery."""
        cls._get_tool_registry()[tool_name] = tool_class
        logger.debug(f"Registered tool type: {tool_name}")

    @classmethod
    def can_recover(cls, task_id: str) -> bool:
        """Check if a task has a recoverable tool state."""
        task_state = state_manager.load_or_create_task_state(task_id)
        persisted_tool_state = task_state.active_tool_state
        if not persisted_tool_state:
            return False

        tool_name = persisted_tool_state.tool_name
        return tool_name in cls._get_tool_registry()


def recover_tool_from_state(task_id: str, tool_name: str) -> BaseWorkflowTool:
    """
    Helper function to recover or create a tool for the given task and tool name.
    This is used by the individual tool implementations.
    """
    from alfred.orchestration.orchestrator import orchestrator

    # Check if tool is already active
    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(f"Found active tool for task {task_id} in state {tool_instance.state}")
        return tool_instance

    # Try to recover from persisted state
    tool_instance = ToolRecovery.recover_tool(task_id)
    if tool_instance:
        orchestrator.active_tools[task_id] = tool_instance
        logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        return tool_instance

    # Create new tool
    tool_class = ToolRecovery._get_tool_registry().get(tool_name)
    if not tool_class:
        raise ValueError(f"Unknown tool type: {tool_name}")

    tool_instance = tool_class(task_id=task_id)
    orchestrator.active_tools[task_id] = tool_instance

    # Persist the initial state
    state_manager.update_tool_state(task_id, tool_instance)
    logger.info(f"Created new {tool_name} tool for task {task_id}")

    return tool_instance
