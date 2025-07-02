"""
Workflow tool configuration system for eliminating handler duplication.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Type, Callable, Any
from enum import Enum

from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.models.schemas import TaskStatus


@dataclass
class WorkflowToolConfig:
    """Configuration for a workflow tool, replacing individual handlers."""

    # Basic configuration
    tool_name: str
    tool_class: Type[BaseWorkflowTool]
    required_status: Optional[TaskStatus] = None

    # Entry status mapping (for status transitions on tool creation)
    entry_status_map: Dict[TaskStatus, TaskStatus] = None

    # Dispatch configuration
    dispatch_on_init: bool = False
    dispatch_state_attr: Optional[str] = None  # e.g., "DISPATCHING"
    target_state_method: str = "dispatch"  # method to call for state transition

    # Context loading configuration
    context_loader: Optional[Callable[[Any, Any], Dict[str, Any]]] = None

    # Validation
    requires_artifact_from: Optional[str] = None  # e.g., ToolName.PLAN_TASK

    def __post_init__(self):
        """Validate configuration consistency."""
        if self.dispatch_on_init and not self.dispatch_state_attr:
            raise ValueError(f"Tool {self.tool_name} has dispatch_on_init=True but no dispatch_state_attr")

        if self.entry_status_map is None:
            self.entry_status_map = {}


# NOTE: Individual tool configurations have been moved to tool_definitions.py
# This file now only contains the WorkflowToolConfig class for backward compatibility.
