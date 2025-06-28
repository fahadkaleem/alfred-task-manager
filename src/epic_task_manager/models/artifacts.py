# File: src/epic_task_manager/models/artifacts.py

# Standard library imports
from datetime import datetime

# Third-party imports
from pydantic import BaseModel, Field, field_validator

# Local application imports
from epic_task_manager.constants import DEFAULT_AI_MODEL, DEFAULT_ARTIFACT_VERSION

from .enums import ArtifactStatus, FileAction, TaskPhase


class ArtifactMetadata(BaseModel):
    """Represents the YAML front matter in an artifact file"""

    task_id: str = Field(..., pattern=r"^[A-Z]+-\d+$", description="Jira task ID format")
    phase: TaskPhase
    status: ArtifactStatus
    version: str = Field(default=DEFAULT_ARTIFACT_VERSION, pattern=r"^\d+\.\d+$")
    ai_model: str = Field(default=DEFAULT_AI_MODEL)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("task_id")
    @classmethod
    def validate_task_id_format(cls, v: str) -> str:
        """Ensure task ID follows Jira format"""
        if not v or not v.strip():
            raise ValueError("Task ID cannot be empty")
        return v.upper()

    class Config:
        use_enum_values = True


class FileChange(BaseModel):
    """Details a single file to be changed"""

    file_path: str = Field(..., min_length=1, description="Path to file")
    action: FileAction
    change_summary: str = Field(..., min_length=10, max_length=500)

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Ensure file path is not empty or just whitespace"""
        if not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()

    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, v) -> str:
        """Accept case-insensitive action values and normalize to uppercase"""
        if isinstance(v, str):
            # Handle common lowercase variations
            upper_v = v.upper()
            if upper_v in ["CREATE", "MODIFY", "DELETE"]:
                return upper_v
        return v  # Let pydantic handle invalid values


class RequirementsArtifact(BaseModel):
    """Structured data for the requirements phase."""

    metadata: ArtifactMetadata
    task_summary: str
    task_description: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class GitSetupArtifact(BaseModel):
    """Structured data for the git_setup phase."""

    metadata: ArtifactMetadata
    branch_name: str = Field(..., description="The name of the git branch")
    branch_created: bool = Field(..., description="Whether a new branch was created")
    branch_status: str = Field(..., description="Current git status of the branch")
    ready_for_work: bool = Field(..., description="Confirmation that branch is ready for development")


class PlanningArtifact(BaseModel):
    """Structured data for the planning phase artifact."""

    metadata: ArtifactMetadata
    scope_verification: str
    technical_approach: str
    file_breakdown: list[FileChange] = Field(default_factory=list)


class StrategyArtifact(BaseModel):
    """Structured data for the planning strategy phase."""

    metadata: ArtifactMetadata
    high_level_strategy: str = Field(..., description="Overall approach and strategic decisions")
    key_components: list[str] = Field(..., description="Major components or modules to be implemented")
    architectural_decisions: str = Field(..., description="Key architectural choices and rationale")
    risk_analysis: str = Field(..., description="Potential risks and mitigation strategies")


class SolutionDesignArtifact(BaseModel):
    """Structured data for the planning solution design phase."""

    metadata: ArtifactMetadata
    approved_strategy_summary: str = Field(..., description="Brief summary of approved strategy")
    detailed_design: str = Field(..., description="Detailed technical design based on strategy")
    file_breakdown: list[FileChange] = Field(..., description="Comprehensive file-by-file breakdown")
    dependencies: list[str] = Field(default_factory=list, description="External dependencies or libraries needed")


class ExecutionStep(BaseModel):
    """A single execution step in the implementation plan."""

    prompt_id: str = Field(..., pattern=r"^STEP-\d{3,}$", description="Unique ID for this execution step")
    prompt_text: str = Field(..., description="The specific task instruction")
    target_files: list[str] = Field(..., description="Files this step will affect")
    depends_on: list[str] = Field(default_factory=list, description="IDs of execution steps this depends on")


class ExecutionPlanArtifact(BaseModel):
    """Structured data for the planning execution plan generation phase."""

    metadata: ArtifactMetadata
    approved_design_summary: str = Field(..., description="Brief summary of approved solution design")
    execution_steps: list[ExecutionStep] = Field(..., description="Machine-executable list of execution steps")
    execution_order_notes: str = Field(..., description="Notes on optimal execution order")


class ScaffoldingArtifact(BaseModel):
    """Structured data for the scaffolding phase artifact."""

    metadata: ArtifactMetadata
    files_scaffolded: list[str] = Field(default_factory=list, description="List of file paths that have been scaffolded with TODO comments.")


class CodingArtifact(BaseModel):
    """Lightweight completion manifest for the coding phase."""

    metadata: ArtifactMetadata
    implementation_summary: str
    execution_steps_completed: list[str] = Field(default_factory=list, description="List of execution step IDs that were completed during implementation")
    testing_notes: str
    acceptance_criteria_met: list[str] = Field(
        default_factory=list,
        description="List of how each acceptance criterion was satisfied",
    )


class TestResults(BaseModel):
    """Structured test execution results."""

    command_run: str = Field(..., description="The test command that was executed")
    exit_code: int = Field(..., description="Exit code from test execution (0 = success)")
    full_output: str = Field(..., description="Complete output from test execution")


class TestingArtifact(BaseModel):
    """Structured data for the testing phase artifact."""

    metadata: ArtifactMetadata
    test_results: TestResults


class FinalizeArtifact(BaseModel):
    """Structured data for the finalize phase artifact."""

    metadata: ArtifactMetadata
    commit_hash: str = Field(..., description="Git commit hash from the final commit")
    pull_request_url: str = Field(..., description="URL of the created pull request")


class TaskSummaryResponse(BaseModel):
    """Response model for the get_task_summary tool."""

    task_id: str
    current_state: str
    artifact_status: str


class InspectArchivedArtifactResponse(BaseModel):
    """Response model for the inspect_archived_artifact tool."""

    task_id: str
    phase_name: str
    artifact_content: str
