"""
Pydantic models for structured work artifacts.
"""

from pydantic import BaseModel, Field


class RequirementsArtifact(BaseModel):
    """
    Structured data artifact for the requirements gathering phase.
    """
    
    task_id: str = Field(..., description="The unique identifier of the task")
    task_summary: str = Field(..., description="A brief summary of the task")
    task_description: str = Field(..., description="Detailed description of the task requirements")
    acceptance_criteria: list[str] = Field(..., description="List of criteria that must be met for task completion")
    task_source: str = Field(..., description="The source of the task (jira, linear, local)")
    additional_context: dict = Field(default_factory=dict, description="Any additional context or metadata from the task source")


class GitSetupArtifact(BaseModel):
    """
    Structured data artifact for the git_setup phase.
    """

    branch_name: str = Field(..., description="The name of the git branch created or used.")
    branch_status: str = Field(..., description="The status of the branch, e.g., 'clean'.")
    ready_for_work: bool = Field(..., description="Confirmation that the branch is ready for development.")


class TestResult(BaseModel):
    """Structured data for a single test execution."""

    command_run: str
    exit_code: int
    full_output: str


class TestingArtifact(BaseModel):
    """Structured artifact for the testing phase."""

    test_results: TestResult


class CodingManifest(BaseModel):
    """Structured artifact for the developer completion manifest."""

    implementation_summary: str
    execution_steps_completed: list[str]
    testing_notes: str


class FinalizeArtifact(BaseModel):
    """Structured data for the finalize phase artifact."""

    commit_hash: str = Field(..., description="Git commit hash from the final commit")
    pull_request_url: str = Field(..., description="URL of the created pull request")


class StrategyArtifact(BaseModel):
    """Structured artifact for the strategy planning phase."""

    high_level_strategy: str = Field(..., description="Overall approach and strategic decisions for implementation")
    key_components: list[str] = Field(..., description="List of major components or modules to be implemented")
    architectural_decisions: str = Field(..., description="Key architectural choices and rationale")
    risk_analysis: str = Field(..., description="Potential risks and mitigation strategies")


class FileBreakdownItem(BaseModel):
    """Individual file change in the solution design."""

    file_path: str = Field(..., description="Path to the file to be modified/created")
    action: str = Field(..., description="One of: 'create', 'modify', or 'delete'")
    change_summary: str = Field(..., description="Detailed description of what changes will be made")


class SolutionDesignArtifact(BaseModel):
    """Structured artifact for the solution design phase."""

    approved_strategy_summary: str = Field(..., description="Brief summary of the approved strategy")
    detailed_design: str = Field(..., description="Comprehensive technical design based on the strategy")
    file_breakdown: list[FileBreakdownItem] = Field(..., description="List of files to be modified with details")
    dependencies: list[str] = Field(default_factory=list, description="List of external dependencies or libraries needed")


class FileModification(BaseModel):
    """Individual file modification in the execution plan."""

    path: str = Field(..., description="Path to the file")
    action: str = Field(..., description="create|modify|delete")
    description: str = Field(..., description="What changes to make")


class ExecutionPlanArtifact(BaseModel):
    """Structured artifact for the execution plan phase."""

    implementation_steps: list[str] = Field(..., description="Ordered list of implementation steps")
    file_modifications: list[FileModification] = Field(..., description="Files that will be created or modified")
    testing_strategy: str = Field(..., description="Testing approach and validation steps")
    success_criteria: list[str] = Field(..., description="Criteria for determining successful completion")


class ScaffoldingManifest(BaseModel):
    """Structured artifact for the scaffolding phase."""

    files_scaffolded: list[str] = Field(..., description="List of files that were scaffolded with TODO comments")
    todo_items_generated: int = Field(..., description="Total number of TODO items generated")
    execution_steps_processed: list[str] = Field(..., description="List of execution plan steps that were processed")
