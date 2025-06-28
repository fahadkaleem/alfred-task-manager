"""
Comprehensive tests for Epic Task Manager Custom Exceptions
Tests exception hierarchy, initialization, and context preservation.
"""

import pytest

from epic_task_manager.exceptions import (
    ArtifactError,
    ArtifactNotFoundError,
    EpicTaskManagerError,
    InitializationError,
    InvalidArtifactFormatError,
    PhaseTransitionError,
    StateFileError,
    StateTransitionError,
    TaskNotFoundError,
)


class TestEpicTaskManagerError:
    """Test base EpicTaskManagerError class."""

    def test_create_base_exception_with_message_only(self):
        """Test creating base exception with message only."""
        error = EpicTaskManagerError("Test error message")

        assert str(error) == "Test error message"
        assert error.task_id is None

    def test_create_base_exception_with_task_id(self):
        """Test creating base exception with task ID."""
        error = EpicTaskManagerError("Test error message", task_id="TEST-123")

        assert str(error) == "Test error message"
        assert error.task_id == "TEST-123"

    def test_base_exception_inheritance(self):
        """Test base exception inherits from Exception."""
        error = EpicTaskManagerError("Test message")

        assert isinstance(error, Exception)
        assert isinstance(error, EpicTaskManagerError)

    def test_base_exception_can_be_raised(self):
        """Test base exception can be raised and caught."""
        with pytest.raises(EpicTaskManagerError, match="Test error"):
            raise EpicTaskManagerError("Test error")

    def test_base_exception_with_empty_message(self):
        """Test base exception with empty message."""
        error = EpicTaskManagerError("")

        assert str(error) == ""
        assert error.task_id is None

    def test_base_exception_with_none_task_id(self):
        """Test base exception with explicit None task_id."""
        error = EpicTaskManagerError("Test message", task_id=None)

        assert error.task_id is None

    def test_base_exception_task_id_attribute_accessible(self):
        """Test task_id attribute is accessible after creation."""
        task_id = "TASK-456"
        error = EpicTaskManagerError("Test message", task_id=task_id)

        # Access task_id attribute
        assert hasattr(error, "task_id")
        assert error.task_id == task_id


class TestSpecificExceptions:
    """Test specific exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            StateFileError,
            InitializationError,
            TaskNotFoundError,
            PhaseTransitionError,
            ArtifactError,
        ],
        ids=["StateFile", "Initialization", "TaskNotFound", "PhaseTransition", "Artifact"],
    )
    def test_exception_inheritance(self, exception_class):
        """Test all specific exceptions inherit from EpicTaskManagerError."""
        error = exception_class("Test message")

        assert isinstance(error, EpicTaskManagerError)
        assert isinstance(error, exception_class)
        assert isinstance(error, Exception)

    @pytest.mark.parametrize(
        "exception_class,message,task_id",
        [
            (StateFileError, "State file error", "TASK-001"),
            (InitializationError, "Init error", "TASK-002"),
            (TaskNotFoundError, "Task not found", "TASK-003"),
            (PhaseTransitionError, "Phase error", "TASK-004"),
            (ArtifactError, "Artifact error", "TASK-005"),
        ],
        ids=["StateFile", "Initialization", "TaskNotFound", "PhaseTransition", "Artifact"],
    )
    def test_exception_initialization(self, exception_class, message, task_id):
        """Test specific exceptions can be initialized with message and task_id."""
        error = exception_class(message, task_id=task_id)

        assert str(error) == message
        assert error.task_id == task_id

    @pytest.mark.parametrize(
        "exception_class",
        [
            StateFileError,
            InitializationError,
            TaskNotFoundError,
            PhaseTransitionError,
            ArtifactError,
        ],
        ids=["StateFile", "Initialization", "TaskNotFound", "PhaseTransition", "Artifact"],
    )
    def test_exception_can_be_raised_and_caught(self, exception_class):
        """Test specific exceptions can be raised and caught."""
        with pytest.raises(exception_class, match="Specific error"):
            raise exception_class("Specific error")

    @pytest.mark.parametrize(
        "exception_class",
        [
            StateFileError,
            InitializationError,
            TaskNotFoundError,
            PhaseTransitionError,
            ArtifactError,
        ],
        ids=["StateFile", "Initialization", "TaskNotFound", "PhaseTransition", "Artifact"],
    )
    def test_exception_caught_as_base_class(self, exception_class):
        """Test specific exceptions can be caught as base exception."""
        with pytest.raises(EpicTaskManagerError):
            raise exception_class("Test error")


class TestStateTransitionError:
    """Test StateTransitionError with additional context."""

    def test_create_state_transition_error_with_context(self):
        """Test creating StateTransitionError with state context."""
        error = StateTransitionError("Invalid transition", current_state="gatherrequirements_working", attempted_transition="advance")

        assert str(error) == "Invalid transition"
        assert error.current_state == "gatherrequirements_working"
        assert error.attempted_transition == "advance"

    def test_state_transition_error_inheritance(self):
        """Test StateTransitionError inherits from EpicTaskManagerError."""
        error = StateTransitionError("Test error", current_state="test_state", attempted_transition="test_transition")

        assert isinstance(error, EpicTaskManagerError)
        assert isinstance(error, StateTransitionError)

    def test_state_transition_error_attributes_accessible(self):
        """Test StateTransitionError attributes are accessible."""
        error = StateTransitionError("Transition error", current_state="planning_devreview", attempted_transition="invalid_action")

        assert hasattr(error, "current_state")
        assert hasattr(error, "attempted_transition")
        assert error.current_state == "planning_devreview"
        assert error.attempted_transition == "invalid_action"

    def test_state_transition_error_can_be_raised(self):
        """Test StateTransitionError can be raised and caught."""
        with pytest.raises(StateTransitionError, match="Cannot transition"):
            raise StateTransitionError("Cannot transition from working to verified", current_state="coding_working", attempted_transition="mark_verified")

    def test_state_transition_error_context_in_exception_handling(self):
        """Test StateTransitionError context is available in exception handling."""
        try:
            raise StateTransitionError("Invalid state change", current_state="testing_aireview", attempted_transition="skip_to_done")
        except StateTransitionError as e:
            assert e.current_state == "testing_aireview"
            assert e.attempted_transition == "skip_to_done"
            assert "Invalid state change" in str(e)

    def test_state_transition_error_with_empty_context(self):
        """Test StateTransitionError with empty context strings."""
        error = StateTransitionError("Test error", current_state="", attempted_transition="")

        assert error.current_state == ""
        assert error.attempted_transition == ""

    @pytest.mark.parametrize(
        "current_state,attempted_transition",
        [
            ("gatherrequirements_working", "advance"),
            ("planning_devreview", "reject"),
            ("coding_verified", "restart"),
            ("testing_aireview", "skip"),
            ("finalize_working", "abort"),
        ],
        ids=["working_advance", "devreview_reject", "verified_restart", "aireview_skip", "working_abort"],
    )
    def test_state_transition_error_various_contexts(self, current_state, attempted_transition):
        """Test StateTransitionError with various state contexts."""
        error = StateTransitionError(f"Cannot {attempted_transition} from {current_state}", current_state=current_state, attempted_transition=attempted_transition)

        assert error.current_state == current_state
        assert error.attempted_transition == attempted_transition
        assert current_state in str(error)
        assert attempted_transition in str(error)


class TestArtifactExceptions:
    """Test artifact-related exceptions."""

    def test_artifact_not_found_error_inheritance(self):
        """Test ArtifactNotFoundError inherits from ArtifactError."""
        error = ArtifactNotFoundError("File not found")

        assert isinstance(error, ArtifactError)
        assert isinstance(error, EpicTaskManagerError)
        assert isinstance(error, ArtifactNotFoundError)

    def test_invalid_artifact_format_error_inheritance(self):
        """Test InvalidArtifactFormatError inherits from ArtifactError."""
        error = InvalidArtifactFormatError("Invalid format")

        assert isinstance(error, ArtifactError)
        assert isinstance(error, EpicTaskManagerError)
        assert isinstance(error, InvalidArtifactFormatError)

    def test_artifact_exceptions_can_be_caught_as_artifact_error(self):
        """Test artifact exceptions can be caught as ArtifactError."""
        with pytest.raises(ArtifactError):
            raise ArtifactNotFoundError("Not found")

        with pytest.raises(ArtifactError):
            raise InvalidArtifactFormatError("Invalid format")

    def test_artifact_exceptions_with_task_id(self):
        """Test artifact exceptions with task_id context."""
        task_id = "ARTIFACT-TEST"

        not_found_error = ArtifactNotFoundError("Artifact missing", task_id=task_id)
        format_error = InvalidArtifactFormatError("Bad format", task_id=task_id)

        assert not_found_error.task_id == task_id
        assert format_error.task_id == task_id

    @pytest.mark.parametrize(
        "exception_class,message",
        [
            (ArtifactNotFoundError, "scratchpad.md not found"),
            (InvalidArtifactFormatError, "Invalid YAML front matter"),
            (ArtifactError, "General artifact error"),
        ],
        ids=["not_found", "invalid_format", "general"],
    )
    def test_artifact_exceptions_messages(self, exception_class, message):
        """Test artifact exceptions preserve messages correctly."""
        error = exception_class(message)

        assert str(error) == message


class TestExceptionHierarchy:
    """Test exception hierarchy and polymorphism."""

    def test_all_exceptions_are_epic_task_manager_errors(self):
        """Test all custom exceptions inherit from EpicTaskManagerError."""
        # Standard exceptions with simple constructor
        standard_exception_classes = [
            StateFileError,
            InitializationError,
            TaskNotFoundError,
            PhaseTransitionError,
            ArtifactError,
            ArtifactNotFoundError,
            InvalidArtifactFormatError,
        ]

        for exception_class in standard_exception_classes:
            error = exception_class("Test message")
            assert isinstance(error, EpicTaskManagerError)

        # StateTransitionError has special constructor
        state_error = StateTransitionError("Test message", "current_state", "attempted_transition")
        assert isinstance(state_error, EpicTaskManagerError)

    def test_catch_all_custom_exceptions(self):
        """Test catching all custom exceptions with base class."""
        # Standard exceptions with simple constructor
        standard_exception_classes = [
            StateFileError,
            InitializationError,
            TaskNotFoundError,
            PhaseTransitionError,
            ArtifactError,
            ArtifactNotFoundError,
            InvalidArtifactFormatError,
        ]

        for exception_class in standard_exception_classes:
            with pytest.raises(EpicTaskManagerError):
                raise exception_class("Test error")

        # StateTransitionError has special constructor
        with pytest.raises(EpicTaskManagerError):
            raise StateTransitionError("Test error", "current_state", "attempted_transition")

    def test_artifact_exception_hierarchy(self):
        """Test artifact exception hierarchy is correct."""
        # ArtifactNotFoundError and InvalidArtifactFormatError should be ArtifactErrors
        not_found = ArtifactNotFoundError("Not found")
        invalid_format = InvalidArtifactFormatError("Invalid")

        assert isinstance(not_found, ArtifactError)
        assert isinstance(invalid_format, ArtifactError)

        # Both should be catchable as ArtifactError
        with pytest.raises(ArtifactError):
            raise ArtifactNotFoundError("Test")

        with pytest.raises(ArtifactError):
            raise InvalidArtifactFormatError("Test")

    def test_exception_method_resolution_order(self):
        """Test exception method resolution order is correct."""
        # Test that more specific exceptions are checked first
        error = ArtifactNotFoundError("Test error")

        # Should be instance of all parent classes
        assert isinstance(error, ArtifactNotFoundError)
        assert isinstance(error, ArtifactError)
        assert isinstance(error, EpicTaskManagerError)
        assert isinstance(error, Exception)

    def test_multiple_exception_handling(self):
        """Test handling multiple exception types in single try-except."""

        def raise_different_errors(error_type):
            if error_type == "state":
                raise StateTransitionError("State error", "current", "attempted")
            if error_type == "artifact":
                raise ArtifactNotFoundError("Artifact error")
            if error_type == "task":
                raise TaskNotFoundError("Task error")

        # Test catching specific types
        with pytest.raises(StateTransitionError):
            raise_different_errors("state")

        with pytest.raises(ArtifactError):
            raise_different_errors("artifact")

        with pytest.raises(TaskNotFoundError):
            raise_different_errors("task")

        # Test catching all as base type
        for error_type in ["state", "artifact", "task"]:
            with pytest.raises(EpicTaskManagerError):
                raise_different_errors(error_type)


class TestExceptionContextPreservation:
    """Test exception context and information preservation."""

    def test_task_id_preservation_across_inheritance(self):
        """Test task_id is preserved across exception inheritance."""
        task_id = "CONTEXT-TEST"

        exceptions = [
            StateFileError("State error", task_id=task_id),
            TaskNotFoundError("Task error", task_id=task_id),
            ArtifactNotFoundError("Artifact error", task_id=task_id),
        ]

        for error in exceptions:
            assert error.task_id == task_id

    def test_exception_message_preservation(self):
        """Test exception messages are preserved correctly."""
        messages = [
            "State file is corrupted",
            "Project initialization failed",
            "Task TEST-123 not found in state machine",
            "Cannot transition from working to verified without review",
            "scratchpad.md file is missing",
        ]

        exception_classes = [
            StateFileError,
            InitializationError,
            TaskNotFoundError,
            PhaseTransitionError,
            ArtifactNotFoundError,
        ]

        for message, exception_class in zip(messages, exception_classes, strict=False):
            error = exception_class(message)
            assert str(error) == message

    def test_state_transition_error_context_preservation(self):
        """Test StateTransitionError preserves all context information."""
        error = StateTransitionError("Cannot advance from working state without submitting work", current_state="gatherrequirements_working", attempted_transition="advance_to_planning")

        # All context should be preserved
        assert str(error) == "Cannot advance from working state without submitting work"
        assert error.current_state == "gatherrequirements_working"
        assert error.attempted_transition == "advance_to_planning"
        assert error.task_id is None  # Default from base class

    def test_exception_with_complex_context(self):
        """Test exceptions with complex context information."""
        task_id = "COMPLEX-CONTEXT"
        error_message = "Complex error with multiple context details"
        current_state = "complex_state_with_underscores"
        attempted_transition = "complex_transition_name"

        error = StateTransitionError(error_message, current_state=current_state, attempted_transition=attempted_transition)

        # Manually set task_id (base class attribute)
        error.task_id = task_id

        # Verify all context is preserved
        assert str(error) == error_message
        assert error.current_state == current_state
        assert error.attempted_transition == attempted_transition
        assert error.task_id == task_id

    def test_exception_context_immutability(self):
        """Test exception context cannot be accidentally modified."""
        error = StateTransitionError("Test error", current_state="initial_state", attempted_transition="initial_transition")

        # Store original values
        original_state = error.current_state
        original_transition = error.attempted_transition

        # Context should remain accessible
        assert error.current_state == original_state
        assert error.attempted_transition == original_transition

        # Values should be string types (immutable)
        assert isinstance(error.current_state, str)
        assert isinstance(error.attempted_transition, str)
