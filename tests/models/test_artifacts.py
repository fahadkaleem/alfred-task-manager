"""
Comprehensive tests for Epic Task Manager Artifact Models
Tests Pydantic models for validation, serialization, and business logic.
"""

from datetime import datetime

from pydantic import ValidationError
import pytest

from epic_task_manager.constants import DEFAULT_AI_MODEL, DEFAULT_ARTIFACT_VERSION
from epic_task_manager.models.artifacts import (
    ArtifactMetadata,
    CodingArtifact,
    FileChange,
    FinalizeArtifact,
    InspectArchivedArtifactResponse,
    PlanningArtifact,
    RequirementsArtifact,
    TaskSummaryResponse,
    TestingArtifact,
    TestResults,
)
from epic_task_manager.models.enums import ArtifactStatus, FileAction, TaskPhase


class TestArtifactMetadata:
    """Test ArtifactMetadata validation and behavior."""

    def test_create_metadata_with_valid_data(self):
        """Test creating metadata with valid data."""
        metadata = ArtifactMetadata(task_id="TEST-123", phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING)

        assert metadata.task_id == "TEST-123"
        assert metadata.phase == TaskPhase.GATHER_REQUIREMENTS
        assert metadata.status == ArtifactStatus.WORKING
        assert metadata.version == DEFAULT_ARTIFACT_VERSION
        assert metadata.ai_model == DEFAULT_AI_MODEL
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)

    def test_metadata_uses_defaults(self):
        """Test metadata uses correct default values."""
        metadata = ArtifactMetadata(task_id="PROJ-456", phase=TaskPhase.PLANNING, status=ArtifactStatus.WORKING)

        assert metadata.version == "1.0"
        assert metadata.ai_model == "claude-3.5-sonnet"

    @pytest.mark.parametrize("invalid_task_id", ["", "   "], ids=["empty", "whitespace"])
    def test_task_id_validation_failures(self, invalid_task_id):
        """Test task ID validation rejects empty/whitespace."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            ArtifactMetadata(task_id=invalid_task_id, phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING)

    @pytest.mark.parametrize("invalid_task_id", ["TEST123", "TEST-", "-123", "test_123"], ids=["no_dash", "no_number", "no_prefix", "underscore"])
    def test_task_id_pattern_failures(self, invalid_task_id):
        """Test task ID validation rejects invalid patterns."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            ArtifactMetadata(task_id=invalid_task_id, phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING)

    @pytest.mark.parametrize(
        "valid_task_id,expected_normalized",
        [
            ("TEST-123", "TEST-123"),
            ("PROJ-456", "PROJ-456"),
            ("EPIC-789", "EPIC-789"),
            ("BUG-1", "BUG-1"),
        ],
        ids=["lowercase", "mixed_case", "uppercase", "single_digit"],
    )
    def test_task_id_normalization(self, valid_task_id, expected_normalized):
        """Test task ID is normalized to uppercase."""
        metadata = ArtifactMetadata(task_id=valid_task_id, phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING)

        assert metadata.task_id == expected_normalized

    @pytest.mark.parametrize("invalid_version", ["1", "1.0.0", "v1.0", "1.0-alpha", "invalid"], ids=["no_minor", "three_parts", "prefix", "suffix", "text"])
    def test_version_validation_failures(self, invalid_version):
        """Test version validation rejects invalid formats."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            ArtifactMetadata(task_id="TEST-123", phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING, version=invalid_version)

    @pytest.mark.parametrize("valid_version", ["1.0", "2.1", "10.5", "0.1"], ids=["basic", "increment", "double_digit", "minor_increment"])
    def test_version_validation_success(self, valid_version):
        """Test version validation accepts valid formats."""
        metadata = ArtifactMetadata(task_id="TEST-123", phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING, version=valid_version)

        assert metadata.version == valid_version

    def test_metadata_serialization(self):
        """Test metadata can be serialized to dict."""
        metadata = ArtifactMetadata(task_id="TEST-123", phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING)

        data = metadata.model_dump()

        assert data["task_id"] == "TEST-123"
        assert data["phase"] == "gatherrequirements"  # Enum value
        assert data["status"] == "working"  # Enum value
        assert "created_at" in data
        assert "updated_at" in data


class TestFileChange:
    """Test FileChange model validation."""

    def test_create_file_change_with_valid_data(self):
        """Test creating file change with valid data."""
        file_change = FileChange(file_path="src/models/user.py", action=FileAction.MODIFY, change_summary="Add email validation to User model")

        assert file_change.file_path == "src/models/user.py"
        assert file_change.action == FileAction.MODIFY
        assert file_change.change_summary == "Add email validation to User model"

    @pytest.mark.parametrize("action", [FileAction.CREATE, FileAction.MODIFY, FileAction.DELETE], ids=["create", "modify", "delete"])
    def test_file_change_action_types(self, action):
        """Test file change supports all action types."""
        file_change = FileChange(file_path="test/file.py", action=action, change_summary="Test action type validation with sufficient length")

        assert file_change.action == action

    def test_file_path_validation_empty_string(self):
        """Test file path validation rejects empty string."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            FileChange(file_path="", action=FileAction.CREATE, change_summary="Valid change summary with enough characters")

    @pytest.mark.parametrize("invalid_path", ["   ", "\t\n"], ids=["spaces", "whitespace"])
    def test_file_path_validation_whitespace_failures(self, invalid_path):
        """Test file path validation rejects whitespace-only paths."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            FileChange(file_path=invalid_path, action=FileAction.CREATE, change_summary="Valid change summary with enough characters")

    def test_file_path_whitespace_trimming(self):
        """Test file path whitespace is trimmed."""
        file_change = FileChange(file_path="  src/file.py  ", action=FileAction.CREATE, change_summary="Test whitespace trimming functionality")

        assert file_change.file_path == "src/file.py"

    @pytest.mark.parametrize(
        "invalid_summary,min_length,max_length",
        [
            ("short", 10, 500),
            ("a" * 501, 10, 500),
        ],
        ids=["too_short", "too_long"],
    )
    def test_change_summary_length_validation(self, invalid_summary, min_length, max_length):
        """Test change summary length validation."""
        with pytest.raises(ValidationError):
            FileChange(file_path="src/file.py", action=FileAction.CREATE, change_summary=invalid_summary)

    def test_change_summary_valid_length(self):
        """Test change summary accepts valid length."""
        summary = "This is a valid change summary with appropriate length for testing"

        file_change = FileChange(file_path="src/file.py", action=FileAction.CREATE, change_summary=summary)

        assert file_change.change_summary == summary

    def test_action_case_insensitive(self):
        """Test that action field accepts lowercase values and normalizes them."""
        # Test lowercase values
        file_change_create = FileChange(file_path="test_file.py", action="create", change_summary="This is a valid change summary that meets the minimum length requirement.")
        assert file_change_create.action == FileAction.CREATE

        file_change_modify = FileChange(file_path="test_file.py", action="modify", change_summary="This is a valid change summary that meets the minimum length requirement.")
        assert file_change_modify.action == FileAction.MODIFY

        file_change_delete = FileChange(file_path="test_file.py", action="delete", change_summary="This is a valid change summary that meets the minimum length requirement.")
        assert file_change_delete.action == FileAction.DELETE

        # Test mixed case
        file_change_mixed = FileChange(file_path="test_file.py", action="Create", change_summary="This is a valid change summary that meets the minimum length requirement.")
        assert file_change_mixed.action == FileAction.CREATE


class TestRequirementsArtifact:
    """Test RequirementsArtifact model validation."""

    @pytest.fixture
    def valid_metadata(self):
        """Valid metadata for testing."""
        return ArtifactMetadata(task_id="TEST-123", phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING)

    def test_create_requirements_artifact(self, valid_metadata):
        """Test creating requirements artifact with valid data."""
        artifact = RequirementsArtifact(
            metadata=valid_metadata,
            task_summary="Implement user authentication",
            task_description="Add OAuth2 login functionality with Google provider",
            acceptance_criteria=["Users can log in with Google account", "Session persists across browser restarts", "Invalid credentials show appropriate error"],
        )

        assert artifact.metadata == valid_metadata
        assert artifact.task_summary == "Implement user authentication"
        assert artifact.task_description == "Add OAuth2 login functionality with Google provider"
        assert len(artifact.acceptance_criteria) == 3

    def test_requirements_artifact_empty_acceptance_criteria(self, valid_metadata):
        """Test requirements artifact with empty acceptance criteria."""
        artifact = RequirementsArtifact(metadata=valid_metadata, task_summary="Test task", task_description="Test description")

        assert artifact.acceptance_criteria == []

    def test_requirements_artifact_serialization(self, valid_metadata):
        """Test requirements artifact can be serialized."""
        artifact = RequirementsArtifact(metadata=valid_metadata, task_summary="Test task", task_description="Test description", acceptance_criteria=["Criterion 1", "Criterion 2"])

        data = artifact.model_dump()

        assert "metadata" in data
        assert data["task_summary"] == "Test task"
        assert data["task_description"] == "Test description"
        assert data["acceptance_criteria"] == ["Criterion 1", "Criterion 2"]


class TestPlanningArtifact:
    """Test PlanningArtifact model validation."""

    @pytest.fixture
    def valid_metadata(self):
        """Valid metadata for testing."""
        return ArtifactMetadata(task_id="TEST-456", phase=TaskPhase.PLANNING, status=ArtifactStatus.WORKING)

    @pytest.fixture
    def sample_file_changes(self):
        """Sample file changes for testing."""
        return [
            FileChange(file_path="src/auth/oauth.py", action=FileAction.CREATE, change_summary="Create OAuth2 authentication handler"),
            FileChange(file_path="src/models/user.py", action=FileAction.MODIFY, change_summary="Add OAuth fields to User model"),
        ]

    def test_create_planning_artifact(self, valid_metadata, sample_file_changes):
        """Test creating planning artifact with valid data."""
        artifact = PlanningArtifact(
            metadata=valid_metadata, scope_verification="Requirements reviewed and confirmed", technical_approach="Use OAuth2 with Google provider", file_breakdown=sample_file_changes
        )

        assert artifact.metadata == valid_metadata
        assert artifact.scope_verification == "Requirements reviewed and confirmed"
        assert artifact.technical_approach == "Use OAuth2 with Google provider"
        assert len(artifact.file_breakdown) == 2

    def test_planning_artifact_empty_file_breakdown(self, valid_metadata):
        """Test planning artifact with empty file breakdown."""
        artifact = PlanningArtifact(metadata=valid_metadata, scope_verification="Scope verified", technical_approach="Technical approach defined")

        assert artifact.file_breakdown == []


class TestCodingArtifact:
    """Test CodingArtifact model validation."""

    @pytest.fixture
    def valid_metadata(self):
        """Valid metadata for testing."""
        return ArtifactMetadata(task_id="TEST-789", phase=TaskPhase.CODING, status=ArtifactStatus.WORKING)

    @pytest.fixture
    def sample_execution_prompts(self):
        """Sample execution prompt IDs for testing."""
        return ["EXEC-001", "EXEC-002", "EXEC-003"]

    def test_create_coding_artifact(self, valid_metadata, sample_execution_prompts):
        """Test creating coding artifact with valid data."""
        artifact = CodingArtifact(
            metadata=valid_metadata,
            implementation_summary="Implemented OAuth2 authentication",
            execution_steps_completed=sample_execution_prompts,
            testing_notes="Unit tests added for authentication flow",
            acceptance_criteria_met=["OAuth login works", "Sessions persist"],
        )

        assert artifact.metadata == valid_metadata
        assert artifact.implementation_summary == "Implemented OAuth2 authentication"
        assert len(artifact.execution_steps_completed) == 3
        assert "EXEC-001" in artifact.execution_steps_completed
        assert artifact.testing_notes == "Unit tests added for authentication flow"
        assert len(artifact.acceptance_criteria_met) == 2

    def test_coding_artifact_empty_lists(self, valid_metadata):
        """Test coding artifact with empty lists."""
        artifact = CodingArtifact(metadata=valid_metadata, implementation_summary="Basic implementation", execution_steps_completed=[], testing_notes="No tests yet")

        assert artifact.execution_steps_completed == []
        assert artifact.acceptance_criteria_met == []

    def test_execution_steps_completed_validation(self, valid_metadata):
        """Test execution_steps_completed field validation."""
        artifact = CodingArtifact(metadata=valid_metadata, implementation_summary="Test implementation", execution_steps_completed=["STEP-001", "STEP-002"], testing_notes="Test notes")

        assert isinstance(artifact.execution_steps_completed, list)
        assert all(isinstance(step_id, str) for step_id in artifact.execution_steps_completed)

    def test_coding_artifact_serialization(self, valid_metadata):
        """Test coding artifact serialization and deserialization."""
        original = CodingArtifact(
            metadata=valid_metadata, implementation_summary="Test implementation", execution_steps_completed=["STEP-001"], testing_notes="Test notes", acceptance_criteria_met=["Criteria met"]
        )

        # Test serialization
        artifact_dict = original.model_dump()
        assert "execution_steps_completed" in artifact_dict
        assert artifact_dict["execution_steps_completed"] == ["STEP-001"]

        # Test deserialization
        reconstructed = CodingArtifact(**artifact_dict)
        assert reconstructed.execution_steps_completed == original.execution_steps_completed


class TestTestResults:
    """Test TestResults model validation."""

    def test_create_test_results_success(self):
        """Test creating test results for successful tests."""
        results = TestResults(command_run="pytest tests/", exit_code=0, full_output="================================ 5 passed in 2.34s ================================")

        assert results.command_run == "pytest tests/"
        assert results.exit_code == 0
        assert "5 passed" in results.full_output

    def test_create_test_results_failure(self):
        """Test creating test results for failed tests."""
        results = TestResults(command_run="pytest tests/test_auth.py", exit_code=1, full_output="FAILED tests/test_auth.py::test_invalid_token - AssertionError")

        assert results.command_run == "pytest tests/test_auth.py"
        assert results.exit_code == 1
        assert "FAILED" in results.full_output


class TestTestingArtifact:
    """Test TestingArtifact model validation."""

    @pytest.fixture
    def valid_metadata(self):
        """Valid metadata for testing."""
        return ArtifactMetadata(task_id="TEST-999", phase=TaskPhase.TESTING, status=ArtifactStatus.WORKING)

    @pytest.fixture
    def sample_test_results(self):
        """Sample test results for testing."""
        return TestResults(command_run="pytest tests/", exit_code=0, full_output="All tests passed successfully")

    def test_create_testing_artifact(self, valid_metadata, sample_test_results):
        """Test creating testing artifact with valid data."""
        artifact = TestingArtifact(metadata=valid_metadata, test_results=sample_test_results)

        assert artifact.metadata == valid_metadata
        assert artifact.test_results == sample_test_results


class TestFinalizeArtifact:
    """Test FinalizeArtifact model validation."""

    @pytest.fixture
    def valid_metadata(self):
        """Valid metadata for testing."""
        return ArtifactMetadata(task_id="TEST-111", phase=TaskPhase.FINALIZE, status=ArtifactStatus.WORKING)

    def test_create_finalize_artifact(self, valid_metadata):
        """Test creating finalize artifact with valid data."""
        artifact = FinalizeArtifact(metadata=valid_metadata, commit_hash="abc123def456", pull_request_url="https://github.com/org/repo/pull/123")

        assert artifact.metadata == valid_metadata
        assert artifact.commit_hash == "abc123def456"
        assert artifact.pull_request_url == "https://github.com/org/repo/pull/123"


class TestTaskSummaryResponse:
    """Test TaskSummaryResponse model validation."""

    def test_create_task_summary_response(self):
        """Test creating task summary response with valid data."""
        response = TaskSummaryResponse(task_id="TEST-222", current_state="planning_working", artifact_status="working")

        assert response.task_id == "TEST-222"
        assert response.current_state == "planning_working"
        assert response.artifact_status == "working"


class TestInspectArchivedArtifactResponse:
    """Test InspectArchivedArtifactResponse model validation."""

    def test_create_inspect_response(self):
        """Test creating inspect archived artifact response with valid data."""
        response = InspectArchivedArtifactResponse(task_id="TEST-333", phase_name="gatherrequirements", artifact_content="# Requirements Artifact\n\nTask: TEST-333")

        assert response.task_id == "TEST-333"
        assert response.phase_name == "gatherrequirements"
        assert "Task: TEST-333" in response.artifact_content


class TestArtifactModelIntegration:
    """Test integration between different artifact models."""

    def test_metadata_consistency_across_artifacts(self):
        """Test metadata is consistent across different artifact types."""
        task_id = "INTEGRATION-1"

        # Create metadata for each phase
        claim_metadata = ArtifactMetadata(task_id=task_id, phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.WORKING)

        planning_metadata = ArtifactMetadata(task_id=task_id, phase=TaskPhase.PLANNING, status=ArtifactStatus.WORKING)

        # Both should have same task_id but different phases
        assert claim_metadata.task_id == planning_metadata.task_id
        assert claim_metadata.phase != planning_metadata.phase

    def test_artifact_workflow_progression(self):
        """Test artifacts can represent workflow progression."""
        task_id = "WORKFLOW-1"

        # Claim task artifact
        requirements_artifact = RequirementsArtifact(
            metadata=ArtifactMetadata(task_id=task_id, phase=TaskPhase.GATHER_REQUIREMENTS, status=ArtifactStatus.APPROVED),
            task_summary="Test workflow",
            task_description="Test description",
            acceptance_criteria=["Criterion 1"],
        )

        # Planning artifact using info from requirements
        planning_artifact = PlanningArtifact(
            metadata=ArtifactMetadata(task_id=task_id, phase=TaskPhase.PLANNING, status=ArtifactStatus.WORKING),
            scope_verification="Based on requirements requirements",
            technical_approach="Implementation approach",
            file_breakdown=[],
        )

        # Verify workflow consistency
        assert requirements_artifact.metadata.task_id == planning_artifact.metadata.task_id
        assert requirements_artifact.metadata.status == ArtifactStatus.APPROVED
        assert planning_artifact.metadata.status == ArtifactStatus.WORKING

    @pytest.mark.parametrize(
        "phase,artifact_class",
        [
            (TaskPhase.GATHER_REQUIREMENTS, RequirementsArtifact),
            (TaskPhase.PLANNING, PlanningArtifact),
            (TaskPhase.CODING, CodingArtifact),
            (TaskPhase.TESTING, TestingArtifact),
            (TaskPhase.FINALIZE, FinalizeArtifact),
        ],
        ids=["claim", "planning", "coding", "testing", "finalize"],
    )
    def test_all_artifacts_have_metadata(self, phase, artifact_class):
        """Test all artifact types include metadata field."""
        # Get the field info for the artifact class
        fields = artifact_class.model_fields

        assert "metadata" in fields
        assert fields["metadata"].annotation == ArtifactMetadata
