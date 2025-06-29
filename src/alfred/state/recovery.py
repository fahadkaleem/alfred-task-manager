"""
Tool recovery functionality for Alfred workflow tools.

Handles reconstruction of workflow tools from persisted state after crashes or restarts.
"""

from typing import Optional, Dict, Type

from src.alfred.core.workflow import BaseWorkflowTool, PlanTaskTool
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ToolRecovery:
    """
    Handles recovery of workflow tools from persisted state.
    
    This class provides the ability to reconstruct workflow tools
    from their persisted state after a crash or restart.
    """
    
    # Registry of tool types for reconstruction
    TOOL_REGISTRY: Dict[str, Type[BaseWorkflowTool]] = {
        "plan_task": PlanTaskTool,
        # Future tools will be added here as they are implemented
        # "implement_task": ImplementTaskTool,
        # "review_code": ReviewCodeTool,
    }
    
    @classmethod
    def recover_tool(cls, task_id: str) -> Optional[BaseWorkflowTool]:
        """
        Attempt to recover a tool from persisted state.
        
        This method:
        1. Loads the persisted state from disk
        2. Identifies the correct tool class
        3. Reconstructs the tool with its saved state
        
        Args:
            task_id: The task identifier
            
        Returns:
            Reconstructed tool instance if successful, None otherwise
        """
        # Load persisted state
        persisted_state = state_manager.load_tool_state(task_id)
        if not persisted_state:
            logger.debug(f"No persisted state found for task {task_id}")
            return None
        
        # Find the tool class
        tool_name = persisted_state.get("tool_name")
        tool_class = cls.TOOL_REGISTRY.get(tool_name)
        if not tool_class:
            logger.error(f"Unknown tool type: {tool_name}. Cannot recover.")
            return None
        
        try:
            # Reconstruct the tool
            tool = tool_class(task_id=task_id)
            
            # Restore the state
            # Convert string state back to enum if necessary
            current_state = persisted_state.get("current_state")
            if hasattr(tool_class, "get_state_from_string"):
                tool.state = tool_class.get_state_from_string(current_state)
            else:
                # Fallback: try to set directly
                tool.state = current_state
            
            # Restore context store
            tool.context_store = persisted_state.get("context_store", {})
            
            # Restore persona name
            tool.persona_name = persisted_state.get("persona_name", tool.persona_name)
            
            logger.info(
                f"Successfully recovered {tool_name} for task {task_id} "
                f"in state {current_state}"
            )
            return tool
            
        except Exception as e:
            logger.error(f"Failed to recover tool for task {task_id}: {e}")
            return None
    
    @classmethod
    def register_tool(cls, tool_name: str, tool_class: Type[BaseWorkflowTool]) -> None:
        """
        Register a new tool type for recovery.
        
        Args:
            tool_name: The name identifier for the tool
            tool_class: The tool class that can be instantiated
        """
        cls.TOOL_REGISTRY[tool_name] = tool_class
        logger.debug(f"Registered tool type: {tool_name}")
    
    @classmethod
    def can_recover(cls, task_id: str) -> bool:
        """
        Check if a task has recoverable state.
        
        Args:
            task_id: The task identifier
            
        Returns:
            True if the task can be recovered, False otherwise
        """
        if not state_manager.has_persisted_state(task_id):
            return False
        
        state = state_manager.load_tool_state(task_id)
        if not state:
            return False
        
        tool_name = state.get("tool_name")
        return tool_name in cls.TOOL_REGISTRY