# src/alfred/tools/registry.py
from typing import Dict, Optional, Type, Callable, Coroutine, Any, List, TYPE_CHECKING
from dataclasses import dataclass
import inspect

from alfred.core.workflow import BaseWorkflowTool
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.lib.structured_logger import get_logger

# THIS IS THE FIX for Blocker #3
if TYPE_CHECKING:
    from alfred.tools.base_tool_handler import BaseToolHandler

logger = get_logger(__name__)


class DuplicateToolError(Exception):
    """Raised when a tool name is registered more than once."""

    pass


@dataclass(frozen=True)
class ToolConfig:
    """Immutable configuration for a registered tool."""

    name: str
    handler_class: Any
    tool_class: Type[BaseWorkflowTool]
    entry_status_map: Dict[TaskStatus, TaskStatus]
    implementation: Callable[..., Coroutine[Any, Any, ToolResponse]]

    def get_handler(self):
        """Get handler instance, handling both class and instance cases."""
        if callable(self.handler_class):
            return self.handler_class()
        return self.handler_class


class ToolRegistry:
    """Self-registering tool system using decorators."""

    def __init__(self):
        self._tools: Dict[str, ToolConfig] = {}

    def register(
        self,
        name: str,
        handler_class: Any,
        tool_class: Type[BaseWorkflowTool],
        entry_status_map: Dict[TaskStatus, TaskStatus],
    ):
        """Decorator to register a tool with its full configuration."""
        if name in self._tools:
            raise DuplicateToolError(f"Tool '{name}' is already registered.")

        def decorator(func: Callable[..., Coroutine[Any, Any, ToolResponse]]):
            config = ToolConfig(name=name, handler_class=handler_class, tool_class=tool_class, entry_status_map=entry_status_map, implementation=func)
            self._tools[name] = config
            logger.info(f"Registered tool: '{name}'")
            return func

        return decorator

    def get_tool_config(self, name: str) -> Optional[ToolConfig]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[ToolConfig]:
        """Returns all registered tools, sorted alphabetically by name."""
        return sorted(self._tools.values(), key=lambda tc: tc.name)


# Global singleton instance
tool_registry = ToolRegistry()
