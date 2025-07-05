"""
WorkflowEngine: Lightweight state machine manager for stateless workflow tools.

This engine operates on pure state dictionaries and provides state transition
functionality without maintaining any state itself.
"""

from typing import List, Dict, Any, TYPE_CHECKING
from transitions import Machine

from alfred.core.state_machine_builder import workflow_builder
from alfred.lib.structured_logger import get_logger

if TYPE_CHECKING:
    from alfred.tools.tool_definitions import ToolDefinition

logger = get_logger(__name__)


class WorkflowEngine:
    """
    Lightweight state machine engine operating on pure state dictionaries.

    This class is responsible for managing state machine transitions without
    holding any state itself. It operates on simple state strings and uses
    the existing ToolDefinition infrastructure.
    """

    def __init__(self, tool_definition: "ToolDefinition"):
        """
        Initialize with tool definition for state machine configuration.

        Args:
            tool_definition: The tool definition containing state machine config
        """
        self.tool_definition = tool_definition
        self._machine_config = self._build_machine_config()

    def _build_machine_config(self) -> Dict[str, Any]:
        """Build machine configuration from tool definition."""
        if len(self.tool_definition.work_states) > 1:
            # Multi-step workflow with reviews
            return workflow_builder.build_workflow_with_reviews(
                work_states=self.tool_definition.work_states, terminal_state=self.tool_definition.terminal_state, initial_state=self.tool_definition.initial_state
            )
        elif self.tool_definition.dispatch_state:
            # Simple workflow with dispatch
            return workflow_builder.build_simple_workflow(
                dispatch_state=self.tool_definition.dispatch_state,
                work_state=self.tool_definition.work_states[0] if self.tool_definition.work_states else None,
                terminal_state=self.tool_definition.terminal_state,
            )
        else:
            # Minimal configuration
            states = [state.value if hasattr(state, "value") else str(state) for state in self.tool_definition.work_states]
            if self.tool_definition.terminal_state:
                terminal = self.tool_definition.terminal_state.value if hasattr(self.tool_definition.terminal_state, "value") else str(self.tool_definition.terminal_state)
                states.append(terminal)

            return {"states": states, "transitions": [], "initial": states[0] if states else None}

    def execute_trigger(self, current_state: str, trigger: str) -> str:
        """
        Execute a state transition and return new state string.

        Args:
            current_state: Current state string
            trigger: Trigger name to execute

        Returns:
            New state string after transition

        Raises:
            ValueError: If transition is invalid
        """
        # Create a temporary state object for the machine
        state_obj = type("StateObj", (), {"state": current_state})()

        # Create machine with temporary object
        machine = Machine(model=state_obj, states=self._machine_config["states"], transitions=self._machine_config["transitions"], initial=current_state, auto_transitions=False)

        # Validate transition exists
        valid_transitions = machine.get_transitions(trigger=trigger, source=current_state)
        if not valid_transitions:
            raise ValueError(f"No valid transition for trigger '{trigger}' from state '{current_state}'")

        # Execute transition
        trigger_method = getattr(state_obj, trigger, None)
        if not trigger_method:
            raise ValueError(f"Trigger method '{trigger}' not found")

        trigger_method()

        return state_obj.state

    def get_valid_triggers(self, from_state: str) -> List[str]:
        """
        Get list of valid triggers from a given state.

        Args:
            from_state: State to get triggers for

        Returns:
            List of valid trigger names
        """
        # Create temporary machine to get transitions
        state_obj = type("StateObj", (), {"state": from_state})()
        machine = Machine(model=state_obj, states=self._machine_config["states"], transitions=self._machine_config["transitions"], initial=from_state, auto_transitions=False)

        # Get all transitions from this state
        triggers = set()
        for transition in self._machine_config["transitions"]:
            if transition.get("source") == from_state:
                triggers.add(transition.get("trigger"))

        return sorted(list(triggers))

    def is_terminal_state(self, state: str) -> bool:
        """
        Check if a state is terminal (workflow complete).

        Args:
            state: State string to check

        Returns:
            True if state is terminal, False otherwise
        """
        if self.tool_definition.terminal_state:
            terminal_value = self.tool_definition.terminal_state.value if hasattr(self.tool_definition.terminal_state, "value") else str(self.tool_definition.terminal_state)
            return state == terminal_value

        return False
