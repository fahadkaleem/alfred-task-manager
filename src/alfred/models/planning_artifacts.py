"""Simplified discovery artifacts for reduced cognitive load."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from alfred.models.schemas import Task


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ContextDiscoveryArtifact(BaseModel):
    """Simplified discovery artifact focusing on essentials."""

    # What we found (markdown formatted for readability)
    findings: str = Field(description="Markdown-formatted discovery findings")

    # Questions that need answers
    questions: List[str] = Field(description="Simple list of questions for clarification", default_factory=list)

    # Files that will be touched
    files_to_modify: List[str] = Field(description="List of files that need changes", default_factory=list)

    # Complexity assessment
    complexity: ComplexityLevel = Field(description="Overall complexity: LOW, MEDIUM, or HIGH", default=ComplexityLevel.MEDIUM)

    # Context bundle for implementation (free-form)
    implementation_context: Dict[str, Any] = Field(description="Any context needed for implementation", default_factory=dict)

    @field_validator("questions")
    @classmethod
    def questions_end_with_questionmark(cls, v):
        for q in v:
            if not q.strip().endswith("?"):
                raise ValueError(f'Question must end with "?": {q}')
        return v

    @field_validator("findings")
    @classmethod
    def findings_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Findings cannot be empty")
        return v


class ClarificationArtifact(BaseModel):
    """Simplified clarification results."""

    # Q&A in markdown format
    clarification_dialogue: str = Field(description="Markdown-formatted Q&A dialogue")

    # Key decisions made
    decisions: List[str] = Field(description="List of decisions made during clarification", default_factory=list)

    # Any new constraints discovered
    additional_constraints: List[str] = Field(description="New constraints or requirements discovered", default_factory=list)


class ContractDesignArtifact(BaseModel):
    """Simplified contracts/interface design."""

    # Interface design in markdown
    interface_design: str = Field(description="Markdown-formatted interface specifications")

    # Key APIs/contracts defined
    contracts_defined: List[str] = Field(description="List of main contracts/interfaces defined", default_factory=list)

    # Any additional notes
    design_notes: List[str] = Field(description="Important design decisions or notes", default_factory=list)


class SubtaskScope(BaseModel):
    """Optional minimal structure for complex subtasks."""

    files: List[str] = Field(default_factory=list, description="Files this subtask will modify or create")
    depends_on_subtasks: List[str] = Field(default_factory=list, description="Other subtask IDs this depends on")


class Subtask(BaseModel):
    """Structured subtask with ID and description."""

    subtask_id: str = Field(..., description="Unique identifier for the subtask (e.g., 'subtask-1', 'ST-001')")
    description: str = Field(..., description="Structured description using markdown format with Goal, Location, Approach, and Verify sections")
    scope: Optional[SubtaskScope] = Field(default=None, description="Optional scope information for complex tasks")


class ImplementationPlanArtifact(BaseModel):
    """Implementation plan with structured subtasks."""

    # Implementation plan in markdown
    implementation_plan: str = Field(description="Markdown-formatted implementation steps")

    # List of structured subtasks
    subtasks: List[Subtask] = Field(description="List of structured subtasks with IDs", default_factory=list)

    # Any risks or concerns
    risks: List[str] = Field(description="Potential risks or concerns", default_factory=list)


class ValidationArtifact(BaseModel):
    """Simplified validation results."""

    # Validation summary in markdown
    validation_summary: str = Field(description="Markdown-formatted validation results")

    # Checklist of validations performed
    validations_performed: List[str] = Field(description="List of validations performed", default_factory=list)

    # Any issues found
    issues_found: List[str] = Field(description="List of issues or concerns found", default_factory=list)

    # Ready for implementation?
    ready_for_implementation: bool = Field(description="Whether the plan is ready for implementation", default=True)


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
    
    def validate_against_plan(self, planned_subtasks: List[str]) -> Optional[str]:
        """Validate completed subtasks against the original plan.
        
        Args:
            planned_subtasks: List of subtask IDs from the original execution plan
            
        Returns:
            None if validation passes, error message if validation fails
        """
        planned_set = set(planned_subtasks)
        completed_set = set(self.completed_subtasks)
        
        missing = planned_set - completed_set
        extra = completed_set - planned_set
        
        if missing:
            return f"Implementation incomplete. Missing subtasks: {sorted(missing)}. Expected all subtasks to be completed: {sorted(planned_subtasks)}"
        
        if extra:
            # Extra subtasks are a warning, not an error
            pass
            
        return None


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
