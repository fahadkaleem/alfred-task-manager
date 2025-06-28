"""
Unit tests for Alfred core data models.
"""

import pytest
from pydantic import ValidationError

from src.alfred.models.schemas import (
    Task,
    TaskStatus,
    SLOT,
    OperationType,
    Taskflow,
)


class TestTaskModel:
    """Test cases for the Task Pydantic model."""

    def test_task_model_creation(self):
        """Test successful Task model instantiation and default status."""
        task = Task(
            task_id="TS-01",
            title="Test Task",
            context="This is a test task for validation",
            implementation_details="Create a simple test implementation",
        )
        
        assert task.task_id == "TS-01"
        assert task.title == "Test Task"
        assert task.context == "This is a test task for validation"
        assert task.implementation_details == "Create a simple test implementation"
        assert task.task_status == TaskStatus.NEW
        assert task.dev_notes is None
        assert task.acceptance_criteria == []
        assert task.ac_verification_steps == []

    def test_task_model_with_all_fields(self):
        """Test Task model with all optional fields populated."""
        task = Task(
            task_id="TS-02",
            title="Complete Task",
            context="Comprehensive test task",
            implementation_details="Full implementation details",
            dev_notes="Important developer notes",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            ac_verification_steps=["Step 1", "Step 2"],
            task_status=TaskStatus.IN_DEVELOPMENT,
        )
        
        assert task.task_status == TaskStatus.IN_DEVELOPMENT
        assert task.dev_notes == "Important developer notes"
        assert len(task.acceptance_criteria) == 2
        assert len(task.ac_verification_steps) == 2

    def test_invalid_task_status_raises_error(self):
        """Test that invalid task status raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                task_id="TS-03",
                title="Invalid Task",
                context="Test invalid status",
                implementation_details="Implementation details",
                task_status="in-progress",  # Invalid status
            )
        
        assert "task_status" in str(exc_info.value)


class TestSLOTModel:
    """Test cases for the SLOT Pydantic model."""

    def test_slot_model_creation(self):
        """Test successful SLOT model instantiation."""
        taskflow = Taskflow(
            procedural_steps=["Step 1", "Step 2"],
            verification_steps=["Verify 1", "Verify 2"],
        )
        
        slot = SLOT(
            slot_id="slot_1.1",
            title="Test SLOT",
            spec="Detailed specification for the slot",
            location="src/test_file.py",
            operation=OperationType.CREATE,
            taskflow=taskflow,
        )
        
        assert slot.slot_id == "slot_1.1"
        assert slot.title == "Test SLOT"
        assert slot.spec == "Detailed specification for the slot"
        assert slot.location == "src/test_file.py"
        assert slot.operation == OperationType.CREATE
        assert isinstance(slot.taskflow, Taskflow)

    def test_invalid_operation_type_raises_error(self):
        """Test that invalid operation type raises ValidationError."""
        taskflow = Taskflow(
            procedural_steps=["Step 1"],
            verification_steps=["Verify 1"],
        )
        
        with pytest.raises(ValidationError) as exc_info:
            SLOT(
                slot_id="slot_1.2",
                title="Invalid SLOT",
                spec="Test spec",
                location="src/test.py",
                operation="invalid_operation",  # Invalid operation
                taskflow=taskflow,
            )
        
        assert "operation" in str(exc_info.value)


class TestTaskflowModel:
    """Test cases for the Taskflow Pydantic model."""

    def test_taskflow_model_creation(self):
        """Test successful Taskflow model instantiation."""
        taskflow = Taskflow(
            procedural_steps=["Execute step 1", "Execute step 2", "Execute step 3"],
            verification_steps=["Verify step 1", "Verify step 2"],
        )
        
        assert len(taskflow.procedural_steps) == 3
        assert len(taskflow.verification_steps) == 2
        assert taskflow.procedural_steps[0] == "Execute step 1"
        assert taskflow.verification_steps[0] == "Verify step 1"


class TestSerialization:
    """Test cases for model serialization and deserialization."""

    def test_task_serialization_and_deserialization(self):
        """Test Task model JSON serialization and deserialization."""
        original_task = Task(
            task_id="TS-04",
            title="Serialization Test",
            context="Test serialization functionality",
            implementation_details="Implement JSON serialization",
            dev_notes="Test notes",
            acceptance_criteria=["AC1", "AC2"],
            ac_verification_steps=["Verify AC1", "Verify AC2"],
            task_status=TaskStatus.PLANNING,
        )
        
        # Serialize to JSON
        json_data = original_task.model_dump_json()
        assert isinstance(json_data, str)
        
        # Deserialize from JSON
        deserialized_task = Task.model_validate_json(json_data)
        
        # Verify all fields match
        assert deserialized_task.task_id == original_task.task_id
        assert deserialized_task.title == original_task.title
        assert deserialized_task.context == original_task.context
        assert deserialized_task.implementation_details == original_task.implementation_details
        assert deserialized_task.dev_notes == original_task.dev_notes
        assert deserialized_task.acceptance_criteria == original_task.acceptance_criteria
        assert deserialized_task.ac_verification_steps == original_task.ac_verification_steps
        assert deserialized_task.task_status == original_task.task_status

    def test_slot_serialization_and_deserialization(self):
        """Test SLOT model JSON serialization and deserialization."""
        taskflow = Taskflow(
            procedural_steps=["Create file", "Add content", "Test file"],
            verification_steps=["Check file exists", "Validate content"],
        )
        
        original_slot = SLOT(
            slot_id="slot_2.1",
            title="Serialization SLOT Test",
            spec="Create and test a new file",
            location="src/new_file.py",
            operation=OperationType.CREATE,
            taskflow=taskflow,
        )
        
        # Serialize to JSON
        json_data = original_slot.model_dump_json()
        assert isinstance(json_data, str)
        
        # Deserialize from JSON
        deserialized_slot = SLOT.model_validate_json(json_data)
        
        # Verify all fields match
        assert deserialized_slot.slot_id == original_slot.slot_id
        assert deserialized_slot.title == original_slot.title
        assert deserialized_slot.spec == original_slot.spec
        assert deserialized_slot.location == original_slot.location
        assert deserialized_slot.operation == original_slot.operation
        assert deserialized_slot.taskflow.procedural_steps == original_slot.taskflow.procedural_steps
        assert deserialized_slot.taskflow.verification_steps == original_slot.taskflow.verification_steps


class TestEnums:
    """Test cases for enum functionality."""

    def test_task_status_enum_values(self):
        """Test that TaskStatus enum has all expected values."""
        expected_statuses = {
            "new", "planning", "ready_for_development", "in_development",
            "ready_for_review", "in_review", "revisions_requested",
            "ready_for_testing", "in_testing", "ready_for_finalization", "done"
        }
        
        actual_statuses = {status.value for status in TaskStatus}
        assert actual_statuses == expected_statuses

    def test_operation_type_enum_values(self):
        """Test that OperationType enum has all expected values."""
        expected_operations = {"create", "modify", "delete", "review"}
        
        actual_operations = {op.value for op in OperationType}
        assert actual_operations == expected_operations

    def test_enum_string_inheritance(self):
        """Test that enums properly inherit from str."""
        assert isinstance(TaskStatus.NEW, str)
        assert isinstance(OperationType.CREATE, str)
        assert TaskStatus.NEW == "new"
        assert OperationType.CREATE == "create"