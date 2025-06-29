# src/alfred/state/recovery.py
"""
Tool recovery functionality for Alfred workflow tools.
Handles reconstruction of workflow tools from persisted state.
"""
from typing import Dict, Optional, Type

from src.alfred.core.workflow import BaseWorkflowTool, PlanTaskTool
from src.alfred.lib.logger import get_logger
from src.alfred.state.manager import state_manager
from src.alfred.constants import ToolName

logger = get_logger(__name__)


class ToolRecovery:
    """Handles recovery of workflow tools from persisted state."""

    TOOL_REGISTRY: Dict[str, Type[BaseWorkflowTool]] = {
        ToolName.PLAN_TASK: PlanTaskTool,
    }

    @classmethod
    def recover_tool(cls, task_id: str) -> Optional[BaseWorkflowTool]:
        """Attempt to recover a tool from the unified persisted state."""
        task_state = state_manager.load_or_create_task_state(task_id)
        persisted_tool_state = task_state.active_tool_state

        if not persisted_tool_state:
            logger.debug(f"No active tool state found for task {task_id} to recover.")
            return None

        tool_name = persisted_tool_state.tool_name
        tool_class = cls.TOOL_REGISTRY.get(tool_name)
        if not tool_class:
            logger.error(f"Unknown tool type: {tool_name}. Cannot recover.")
            return None

        try:
            tool = tool_class(task_id=task_id)
            tool.state = persisted_tool_state.current_state
            tool.context_store = persisted_tool_state.context_store
            tool.persona_name = persisted_tool_state.persona_name

            logger.info(
                f"Successfully recovered {tool_name} for task {task_id} in state {tool.state}"
            )
            return tool
        except Exception as e:
            logger.error(
                f"Failed to recover tool for task {task_id}: {e}", exc_info=True
            )
            return None

    @classmethod
    def register_tool(cls, tool_name: str, tool_class: Type[BaseWorkflowTool]) -> None:
        """Register a new tool type for recovery."""
        cls.TOOL_REGISTRY[tool_name] = tool_class
        logger.debug(f"Registered tool type: {tool_name}")

    @classmethod
    def can_recover(cls, task_id: str) -> bool:
        """Check if a task has a recoverable tool state."""
        task_state = state_manager.load_or_create_task_state(task_id)
        persisted_tool_state = task_state.active_tool_state
        if not persisted_tool_state:
            return False

        tool_name = persisted_tool_state.tool_name
        return tool_name in cls.TOOL_REGISTRY