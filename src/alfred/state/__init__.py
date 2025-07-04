"""
State management module for Alfred workflow tools.

This module provides persistence and recovery capabilities for workflow tools,
ensuring that task progress survives crashes and restarts.
"""

from alfred.state.manager import StateManager, state_manager
from alfred.state.recovery import ToolRecovery

__all__ = ["StateManager", "state_manager", "ToolRecovery"]
