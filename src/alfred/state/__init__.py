"""
State management package.

This package provides the state management infrastructure for Alfred,
including the StateManager for task state persistence.
"""

from alfred.state.manager import StateManager, state_manager

__all__ = ["StateManager", "state_manager"]
