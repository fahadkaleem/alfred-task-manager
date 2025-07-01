# src/alfred/core/workflow.py
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
from transitions.core import Machine

from src.alfred.constants import ToolName, Triggers
from src.alfred.core.state_machine_builder import workflow_builder
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


    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        # Delegate to builder
        return workflow_builder.get_review_states_for_state(state)

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

        # Use the builder to create the state machine configuration
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=[
                PlanTaskState.CONTEXTUALIZE,
                PlanTaskState.STRATEGIZE,
                PlanTaskState.DESIGN,
                PlanTaskState.GENERATE_SUBTASKS
            ],
            terminal_state=PlanTaskState.VERIFIED,
            initial_state=PlanTaskState.CONTEXTUALIZE
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

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

        # Use builder for the two-step workflow
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=[
                StartTaskState.AWAITING_GIT_STATUS,
                StartTaskState.AWAITING_BRANCH_CREATION
            ],
            terminal_state=StartTaskState.VERIFIED,
            initial_state=StartTaskState.AWAITING_GIT_STATUS
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return StartTaskState.AWAITING_BRANCH_CREATION.value


class ImplementTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.IMPLEMENT_TASK)
        self.artifact_map = {
            ImplementTaskState.IMPLEMENTING: ImplementationManifestArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=ImplementTaskState.DISPATCHING,
            work_state=ImplementTaskState.IMPLEMENTING,
            terminal_state=ImplementTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return ImplementTaskState.IMPLEMENTING.value


class ReviewTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.REVIEW_TASK)
        self.artifact_map = {
            ReviewTaskState.REVIEWING: ReviewArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=ReviewTaskState.DISPATCHING,
            work_state=ReviewTaskState.REVIEWING,
            terminal_state=ReviewTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return ReviewTaskState.REVIEWING.value


class TestTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.TEST_TASK)
        self.artifact_map = {
            TestTaskState.TESTING: TestResultArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=TestTaskState.DISPATCHING,
            work_state=TestTaskState.TESTING,
            terminal_state=TestTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return TestTaskState.TESTING.value


class FinalizeTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.FINALIZE_TASK)
        self.artifact_map = {
            FinalizeTaskState.FINALIZING: FinalizeArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=FinalizeTaskState.DISPATCHING,
            work_state=FinalizeTaskState.FINALIZING,
            terminal_state=FinalizeTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return FinalizeTaskState.FINALIZING.value


class CreateSpecTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_SPEC)
        self.artifact_map = {
            CreateSpecState.DRAFTING_SPEC: EngineeringSpec,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=CreateSpecState.DISPATCHING,
            work_state=CreateSpecState.DRAFTING_SPEC,
            terminal_state=CreateSpecState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return CreateSpecState.DRAFTING_SPEC.value


class CreateTasksTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_TASKS_FROM_SPEC)
        self.artifact_map = {
            CreateTasksState.DRAFTING_TASKS: TaskCreationArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=CreateTasksState.DISPATCHING,
            work_state=CreateTasksState.DRAFTING_TASKS,
            terminal_state=CreateTasksState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return CreateTasksState.DRAFTING_TASKS.value
