# src/alfred/core/workflow.py
from transitions.core import Machine
from typing import List, Dict, Any, Type
from enum import Enum
from pydantic import BaseModel

class PlanTaskState(str, Enum):
    """States for the PlanTaskTool's internal State Machine."""
    CONTEXTUALIZE = "contextualize"
    REVIEW_CONTEXT = "review_context"
    STRATEGIZE = "strategize"
    REVIEW_STRATEGY = "review_strategy"
    DESIGN = "design"
    REVIEW_DESIGN = "review_design"
    GENERATE_SLOTS = "generate_slots"
    REVIEW_PLAN = "review_plan"
    VERIFIED = "verified"  # The final, terminal state for the tool.

class BaseWorkflowTool:
    """A base class providing shared State Machine logic for Alfred's tools."""
    def __init__(self, task_id: str, tool_name: str = None, persona_name: str = None):
        self.task_id = task_id
        self.tool_name = tool_name or self.__class__.__name__.lower().replace('tool', '')
        self.persona_name = persona_name
        self.state = None  # Will be set by the Machine instance
        self.machine = None
        # Add a new attribute for artifact mapping
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}

    @property
    def is_terminal(self) -> bool:
        """
        Checks if the current state is a terminal (final) state.
        Override in subclasses to define terminal states.
        """
        return self.state == "verified"

    def _create_review_transitions(self, source_state: Enum, review_state: Enum, success_destination_state: Enum) -> List[Dict[str, Any]]:
        """Factory for creating the standard two-step (AI, Human) review transitions."""
        return [
            # Submit work, transition into the review state for AI self-review
            {'trigger': f'submit_{source_state.value}', 'source': source_state.value, 'dest': review_state.value},
            # AI self-approves, moves to human review
            {'trigger': 'ai_approve', 'source': review_state.value, 'dest': success_destination_state.value},
            # A rejection from AI review goes back to the source state to be reworked
            {'trigger': 'request_revision', 'source': review_state.value, 'dest': source_state.value},
        ]

class PlanTaskTool(BaseWorkflowTool):
    """Encapsulates the state and logic for the `plan_task` command."""
    def __init__(self, task_id: str, persona_name: str = "planning"):
        super().__init__(task_id, tool_name="plan_task", persona_name=persona_name)
        
        # Import the new artifact models
        from src.alfred.models.planning_artifacts import (
            ContextAnalysisArtifact, 
            StrategyArtifact, 
            DesignArtifact, 
            ExecutionPlanArtifact
        )
        
        # Define the artifact validation map for this tool
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SLOTS: ExecutionPlanArtifact,
        }
        
        # Use the PlanTaskState Enum for state definitions - convert to string values
        states = [state.value for state in PlanTaskState]

        transitions = [
            *self._create_review_transitions(PlanTaskState.CONTEXTUALIZE, PlanTaskState.REVIEW_CONTEXT, PlanTaskState.STRATEGIZE),
            *self._create_review_transitions(PlanTaskState.STRATEGIZE, PlanTaskState.REVIEW_STRATEGY, PlanTaskState.DESIGN),
            *self._create_review_transitions(PlanTaskState.DESIGN, PlanTaskState.REVIEW_DESIGN, PlanTaskState.GENERATE_SLOTS),
            *self._create_review_transitions(PlanTaskState.GENERATE_SLOTS, PlanTaskState.REVIEW_PLAN, PlanTaskState.VERIFIED),
        ]
        
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=PlanTaskState.CONTEXTUALIZE.value)