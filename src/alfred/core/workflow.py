# src/alfred/core/workflow.py
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from alfred.constants import ToolName, Triggers
from alfred.core.state_machine_builder import workflow_builder
from alfred.models.planning_artifacts import (
    BranchCreationArtifact,
    FinalizeArtifact,
    GitStatusArtifact,
    ImplementationManifestArtifact,
    PRDInputArtifact,
    ReviewArtifact,
    TaskCreationArtifact,
    TestResultArtifact,
)
from alfred.models.engineering_spec import EngineeringSpec


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
    """
    Stateless base class for workflow tools.

    No longer holds machine instance or state. Contains only static configuration
    and utility methods for workflow management.
    """

    def __init__(self, task_id: str, tool_name: str):
        self.task_id = task_id
        self.tool_name = tool_name
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}

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


class StartTaskTool(BaseWorkflowTool):
    """Re-architected StartTaskTool with a streamlined state machine."""

    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.START_TASK)
        self.artifact_map = {
            StartTaskState.AWAITING_GIT_STATUS: GitStatusArtifact,
            StartTaskState.AWAITING_BRANCH_CREATION: BranchCreationArtifact,
        }

    def get_final_work_state(self) -> str:
        return StartTaskState.AWAITING_BRANCH_CREATION.value


class ImplementTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.IMPLEMENT_TASK)
        self.artifact_map = {
            ImplementTaskState.IMPLEMENTING: ImplementationManifestArtifact,
        }

    def get_final_work_state(self) -> str:
        return ImplementTaskState.IMPLEMENTING.value


class ReviewTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.REVIEW_TASK)
        self.artifact_map = {
            ReviewTaskState.REVIEWING: ReviewArtifact,
        }

    def get_final_work_state(self) -> str:
        return ReviewTaskState.REVIEWING.value


class TestTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.TEST_TASK)
        self.artifact_map = {
            TestTaskState.TESTING: TestResultArtifact,
        }

    def get_final_work_state(self) -> str:
        return TestTaskState.TESTING.value


class FinalizeTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.FINALIZE_TASK)
        self.artifact_map = {
            FinalizeTaskState.FINALIZING: FinalizeArtifact,
        }

    def get_final_work_state(self) -> str:
        return FinalizeTaskState.FINALIZING.value


class CreateSpecTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_SPEC)
        self.artifact_map = {
            CreateSpecState.DRAFTING_SPEC: EngineeringSpec,
        }

    def get_final_work_state(self) -> str:
        return CreateSpecState.DRAFTING_SPEC.value


class CreateTasksTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_TASKS_FROM_SPEC)
        self.artifact_map = {
            CreateTasksState.DRAFTING_TASKS: TaskCreationArtifact,
        }

    def get_final_work_state(self) -> str:
        return CreateTasksState.DRAFTING_TASKS.value
