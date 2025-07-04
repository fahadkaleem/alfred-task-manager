"""
Generic workflow handler that replaces all individual tool handlers.
"""

from typing import Optional, Any

from alfred.core.workflow import BaseWorkflowTool
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.tools.workflow_config import WorkflowToolConfig
from alfred.state.manager import state_manager
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class GenericWorkflowHandler(BaseToolHandler):
    """
    A single, configurable handler that replaces all individual workflow tool handlers.

    This handler uses configuration to determine behavior, eliminating the need for
    separate handler classes for each tool.
    """

    def __init__(self, config: WorkflowToolConfig):
        """Initialize with a workflow configuration."""
        super().__init__(
            tool_name=config.tool_name,
            tool_class=config.tool_class,
            required_status=config.required_status,
        )
        self.config = config

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method using the configured tool class."""
        return self.config.tool_class(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """
        Generic setup logic driven by configuration.

        This method handles:
        1. Special validation (e.g., plan_task status check)
        2. Context loading from previous phases
        3. Auto-dispatch if configured
        4. State persistence
        """
        # Special validation for plan_task
        if self.config.tool_name == "plan_task":
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' or resume a 'planning' task.",
                )

        # Load context if configured (for both dispatching and non-dispatching tools)
        if self.config.context_loader:
            # Load task state for context
            task_state = state_manager.load_or_create(task.task_id)

            try:
                context = self.config.context_loader(task, task_state)
                # Update context_store with context loader values, allowing overrides for proper variable mapping
                for key, value in context.items():
                    tool_instance.context_store[key] = value
            except ValueError as e:
                # Context loader can raise ValueError for missing dependencies
                return ToolResponse(status="error", message=str(e))
            except Exception as e:
                logger.error("Context loader failed", task_id=task.task_id, tool_name=self.config.tool_name, error=str(e))
                return ToolResponse(status="error", message=f"Failed to load required context for {self.config.tool_name}: {str(e)}")

        # Check if we should dispatch on initialization
        if self.config.dispatch_on_init and tool_instance.state == self.config.dispatch_state_attr:
            # Dispatch to next state
            dispatch_method = getattr(tool_instance, self.config.target_state_method)
            dispatch_method()

            # Persist the state change
            state_manager.update_tool_state(task.task_id, tool_instance)

            logger.info("Dispatched tool to state", task_id=task.task_id, tool_name=self.config.tool_name, state=tool_instance.state)

        return None
