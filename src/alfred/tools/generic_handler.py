"""
Generic workflow handler that replaces all individual tool handlers.
"""

import inspect
from typing import Optional, Any

from alfred.core.workflow import BaseWorkflowTool
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.tools.workflow_config import WorkflowToolConfig
from alfred.state.manager import state_manager
from alfred.core.prompter import generate_prompt
from alfred.lib.structured_logger import get_logger, setup_task_logging
from alfred.lib.task_utils import load_task_with_error_details

logger = get_logger(__name__)


class GenericWorkflowHandler(BaseToolHandler):
    """
    A single, configurable handler that replaces all individual workflow tool handlers.

    This handler uses configuration to determine behavior and operates using the new
    stateless WorkflowEngine pattern, eliminating the need for stateful tool instances.
    """

    def __init__(self, config: WorkflowToolConfig):
        """Initialize with a workflow configuration."""
        super().__init__(
            tool_name=config.tool_name,
            tool_class=config.tool_class,
            required_status=config.required_status,
        )
        self.config = config

    async def execute(self, task_id: str = None, **kwargs: Any) -> ToolResponse:
        """Enhanced execute method supporting both workflow and simple tools."""
        # Simple tool path (tool_class == None)
        if self.config.tool_class is None:
            return await self._execute_simple_tool(task_id=task_id, **kwargs)

        # New stateless workflow path using WorkflowEngine
        return await self._execute_stateless_workflow(task_id, **kwargs)

    async def _execute_simple_tool(self, **kwargs: Any) -> ToolResponse:
        """Execute simple tool via context_loader function."""
        if self.config.context_loader is None:
            return ToolResponse(status="error", message=f"Tool {self.config.tool_name} has no tool_class and no context_loader")

        try:
            # Call the logic function with all arguments
            if inspect.iscoroutinefunction(self.config.context_loader):
                return await self.config.context_loader(**kwargs)
            else:
                return self.config.context_loader(**kwargs)
        except Exception as e:
            logger.error("Simple tool execution failed", tool_name=self.config.tool_name, error=str(e))
            return ToolResponse(status="error", message=f"Tool execution failed: {str(e)}")

    async def _execute_stateless_workflow(self, task_id: str, **kwargs: Any) -> ToolResponse:
        """Execute stateless workflow using WorkflowEngine pattern."""
        setup_task_logging(task_id)

        task, error_msg = load_task_with_error_details(task_id)
        if not task:
            return ToolResponse(status="error", message=error_msg or f"Task '{task_id}' not found.")

        # Load or create task state
        task_state = state_manager.load_or_create(task_id)

        # Check required status
        if self.required_status and task.task_status != self.required_status:
            return ToolResponse(
                status="error",
                message=f"Task '{task_id}' has status '{task.task_status.value}'. Tool '{self.tool_name}' requires status to be '{self.required_status.value}'.",
            )

        # Special validation for plan_task
        if self.config.tool_name == "plan_task":
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' or resume a 'planning' task.",
                )

        # Get or create workflow state
        workflow_state = self._get_or_create_workflow_state(task_state, task_id)

        # Create stateless tool instance for configuration access
        tool_instance = self.config.tool_class(task_id=task_id)

        # Setup context and handle dispatch
        setup_response = await self._setup_stateless_tool(workflow_state, tool_instance, task, **kwargs)
        if setup_response:
            return setup_response

        # Generate response using current state
        return self._generate_stateless_response(workflow_state, tool_instance, task)

    def _get_or_create_workflow_state(self, task_state: TaskState, task_id: str) -> WorkflowState:
        """Get or create workflow state for this tool."""
        # Check if we already have an active workflow state for this tool
        if task_state.active_tool_state and task_state.active_tool_state.tool_name == self.config.tool_name:
            return task_state.active_tool_state

        # Create new workflow state (local import to avoid circular dependency)
        from alfred.tools.tool_definitions import get_tool_definition

        tool_definition = get_tool_definition(self.config.tool_name)
        if not tool_definition:
            raise ValueError(f"No tool definition found for {self.config.tool_name}")

        initial_state = tool_definition.initial_state.value if hasattr(tool_definition.initial_state, "value") else str(tool_definition.initial_state)

        workflow_state = WorkflowState(task_id=task_id, tool_name=self.config.tool_name, current_state=initial_state, context_store={})

        # Update task state with new workflow state
        with state_manager.complex_update(task_id) as state:
            state.active_tool_state = workflow_state

        logger.info("Created new workflow state", task_id=task_id, tool_name=self.config.tool_name, state=initial_state)
        return workflow_state

    async def _setup_stateless_tool(self, workflow_state: WorkflowState, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Setup context and handle dispatch using stateless pattern."""

        # Load context if configured
        if self.config.context_loader:
            # Load task state for context
            task_state = state_manager.load_or_create(task.task_id)

            try:
                context = self.config.context_loader(task, task_state)
                # Update workflow state context_store with context loader values
                for key, value in context.items():
                    workflow_state.context_store[key] = value
            except ValueError as e:
                # Context loader can raise ValueError for missing dependencies
                return ToolResponse(status="error", message=str(e))
            except Exception as e:
                logger.error("Context loader failed", task_id=task.task_id, tool_name=self.config.tool_name, error=str(e))
                return ToolResponse(status="error", message=f"Failed to load required context for {self.config.tool_name}: {str(e)}")

        # Handle auto-dispatch if configured
        if self.config.dispatch_on_init and workflow_state.current_state == self.config.dispatch_state_attr:
            try:
                # Local import to avoid circular dependency
                from alfred.core.workflow_engine import WorkflowEngine

                # Use WorkflowEngine for state transition (local import to avoid circular dependency)
                from alfred.tools.tool_definitions import get_tool_definition

                tool_definition = get_tool_definition(self.config.tool_name)
                engine = WorkflowEngine(tool_definition)

                # Execute dispatch transition
                new_state = engine.execute_trigger(workflow_state.current_state, self.config.target_state_method)
                workflow_state.current_state = new_state

                # Persist the state change
                with state_manager.complex_update(task.task_id) as state:
                    state.active_tool_state = workflow_state

                logger.info("Dispatched tool to state", task_id=task.task_id, tool_name=self.config.tool_name, state=new_state)

            except Exception as e:
                logger.error("Auto-dispatch failed", task_id=task.task_id, tool_name=self.config.tool_name, error=str(e))
                return ToolResponse(status="error", message=f"Failed to dispatch tool: {str(e)}")

        return None

    def _generate_stateless_response(self, workflow_state: WorkflowState, tool_instance: BaseWorkflowTool, task: Task) -> ToolResponse:
        """Generate response using stateless pattern."""
        try:
            prompt = generate_prompt(
                task_id=task.task_id,
                tool_name=workflow_state.tool_name,
                state=workflow_state.current_state,
                task=task,
                additional_context=workflow_state.context_store.copy(),
            )
            message = f"Initiated tool '{self.config.tool_name}' for task '{task.task_id}'. Current state: {workflow_state.current_state}."
            return ToolResponse(status="success", message=message, next_prompt=prompt)
        except (ValueError, RuntimeError, KeyError) as e:
            # Handle errors from the new prompter
            logger.error("Prompt generation failed", task_id=task.task_id, tool_name=workflow_state.tool_name, error=str(e), exc_info=True)
            return ToolResponse(status="error", message=f"A critical error occurred while preparing the next step: {e}")

    # Legacy methods kept for BaseToolHandler compatibility but not used in stateless path
    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Legacy factory method - not used in stateless workflow path."""
        return self.config.tool_class(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Legacy setup method - not used in stateless workflow path."""
        return None
