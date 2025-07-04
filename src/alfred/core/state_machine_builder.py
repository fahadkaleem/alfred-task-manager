"""
Centralized state machine builder for workflow tools.
Eliminates duplication of state machine creation logic.
"""

from enum import Enum
from typing import List, Dict, Any, Type, Optional, Union
from transitions import Machine

from alfred.constants import Triggers
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class WorkflowStateMachineBuilder:
    """
    Builder for creating workflow state machines with standardized review cycles.

    This builder encapsulates the common pattern used across all workflow tools:
    1. Work states that require review
    2. AI review state
    3. Human review state
    4. Transitions between states
    """

    def __init__(self):
        self.states: List[str] = []
        self.transitions: List[Dict[str, Any]] = []

    def create_review_transitions(self, source_state: str, success_destination_state: str, revision_destination_state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Creates a standard review cycle for a work state.

        This generates:
        1. work_state -> work_state_awaiting_ai_review (via submit trigger)
        2. ai_review -> human_review (via ai_approve trigger)
        3. ai_review -> work_state (via request_revision trigger)
        4. human_review -> next_state (via human_approve trigger)
        5. human_review -> work_state (via request_revision trigger)
        6. work_state -> work_state (via request_revision trigger)
        """
        if revision_destination_state is None:
            revision_destination_state = source_state

        # Generate state names
        ai_review_state = f"{source_state}_awaiting_ai_review"
        human_review_state = f"{source_state}_awaiting_human_review"

        return [
            # Submit work to enter review cycle
            {
                "trigger": Triggers.submit_trigger(source_state),
                "source": source_state,
                "dest": ai_review_state,
            },
            # AI approves
            {
                "trigger": Triggers.AI_APPROVE,
                "source": ai_review_state,
                "dest": human_review_state,
            },
            # AI requests revision
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": ai_review_state,
                "dest": revision_destination_state,
            },
            # Human approves
            {
                "trigger": Triggers.HUMAN_APPROVE,
                "source": human_review_state,
                "dest": success_destination_state,
            },
            # Human requests revision
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": human_review_state,
                "dest": revision_destination_state,
            },
            # Working state requests revision (iterative refinement)
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": source_state,
                "dest": revision_destination_state,
            },
        ]

    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        return [f"{state}_awaiting_ai_review", f"{state}_awaiting_human_review"]

    def build_workflow_with_reviews(self, work_states: List[Union[str, Enum]], terminal_state: Union[str, Enum], initial_state: Union[str, Enum]) -> Dict[str, Any]:
        """
        Build a complete workflow with review cycles for each work state.

        Args:
            work_states: List of states that require review cycles
            terminal_state: Final state of the workflow
            initial_state: Starting state of the workflow

        Returns:
            Dictionary with 'states' and 'transitions' for Machine initialization
        """
        all_states = []
        all_transitions = []

        # Convert enums to strings if needed
        work_state_values = [s.value if hasattr(s, "value") else s for s in work_states]
        terminal_value = terminal_state.value if hasattr(terminal_state, "value") else terminal_state
        initial_value = initial_state.value if hasattr(initial_state, "value") else initial_state

        # Add all work states and their review states
        for i, state in enumerate(work_state_values):
            # Add the work state
            all_states.append(state)

            # Add review states
            review_states = self.get_review_states_for_state(state)
            all_states.extend(review_states)

            # Determine next state
            if i + 1 < len(work_state_values):
                next_state = work_state_values[i + 1]
            else:
                next_state = terminal_value

            # Create transitions for this state
            transitions = self.create_review_transitions(source_state=state, success_destination_state=next_state)
            all_transitions.extend(transitions)

        # Add terminal state
        all_states.append(terminal_value)

        return {"states": all_states, "transitions": all_transitions, "initial": initial_value}

    def build_simple_workflow(self, dispatch_state: Union[str, Enum], work_state: Union[str, Enum], terminal_state: Union[str, Enum], dispatch_trigger: str = "dispatch") -> Dict[str, Any]:
        """
        Build a simple workflow: dispatch -> work (with review) -> terminal.

        This is the pattern used by implement, review, test, and finalize tools.
        """
        dispatch_value = dispatch_state.value if hasattr(dispatch_state, "value") else dispatch_state
        work_value = work_state.value if hasattr(work_state, "value") else work_state
        terminal_value = terminal_state.value if hasattr(terminal_state, "value") else terminal_state

        states = [dispatch_value, work_value, f"{work_value}_awaiting_ai_review", f"{work_value}_awaiting_human_review", terminal_value]

        transitions = [{"trigger": dispatch_trigger, "source": dispatch_value, "dest": work_value}]

        # Add review transitions
        transitions.extend(self.create_review_transitions(source_state=work_value, success_destination_state=terminal_value))

        return {"states": states, "transitions": transitions, "initial": dispatch_value}


# Singleton instance for convenience
workflow_builder = WorkflowStateMachineBuilder()
