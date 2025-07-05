# src/alfred/tools/base_tool_handler.py
from abc import ABC, abstractmethod
from typing import Optional, Type, Any

from alfred.core.prompter import generate_prompt
from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.structured_logger import get_logger, setup_task_logging
from alfred.lib.task_utils import load_task_with_error_details
from alfred.models.schemas import Task, TaskStatus, ToolResponse

logger = get_logger(__name__)


class BaseToolHandler(ABC):
    """Base handler for all tool implementations using the Template Method pattern."""

    def __init__(
        self,
        tool_name: str,
        tool_class: Optional[Type[BaseWorkflowTool]],
        required_status: Optional[TaskStatus] = None,
    ):
        self.tool_name = tool_name
        self.tool_class = tool_class
        self.required_status = required_status

    async def execute(self, task_id: str, **kwargs: Any) -> ToolResponse:
        """Template method defining the algorithm structure for all tools."""
        setup_task_logging(task_id)

        task, error_msg = load_task_with_error_details(task_id)
        if not task:
            return ToolResponse(status="error", message=error_msg or f"Task '{task_id}' not found.")

        # Check required status if specified
        if self.required_status and task.task_status != self.required_status:
            return ToolResponse(
                status="error",
                message=f"Task '{task_id}' has status '{task.task_status.value}'. Tool '{self.tool_name}' requires status to be '{self.required_status.value}'.",
            )

        # Always create fresh tool instance - no persistence
        tool_instance = self._create_new_tool(task_id, task)

        # The setup_tool hook is responsible for tool-specific setup
        setup_response = await self._setup_tool(tool_instance, task, **kwargs)
        if setup_response and isinstance(setup_response, ToolResponse):
            return setup_response

        return self._generate_response(tool_instance, task)

    def _generate_response(self, tool_instance: BaseWorkflowTool, task: Task) -> ToolResponse:
        """Common logic for generating the final prompt and tool response."""
        try:
            prompt = generate_prompt(
                task_id=task.task_id,
                tool_name=tool_instance.tool_name,
                state=tool_instance.state,
                task=task,
                additional_context=tool_instance.context_store.copy(),
            )
            message = f"Initiated tool '{self.tool_name}' for task '{task.task_id}'. Current state: {tool_instance.state}."
            return ToolResponse(status="success", message=message, next_prompt=prompt)
        except (ValueError, RuntimeError, KeyError) as e:
            # Handle errors from the new prompter
            logger.error("Prompt generation failed", task_id=task.task_id, tool_name=tool_instance.tool_name, error=str(e), exc_info=True)
            return ToolResponse(status="error", message=f"A critical error occurred while preparing the next step: {e}")

    @abstractmethod
    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method for creating a new tool instance. Subclasses must implement."""
        pass

    @abstractmethod
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Hook for subclasses to perform tool-specific setup, including initial state dispatch."""
        pass
