# src/alfred/core/workflow.py
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
from transitions.core import Machine

from src.alfred.constants import ToolName, Triggers
from src.alfred.models.planning_artifacts import (
    BranchCreationArtifact,
    ContextAnalysisArtifact,
    DesignArtifact,
    ExecutionPlanArtifact,
    GitStatusArtifact,
    StrategyArtifact,
)


class ReviewState(str, Enum):
    AWAITING_AI_REVIEW = "awaiting_ai_review"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"


class PlanTaskState(str, Enum):
    CONTEXTUALIZE = "contextualize"
    STRATEGIZE = "strategize"
    DESIGN = "design"
    GENERATE_SUBTASKS = "generate_subtasks"
    VERIFIED = "verified"


class StartTaskState(str, Enum):
    """A leaner, more logical state model for StartTaskTool."""
    AWAITING_GIT_STATUS = "awaiting_git_status"
    AWAITING_BRANCH_CREATION = "awaiting_branch_creation"
    VERIFIED = "verified"


class BaseWorkflowTool:
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
        return self.state == "verified"

    def _create_review_transitions(self, source_state: str, success_destination_state: str) -> List[Dict[str, Any]]:
        return [
            {"trigger": Triggers.submit_trigger(source_state), "source": source_state, "dest": ReviewState.AWAITING_AI_REVIEW.value},
            {"trigger": "ai_approve", "source": ReviewState.AWAITING_AI_REVIEW.value, "dest": ReviewState.AWAITING_HUMAN_REVIEW.value},
            {"trigger": "request_revision", "source": ReviewState.AWAITING_AI_REVIEW.value, "dest": source_state},
            {"trigger": "human_approve", "source": ReviewState.AWAITING_HUMAN_REVIEW.value, "dest": success_destination_state},
            {"trigger": "request_revision", "source": ReviewState.AWAITING_HUMAN_REVIEW.value, "dest": source_state},
        ]


class PlanTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str, persona_name: str = "planning"):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK, persona_name=persona_name)
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SUBTASKS: ExecutionPlanArtifact,
        }
        states = [state.value for state in PlanTaskState] + [state.value for state in ReviewState]
        transitions = [
            *self._create_review_transitions(PlanTaskState.CONTEXTUALIZE.value, PlanTaskState.STRATEGIZE.value),
            *self._create_review_transitions(PlanTaskState.STRATEGIZE.value, PlanTaskState.DESIGN.value),
            *self._create_review_transitions(PlanTaskState.DESIGN.value, PlanTaskState.GENERATE_SUBTASKS.value),
            *self._create_review_transitions(PlanTaskState.GENERATE_SUBTASKS.value, PlanTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=PlanTaskState.CONTEXTUALIZE.value)


class StartTaskTool(BaseWorkflowTool):
    """Re-architected StartTaskTool with a streamlined state machine."""
    def __init__(self, task_id: str, persona_name: str = "onboarding"):
        super().__init__(task_id, tool_name=ToolName.START_TASK, persona_name=persona_name)
        self.artifact_map = {
            StartTaskState.AWAITING_GIT_STATUS: GitStatusArtifact,
            StartTaskState.AWAITING_BRANCH_CREATION: BranchCreationArtifact,
        }
        states = [state.value for state in StartTaskState] + [state.value for state in ReviewState]
        transitions = [
            # 1. User submits Git Status. After review, success moves to AWAITING_BRANCH_CREATION.
            *self._create_review_transitions(StartTaskState.AWAITING_GIT_STATUS.value, StartTaskState.AWAITING_BRANCH_CREATION.value),
            # 2. User submits Branch Creation result. After review, success moves to VERIFIED (terminal).
            *self._create_review_transitions(StartTaskState.AWAITING_BRANCH_CREATION.value, StartTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=StartTaskState.AWAITING_GIT_STATUS.value)