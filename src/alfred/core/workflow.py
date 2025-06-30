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
    FinalizeArtifact,
    GitStatusArtifact,
    ImplementationManifestArtifact,
    PRDInputArtifact,
    ReviewArtifact,
    StrategyArtifact,
    TaskCreationArtifact,
    TestResultArtifact,
)
from src.alfred.models.engineering_spec import EngineeringSpec


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


class ImplementTaskState(str, Enum):
    DISPATCHING = "dispatching"
    IMPLEMENTING = "implementing"
    VERIFIED = "verified"


class ReviewTaskState(str, Enum):
    DISPATCHING = "dispatching"
    REVIEWING = "reviewing"
    VERIFIED = "verified"


class TestTaskState(str, Enum):
    DISPATCHING = "dispatching"
    TESTING = "testing"
    VERIFIED = "verified"


class FinalizeTaskState(str, Enum):
    DISPATCHING = "dispatching"
    FINALIZING = "finalizing"
    VERIFIED = "verified"


class CreateSpecState(str, Enum):
    DISPATCHING = "dispatching"
    DRAFTING_SPEC = "drafting_spec"
    VERIFIED = "verified"


class CreateTasksState(str, Enum):
    DISPATCHING = "dispatching"
    DRAFTING_TASKS = "drafting_tasks"
    VERIFIED = "verified"


class BaseWorkflowTool:
    def __init__(self, task_id: str, tool_name: str):
        self.task_id = task_id
        self.tool_name = tool_name
        self.state: Optional[str] = None
        self.machine: Optional[Machine] = None
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}
        self.context_store: Dict[str, Any] = {}

    @property
    def is_terminal(self) -> bool:
        return self.state == "verified"

    def _create_review_transitions(self, source_state: str, success_destination_state: str, revision_destination_state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generates a unique, state-specific review cycle.
        Example: For source_state 'strategize', it creates 'strategize_awaiting_ai_review'.
        """
        if revision_destination_state is None:
            revision_destination_state = source_state

        # Dynamic state name generation
        ai_review_state = f"{source_state}_awaiting_ai_review"
        human_review_state = f"{source_state}_awaiting_human_review"

        return [
            # Trigger to enter the review cycle for this specific state
            {
                "trigger": Triggers.submit_trigger(source_state),
                "source": source_state,
                "dest": ai_review_state,
            },
            # AI approves its own work
            {
                "trigger": Triggers.AI_APPROVE,
                "source": ai_review_state,
                "dest": human_review_state,
            },
            # AI requests revision (goes back to the start of this state's work)
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": ai_review_state,
                "dest": revision_destination_state,
            },
            # Human approves the work, advancing to the next major state
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
        ]

    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        return [f"{state}_awaiting_ai_review", f"{state}_awaiting_human_review"]

    def get_final_work_state(self) -> str:
        """Get the final work state that produces the main artifact.

        This method should be overridden by subclasses to return the state
        that produces the primary artifact for the tool.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_final_work_state()")


class PlanTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK)
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SUBTASKS: ExecutionPlanArtifact,
        }

        # Define the base states
        base_states = [state.value for state in PlanTaskState]

        # Dynamically generate the unique review states for each step
        review_states = []
        for state in [PlanTaskState.CONTEXTUALIZE, PlanTaskState.STRATEGIZE, PlanTaskState.DESIGN, PlanTaskState.GENERATE_SUBTASKS]:
            review_states.extend(self.get_review_states_for_state(state.value))

        all_states = base_states + review_states

        # Define the transitions using the new helper
        transitions = [
            *self._create_review_transitions(source_state=PlanTaskState.CONTEXTUALIZE.value, success_destination_state=PlanTaskState.STRATEGIZE.value),
            *self._create_review_transitions(source_state=PlanTaskState.STRATEGIZE.value, success_destination_state=PlanTaskState.DESIGN.value),
            *self._create_review_transitions(source_state=PlanTaskState.DESIGN.value, success_destination_state=PlanTaskState.GENERATE_SUBTASKS.value),
            *self._create_review_transitions(source_state=PlanTaskState.GENERATE_SUBTASKS.value, success_destination_state=PlanTaskState.VERIFIED.value),
        ]

        self.machine = Machine(model=self, states=all_states, transitions=transitions, initial=PlanTaskState.CONTEXTUALIZE.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return PlanTaskState.GENERATE_SUBTASKS.value


class StartTaskTool(BaseWorkflowTool):
    """Re-architected StartTaskTool with a streamlined state machine."""

    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.START_TASK)
        self.artifact_map = {
            StartTaskState.AWAITING_GIT_STATUS: GitStatusArtifact,
            StartTaskState.AWAITING_BRANCH_CREATION: BranchCreationArtifact,
        }

        # Define base states
        base_states = [state.value for state in StartTaskState]

        # Generate review states
        review_states = []
        review_states.extend(self.get_review_states_for_state(StartTaskState.AWAITING_GIT_STATUS.value))
        review_states.extend(self.get_review_states_for_state(StartTaskState.AWAITING_BRANCH_CREATION.value))

        all_states = base_states + review_states

        transitions = [
            # 1. User submits Git Status. After review, success moves to AWAITING_BRANCH_CREATION.
            *self._create_review_transitions(StartTaskState.AWAITING_GIT_STATUS.value, StartTaskState.AWAITING_BRANCH_CREATION.value),
            # 2. User submits Branch Creation result. After review, success moves to VERIFIED (terminal).
            *self._create_review_transitions(StartTaskState.AWAITING_BRANCH_CREATION.value, StartTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=all_states, transitions=transitions, initial=StartTaskState.AWAITING_GIT_STATUS.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return StartTaskState.AWAITING_BRANCH_CREATION.value


class ImplementTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.IMPLEMENT_TASK)
        self.artifact_map = {
            # The ONLY artifact submitted is from the IMPLEMENTING state.
            ImplementTaskState.IMPLEMENTING: ImplementationManifestArtifact,
        }

        source_state = ImplementTaskState.IMPLEMENTING.value

        # Dynamically generate the state names
        states = [
            ImplementTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            ImplementTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": ImplementTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=ImplementTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=ImplementTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return ImplementTaskState.IMPLEMENTING.value


class ReviewTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.REVIEW_TASK)
        self.artifact_map = {
            # Only the reviewing state produces an artifact
            ReviewTaskState.REVIEWING: ReviewArtifact,
        }

        source_state = ReviewTaskState.REVIEWING.value

        states = [
            ReviewTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            ReviewTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": ReviewTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=ReviewTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=ReviewTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return ReviewTaskState.REVIEWING.value


class TestTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.TEST_TASK)
        self.artifact_map = {
            # Only the testing state produces an artifact
            TestTaskState.TESTING: TestResultArtifact,
        }

        source_state = TestTaskState.TESTING.value

        states = [
            TestTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            TestTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": TestTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=TestTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=TestTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return TestTaskState.TESTING.value


class FinalizeTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.FINALIZE_TASK)
        self.artifact_map = {
            # Only the finalizing state produces an artifact
            FinalizeTaskState.FINALIZING: FinalizeArtifact,
        }

        source_state = FinalizeTaskState.FINALIZING.value

        states = [
            FinalizeTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            FinalizeTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": FinalizeTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=FinalizeTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=FinalizeTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return FinalizeTaskState.FINALIZING.value


class CreateSpecTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_SPEC)
        self.artifact_map = {
            CreateSpecState.DRAFTING_SPEC: EngineeringSpec,  # Only one artifact
        }

        source_state = CreateSpecState.DRAFTING_SPEC.value

        states = [
            CreateSpecState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            CreateSpecState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": CreateSpecState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=CreateSpecState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=CreateSpecState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return CreateSpecState.DRAFTING_SPEC.value


class CreateTasksTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_TASKS)
        self.artifact_map = {
            CreateTasksState.DRAFTING_TASKS: TaskCreationArtifact,  # Only one artifact
        }

        source_state = CreateTasksState.DRAFTING_TASKS.value

        states = [
            CreateTasksState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            CreateTasksState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": CreateTasksState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=CreateTasksState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=CreateTasksState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return CreateTasksState.DRAFTING_TASKS.value
