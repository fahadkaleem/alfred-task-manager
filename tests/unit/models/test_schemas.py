"""
Unit tests for Alfred schemas and data models.
"""

import pytest
from datetime import datetime
from typing import Any, Dict

from src.alfred.models.schemas import (
    ToolResponse,
    TaskStatus,
    OperationType,
    Task,
    Subtask,
)


class TestToolResponse:
    """Test ToolResponse model validation and behavior."""

    def test_tool_response_creation_success(self):
        """Test creating a successful ToolResponse."""
        response = ToolResponse(status="success", message="Operation completed", data={"key": "value"}, next_prompt="Next step...")

        assert response.status == "success"
        assert response.message == "Operation completed"
        assert response.data == {"key": "value"}
        assert response.next_prompt == "Next step..."

    def test_tool_response_minimal_creation(self):
        """Test creating ToolResponse with minimal required fields."""
        response = ToolResponse(status="success", message="Done")

        assert response.status == "success"
        assert response.message == "Done"
        assert response.data is None
        assert response.next_prompt is None

    def test_tool_response_error_status(self):
        """Test creating error ToolResponse."""
        response = ToolResponse(status="error", message="Something went wrong", data={"error_code": "ERR_001"})

        assert response.status == "error"
        assert response.message == "Something went wrong"
        assert response.data["error_code"] == "ERR_001"

    def test_tool_response_serialization(self):
        """Test ToolResponse can be serialized to dict."""
        response = ToolResponse(status="success", message="Test", data={"test": True})

        serialized = response.model_dump()
        assert isinstance(serialized, dict)
        assert serialized["status"] == "success"
        assert serialized["message"] == "Test"
        assert serialized["data"]["test"] is True


class TestTaskStatus:
    """Test TaskStatus enum functionality."""

    def test_all_status_values_exist(self):
        """Test that all expected status values are defined."""
        expected_statuses = [
            "new",
            "creating_spec",
            "spec_completed",
            "creating_tasks",
            "tasks_created",
            "planning",
            "ready_for_development",
            "in_development",
            "ready_for_review",
            "in_review",
            "revisions_requested",
            "ready_for_testing",
            "in_testing",
            "ready_for_finalization",
            "in_finalization",
            "done",
        ]

        for status in expected_statuses:
            assert hasattr(TaskStatus, status.upper())
            assert TaskStatus(status) == status

    def test_status_string_conversion(self):
        """Test TaskStatus string representation."""
        assert TaskStatus.NEW.value == "new"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.IN_DEVELOPMENT.value == "in_development"

    def test_status_comparison(self):
        """Test TaskStatus comparison operations."""
        assert TaskStatus.NEW == "new"
        assert TaskStatus.NEW != TaskStatus.DONE
        assert TaskStatus.NEW == TaskStatus.NEW


class TestOperationType:
    """Test OperationType enum functionality."""

    def test_all_operation_types_exist(self):
        """Test that all expected operation types are defined."""
        expected_operations = ["CREATE", "MODIFY", "DELETE", "REVIEW"]

        for operation in expected_operations:
            assert hasattr(OperationType, operation)
            assert OperationType(operation) == operation

    def test_operation_type_values(self):
        """Test OperationType enum values."""
        assert OperationType.CREATE == "CREATE"
        assert OperationType.MODIFY == "MODIFY"
        assert OperationType.DELETE == "DELETE"
        assert OperationType.REVIEW == "REVIEW"


class TestTask:
    """Test Task model validation and behavior."""

    def test_task_creation_minimal(self, sample_task):
        """Test creating Task with minimal required fields."""
        task = Task(task_id="MIN-001", title="Minimal Task", context="Test context", implementation_details="Test implementation", task_status=TaskStatus.NEW, acceptance_criteria=["Test criterion"])

        assert task.task_id == "MIN-001"
        assert task.title == "Minimal Task"
        assert task.task_status == TaskStatus.NEW
        assert len(task.acceptance_criteria) == 1

    def test_task_creation_full(self):
        """Test creating Task with all fields."""
        task = Task(
            task_id="FULL-001",
            title="Full Task",
            context="Complete context",
            implementation_details="Complete implementation details",
            task_status=TaskStatus.PLANNING,
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            ac_verification_steps=["Verify 1", "Verify 2"],
            dev_notes="Developer notes",
        )

        assert task.task_id == "FULL-001"
        assert task.title == "Full Task"
        assert task.task_status == TaskStatus.PLANNING
        assert task.context == "Complete context"
        assert task.implementation_details == "Complete implementation details"
        assert task.dev_notes == "Developer notes"
        assert len(task.ac_verification_steps) == 2

    def test_task_status_validation(self):
        """Test Task status validation."""
        # Valid status
        task = Task(task_id="VALID-001", title="Valid Task", context="Test context", implementation_details="Test implementation", task_status=TaskStatus.NEW, acceptance_criteria=["Test"])
        assert task.task_status == TaskStatus.NEW

    def test_task_serialization(self, sample_task):
        """Test Task serialization to dict."""
        task_dict = sample_task.model_dump()

        assert isinstance(task_dict, dict)
        assert task_dict["task_id"] == "SAMPLE-001"
        assert task_dict["task_status"] == "new"
        assert "acceptance_criteria" in task_dict

    def test_task_deserialization(self):
        """Test Task creation from dict."""
        task_data = {
            "task_id": "DESER-001",
            "title": "Deserialized Task",
            "context": "From dict context",
            "implementation_details": "From dict implementation",
            "task_status": "new",
            "acceptance_criteria": ["Test"],
        }

        task = Task(**task_data)
        assert task.task_id == "DESER-001"
        assert task.task_status == TaskStatus.NEW

    def test_task_id_validation(self):
        """Test task ID format validation."""
        # Valid task IDs should work
        valid_ids = ["TEST-001", "PROJ-123", "EPIC-01", "BUG-999"]

        for task_id in valid_ids:
            task = Task(task_id=task_id, title="Test", context="Test context", implementation_details="Test implementation", task_status=TaskStatus.NEW, acceptance_criteria=["Test"])
            assert task.task_id == task_id

    def test_empty_acceptance_criteria_allowed(self):
        """Test that empty acceptance criteria is allowed (defaults to empty list)."""
        task = Task(
            task_id="NO-AC-001",
            title="No AC Task",
            context="Missing acceptance criteria",
            implementation_details="Test implementation",
            task_status=TaskStatus.NEW,
            acceptance_criteria=[],  # Empty list is allowed
        )
        assert task.acceptance_criteria == []


class TestSubtask:
    """Test Subtask model validation and behavior."""

    def test_subtask_creation_minimal(self):
        """Test creating Subtask with minimal required fields."""
        subtask = Subtask(
            subtask_id="ST-001",
            title="Test Subtask",
            location="src/test.py",
            operation=OperationType.CREATE,
            specification=["Create test file", "Add basic logic"],
            test=["Verify file exists", "Run unit tests"],
        )

        assert subtask.subtask_id == "ST-001"
        assert subtask.title == "Test Subtask"
        assert subtask.location == "src/test.py"
        assert subtask.operation == OperationType.CREATE
        assert len(subtask.specification) == 2
        assert len(subtask.test) == 2
        assert subtask.summary is None

    def test_subtask_creation_with_summary(self):
        """Test creating Subtask with optional summary."""
        subtask = Subtask(
            subtask_id="ST-002",
            title="Complex Subtask",
            summary="This subtask involves complex refactoring",
            location="src/complex.py",
            operation=OperationType.MODIFY,
            specification=["Refactor function", "Update tests"],
            test=["Run tests", "Check coverage"],
        )

        assert subtask.summary == "This subtask involves complex refactoring"

    def test_subtask_operation_types(self):
        """Test all operation types work with Subtask."""
        for operation in OperationType:
            subtask = Subtask(
                subtask_id=f"ST-{operation.value}",
                title=f"Test {operation.value}",
                location="src/test.py",
                operation=operation,
                specification=[f"Execute {operation.value}"],
                test=[f"Verify {operation.value}"],
            )
            assert subtask.operation == operation

    def test_subtask_serialization(self):
        """Test Subtask serialization to dict."""
        subtask = Subtask(
            subtask_id="ST-SER", title="Serialization Test", location="src/serialize.py", operation=OperationType.CREATE, specification=["Create serialization logic"], test=["Test serialization"]
        )

        subtask_dict = subtask.model_dump()
        assert isinstance(subtask_dict, dict)
        assert subtask_dict["subtask_id"] == "ST-SER"
        assert subtask_dict["operation"] == "CREATE"  # Should use enum value
        assert "specification" in subtask_dict
        assert "test" in subtask_dict

    def test_subtask_specification_validation(self):
        """Test Subtask specification list validation."""
        # Empty specification should be allowed
        subtask = Subtask(subtask_id="ST-EMPTY", title="Empty Spec", location="src/empty.py", operation=OperationType.REVIEW, specification=[], test=["Review code"])
        assert subtask.specification == []

        # Multiple specification steps
        subtask = Subtask(subtask_id="ST-MULTI", title="Multi Step", location="src/multi.py", operation=OperationType.MODIFY, specification=["Step 1", "Step 2", "Step 3"], test=["Test all steps"])
        assert len(subtask.specification) == 3

    def test_subtask_test_validation(self):
        """Test Subtask test list validation."""
        # Empty test list should be allowed
        subtask = Subtask(subtask_id="ST-NO-TEST", title="No Tests", location="src/notest.py", operation=OperationType.DELETE, specification=["Delete file"], test=[])
        assert subtask.test == []

        # Multiple test steps
        subtask = Subtask(
            subtask_id="ST-MULTI-TEST",
            title="Multi Test",
            location="src/multitest.py",
            operation=OperationType.CREATE,
            specification=["Create function"],
            test=["Unit test", "Integration test", "Manual test"],
        )
        assert len(subtask.test) == 3
