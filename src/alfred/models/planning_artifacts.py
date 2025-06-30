# src/alfred/models/planning_artifacts.py
from pydantic import BaseModel, Field
from typing import List, Dict, Literal
from .schemas import Subtask, Task


class ContextAnalysisArtifact(BaseModel):
    context_summary: str
    affected_files: List[str]
    questions_for_developer: List[str]


class StrategyArtifact(BaseModel):
    high_level_strategy: str
    key_components: List[str]
    new_dependencies: List[str] = Field(default_factory=list)
    risk_analysis: str | None = None


class FileChange(BaseModel):
    file_path: str = Field(description="The full path to the file that will be created or modified.")
    change_summary: str = Field(description="A detailed description of the new content or changes for this file.")
    operation: Literal["CREATE", "MODIFY"] = Field(description="Whether the file will be created or modified.")


class DesignArtifact(BaseModel):
    design_summary: str = Field(description="A high-level summary of the implementation design.")
    file_breakdown: List[FileChange] = Field(description="A file-by-file breakdown of all required changes.")


# The Execution Plan is a collection of Subtasks
class ExecutionPlanArtifact(BaseModel):
    subtasks: List[Subtask] = Field(description="The ordered list of Subtasks that form the execution plan")


class GitStatusArtifact(BaseModel):
    is_clean: bool
    current_branch: str
    uncommitted_files: List[str]


class BranchCreationArtifact(BaseModel):
    branch_name: str
    success: bool
    details: str


class ImplementationManifestArtifact(BaseModel):
    summary: str
    completed_subtasks: List[str]
    testing_notes: str


class ReviewArtifact(BaseModel):
    summary: str
    approved: bool
    feedback: List[str]


class TestResultArtifact(BaseModel):
    command: str
    exit_code: int
    output: str


class FinalizeArtifact(BaseModel):
    commit_hash: str
    pr_url: str


# Pre-planning Phase Artifacts
class PRDInputArtifact(BaseModel):
    prd_content: str = Field(description="The raw text or content of the Product Requirements Document.")


class TaskCreationArtifact(BaseModel):
    tasks: List[Task] = Field(description="A list of all generated Task objects.")
