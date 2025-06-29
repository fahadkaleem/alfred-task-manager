# src/alfred/core/workflow.py
from enum import Enum
from typing import Any, Dict, List, Type, Optional

from pydantic import BaseModel
from transitions.core import Machine

from src.alfred.constants import ToolName, Triggers
from src.alfred.models.planning_artifacts import (
    ContextAnalysisArtifact,
    DesignArtifact,
    ExecutionPlanArtifact,
    StrategyArtifact,
)


class ReviewState(str, Enum):
    """Generic review states applicable to all tools."""

    AWAITING_AI_REVIEW = "awaiting_ai_review"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"


class PlanTaskState(str, Enum):
    """Working states for the PlanTaskTool's internal State Machine."""

    CONTEXTUALIZE = "contextualize"
    STRATEGIZE = "strategize"
    DESIGN = "design"
    GENERATE_SUBTASKS = "generate_subtasks"
    VERIFIED = "verified"


class BaseWorkflowTool:
    """A base class providing shared State Machine logic for Alfred's tools."""

    def __init__(self, task_id: str, tool_name: str, persona_name: str):
        self.task_id = task_id
        self.tool_name = tool_name
        self.persona_name = persona_name
        self.state: Optional[str] = None
        self.machine: Optional[Machine] = None
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}
        self.context_store: Dict[str, Any] = {}

    @property
    def is_terminal(self) -> bool:
        """Checks if the current state is a terminal (final) state."""
        return self.state == "verified"

    def _create_review_transitions(
        self, source_state: Enum, success_destination_state: Enum
    ) -> List[Dict[str, Any]]:
        """Factory for the mandatory two-step (AI -> Human) review transitions."""
        return [
            {
                "trigger": Triggers.submit_trigger(source_state.value),
                "source": source_state.value,
                "dest": ReviewState.AWAITING_AI_REVIEW.value,
            },
            {
                "trigger": "ai_approve",
                "source": ReviewState.AWAITING_AI_REVIEW.value,
                "dest": ReviewState.AWAITING_HUMAN_REVIEW.value,
            },
            {
                "trigger": "request_revision",
                "source": ReviewState.AWAITING_AI_REVIEW.value,
                "dest": source_state.value,
            },
            {
                "trigger": "human_approve",
                "source": ReviewState.AWAITING_HUMAN_REVIEW.value,
                "dest": success_destination_state.value,
            },
            {
                "trigger": "request_revision",
                "source": ReviewState.AWAITING_HUMAN_REVIEW.value,
                "dest": source_state.value,
            },
        ]


class PlanTaskTool(BaseWorkflowTool):
    """Encapsulates the state and logic for the `plan_task` command."""

    def __init__(self, task_id: str, persona_name: str = "planning"):
        super().__init__(
            task_id, tool_name=ToolName.PLAN_TASK, persona_name=persona_name
        )

        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SUBTASKS: ExecutionPlanArtifact,
        }

        states = [state.value for state in PlanTaskState] + [
            state.value for state in ReviewState
        ]

        transitions = [
            *self._create_review_transitions(
                PlanTaskState.CONTEXTUALIZE, PlanTaskState.STRATEGIZE
            ),
            *self._create_review_transitions(
                PlanTaskState.STRATEGIZE, PlanTaskState.DESIGN
            ),
            *self._create_review_transitions(
                PlanTaskState.DESIGN, PlanTaskState.GENERATE_SUBTASKS
            ),
            *self._create_review_transitions(
                PlanTaskState.GENERATE_SUBTASKS, PlanTaskState.VERIFIED
            ),
        ]

        self.machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial=PlanTaskState.CONTEXTUALIZE.value,
        )