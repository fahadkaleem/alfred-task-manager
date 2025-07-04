# src/alfred/tools/base_tool_handler.py
from abc import ABC, abstractmethod
from typing import Optional, Type, Any

from alfred.core.prompter import generate_prompt
from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.logger import get_logger, setup_task_logging
from alfred.lib.task_utils import load_task, load_task_with_error_details
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.orchestration.orchestrator import orchestrator
from alfred.state.manager import state_manager
from alfred.state.recovery import ToolRecovery
from alfred.tools.registry import tool_registry

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

        get_tool_result = self._get_or_create_tool(task_id, task)
        if isinstance(get_tool_result, ToolResponse):
            return get_tool_result
        tool_instance = get_tool_result

        # The setup_tool hook is now responsible for initial state dispatch if needed
        setup_response = await self._setup_tool(tool_instance, task, **kwargs)
        if setup_response and isinstance(setup_response, ToolResponse):
            return setup_response

        return self._generate_response(tool_instance, task)

    def _get_or_create_tool(self, task_id: str, task: Task) -> BaseWorkflowTool | ToolResponse:
        """Common tool recovery and creation logic."""
        if task_id in orchestrator.active_tools:
            logger.info(f"Found active tool '{self.tool_name}' for task {task_id}.")
            return orchestrator.active_tools[task_id]

        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(f"Recovered tool '{self.tool_name}' for task {task_id}.")
            return tool_instance

        if self.required_status and task.task_status != self.required_status:
            return ToolResponse(
                status="error",
                message=f"Task '{task_id}' has status '{task.task_status.value}'. Tool '{self.tool_name}' requires status to be '{self.required_status.value}'.",
            )

        # Use the factory method for instantiation
        new_tool = self._create_new_tool(task_id, task)
        orchestrator.active_tools[task_id] = new_tool

        # Get the tool config from the registry to determine status transition
        tool_config = tool_registry.get_tool_config(self.tool_name)
        if tool_config and task.task_status in tool_config.entry_status_map:
            new_status = tool_config.entry_status_map[task.task_status]
            state_manager.update_task_status(task_id, new_status)

        # Persist the initial state of the newly created tool
        state_manager.update_tool_state(task_id, new_tool)

        logger.info(f"Created new '{self.tool_name}' tool for task {task_id}.")
        return new_tool

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
            logger.error(f"Prompt generation failed: {e}", exc_info=True)
            return ToolResponse(status="error", message=f"A critical error occurred while preparing the next step: {e}")

    @abstractmethod
    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method for creating a new tool instance. Subclasses must implement."""
        pass

    @abstractmethod
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Hook for subclasses to perform tool-specific setup, including initial state dispatch."""
        pass
