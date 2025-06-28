"""
Comprehensive tests for Epic Task Manager task tools
Tests begin_or_resume_task and approve_and_advance functions with real workflow validation.
"""

import time

import pytest

from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.tools.task_tools import (
    _is_project_initialized,
    approve_and_advance,
    begin_or_resume_task,
)


class TestStartTask:
    """Test begin_or_resume_task tool functionality."""

    @pytest.mark.asyncio
    async def test_start_task_project_not_initialized(self, isolated_epic_settings):
        """Test begin_or_resume_task fails when project not initialized."""
        # Config file doesn't exist
        result = await begin_or_resume_task("TEST-123")

        assert result.status == STATUS_ERROR
        assert "Project not initialized" in result.message

    @pytest.mark.asyncio
    async def test_start_task_creates_new_task(self, initialized_project):
        """Test begin_or_resume_task creates new task using real functionality."""
        test_settings = initialized_project

        # Use a unique task ID to ensure we're creating a new task
        unique_task_id = f"NEW-TASK-{int(time.time())}"

        result = await begin_or_resume_task(unique_task_id)

        assert result.status == STATUS_SUCCESS
        assert unique_task_id in result.message
        assert "gatherrequirements_working" in result.message
        assert result.next_prompt is not None

        # Verify task directory was created in the test directory
        task_dir = test_settings.workspace_dir / unique_task_id
        assert task_dir.exists()

    @pytest.mark.asyncio
    async def test_start_task_resumes_existing_task(self, initialized_project):
        """Test begin_or_resume_task resumes existing task using real functionality."""

        # Create task first
        create_result = await begin_or_resume_task("EXISTING-TASK")
        assert create_result.status == STATUS_SUCCESS

        # Resume the same task
        resume_result = await begin_or_resume_task("EXISTING-TASK")

        assert resume_result.status == STATUS_SUCCESS
        assert "Resuming task EXISTING-TASK" in resume_result.message
        assert "gatherrequirements_working" in resume_result.message

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "task_id,expected_normalization",
        [
            ("TEST-123", "TEST-123"),
            ("PROJ-456", "PROJ-456"),
            ("EPIC-1", "EPIC-1"),
        ],
        ids=["standard", "project", "single_digit"],
    )
    async def test_start_task_handles_valid_task_ids(self, initialized_project, task_id, expected_normalization):
        """Test begin_or_resume_task handles various valid task ID formats."""
        unique_task_id = f"{task_id}-{int(time.time())}"

        result = await begin_or_resume_task(unique_task_id)

        assert result.status == STATUS_SUCCESS
        assert unique_task_id in result.message


class TestAdvanceToNextPhase:
    """Test approve_and_advance tool functionality."""

    @pytest.mark.asyncio
    async def test_advance_project_not_initialized(self, isolated_epic_settings):
        """Test advance fails when project not initialized."""
        result = await approve_and_advance("TEST-123")

        assert result.status == STATUS_ERROR
        assert "Project not initialized" in result.message

    @pytest.mark.asyncio
    async def test_advance_task_not_found(self, initialized_project):
        """Test advance fails when task doesn't exist."""
        result = await approve_and_advance("NONEXISTENT-TASK")

        assert result.status == STATUS_ERROR
        assert "not found" in result.message

    @pytest.mark.asyncio
    async def test_advance_wrong_state(self, initialized_project):
        """Test advance fails when task in wrong state."""
        # Create task (starts in working state)
        await begin_or_resume_task("WRONG-STATE")

        # Try to advance without proper review cycle
        result = await approve_and_advance("WRONG-STATE")

        assert result.status == STATUS_ERROR
        assert "devreview" in result.message or "verified" in result.message


class TestPrivateHelperFunctions:
    """Test private helper functions in task_tools."""

    def test_is_project_initialized_true(self, initialized_project):
        """Test _is_project_initialized returns True when config exists."""
        assert _is_project_initialized() is True

    def test_is_project_initialized_false(self, isolated_epic_settings):
        """Test _is_project_initialized returns False when config doesn't exist."""
        assert _is_project_initialized() is False


class TestTaskToolsIntegration:
    """Test integration between task tools and other components."""

    @pytest.mark.asyncio
    async def test_task_lifecycle_integration(self, initialized_project):
        """Test complete task creation and state checking."""
        test_settings = initialized_project

        # Create task with unique ID
        unique_task_id = f"INTEGRATION-TEST-{int(time.time())}"
        result = await begin_or_resume_task(unique_task_id)
        assert result.status == STATUS_SUCCESS

        # Verify task directory was created
        task_dir = test_settings.workspace_dir / unique_task_id
        assert task_dir.exists()

        # Verify Epic Task Manager created the task structure
        assert len(list(task_dir.iterdir())) > 0  # At least some files/dirs should exist

    @pytest.mark.asyncio
    async def test_multiple_tasks_isolation(self, initialized_project):
        """Test multiple tasks don't interfere with each other."""
        test_settings = initialized_project

        # Create multiple tasks with unique IDs
        base_timestamp = int(time.time())
        task_ids = [f"TASK-{i}-{base_timestamp}" for i in range(1, 4)]

        for task_id in task_ids:
            result = await begin_or_resume_task(task_id)
            assert result.status == STATUS_SUCCESS

        # Verify each task has its own directory
        for task_id in task_ids:
            task_dir = test_settings.workspace_dir / task_id
            assert task_dir.exists()

            # Verify task structure was created
            assert len(list(task_dir.iterdir())) > 0

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, isolated_epic_settings):
        """Test error handling is consistent across tools."""
        # Both tools should handle uninitialized project the same way
        start_result = await begin_or_resume_task("TEST-123")
        advance_result = await approve_and_advance("TEST-123")

        assert start_result.status == STATUS_ERROR
        assert advance_result.status == STATUS_ERROR
        assert "Project not initialized" in start_result.message
        assert "Project not initialized" in advance_result.message

    @pytest.mark.asyncio
    async def test_response_format_consistency(self, initialized_project):
        """Test response format is consistent across tools."""
        result = await begin_or_resume_task("FORMAT-TEST")

        # Verify consistent response format
        assert hasattr(result, "status")
        assert hasattr(result, "message")
        assert result.status in [STATUS_SUCCESS, STATUS_ERROR]
        assert isinstance(result.message, str)
        assert len(result.message) > 0
