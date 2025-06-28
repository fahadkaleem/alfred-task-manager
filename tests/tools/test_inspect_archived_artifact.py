# File: tests/tools/test_inspect_archived_artifact.py

from unittest.mock import MagicMock, patch

import pytest

from epic_task_manager.tools.inspect_archived_artifact import (
    inspect_archived_artifact,
)


@pytest.fixture
def mock_settings():
    """Mock settings with config file existing."""
    with patch("epic_task_manager.tools.inspect_archived_artifact.settings") as mock:
        mock.config_file.exists.return_value = True
        yield mock


@pytest.fixture
def mock_settings_not_initialized():
    """Mock settings with config file not existing."""
    with patch("epic_task_manager.tools.inspect_archived_artifact.settings") as mock:
        mock.config_file.exists.return_value = False
        yield mock


@pytest.fixture
def mock_state_manager():
    """Mock StateManager."""
    with patch("epic_task_manager.tools.inspect_archived_artifact.StateManager") as mock:
        yield mock


@pytest.fixture
def mock_artifact_manager():
    """Mock ArtifactManager."""
    with patch("epic_task_manager.tools.inspect_archived_artifact.ArtifactManager") as mock:
        yield mock


@pytest.mark.asyncio
class TestInspectArchivedArtifact:
    """Test cases for the inspect_archived_artifact tool."""

    async def test_project_not_initialized(self, mock_settings_not_initialized):
        """Test error when project is not initialized."""
        result = await inspect_archived_artifact("IS-1234", "planning")

        assert result.status == "error"
        assert "Project not initialized" in result.message

    async def test_task_not_found(self, mock_settings, mock_state_manager, mock_artifact_manager):
        """Test error when task does not exist."""
        # Mock StateManager to return None (task not found)
        mock_state_manager_instance = MagicMock()
        mock_state_manager.return_value = mock_state_manager_instance
        mock_state_manager_instance.get_machine.return_value = None

        result = await inspect_archived_artifact("NONEXISTENT-123", "planning")

        assert result.status == "error"
        assert "Task NONEXISTENT-123 not found" in result.message

    async def test_invalid_phase_name(self, mock_settings, mock_state_manager, mock_artifact_manager):
        """Test error when invalid phase_name is provided."""
        # Mock StateManager to return a valid machine
        mock_state_manager_instance = MagicMock()
        mock_state_manager.return_value = mock_state_manager_instance
        mock_state_manager_instance.get_machine.return_value = MagicMock()

        result = await inspect_archived_artifact("IS-1234", "invalid_phase")

        assert result.status == "error"
        assert "Invalid phase_name 'invalid_phase'" in result.message
        assert "Must be one of: gatherrequirements, planning, coding, testing, finalize" in result.message

    async def test_archived_artifact_not_found(self, mock_settings, mock_state_manager, mock_artifact_manager):
        """Test error when archived artifact does not exist."""
        # Mock StateManager to return a valid machine
        mock_state_manager_instance = MagicMock()
        mock_state_manager.return_value = mock_state_manager_instance
        mock_state_manager_instance.get_machine.return_value = MagicMock()

        # Mock ArtifactManager to return a path that doesn't exist
        mock_artifact_manager_instance = MagicMock()
        mock_artifact_manager.return_value = mock_artifact_manager_instance
        mock_archive_path = MagicMock()
        mock_archive_path.exists.return_value = False
        mock_artifact_manager_instance.get_archive_path.return_value = mock_archive_path

        result = await inspect_archived_artifact("IS-1234", "planning")

        assert result.status == "error"
        assert "No archived artifact found for task IS-1234 phase 'planning'" in result.message
        assert "The phase may not have been completed yet" in result.message

    async def test_successful_artifact_retrieval(self, mock_settings, mock_state_manager, mock_artifact_manager):
        """Test successful retrieval of archived artifact."""
        # Mock StateManager to return a valid machine
        mock_state_manager_instance = MagicMock()
        mock_state_manager.return_value = mock_state_manager_instance
        mock_state_manager_instance.get_machine.return_value = MagicMock()

        # Mock ArtifactManager to return a valid archived artifact
        mock_artifact_manager_instance = MagicMock()
        mock_artifact_manager.return_value = mock_artifact_manager_instance
        mock_archive_path = MagicMock()
        mock_archive_path.exists.return_value = True

        # Sample artifact content
        sample_content = """---
task_id: IS-1234
phase: planning
status: verified
version: 1.0
ai_model: claude-3.5-sonnet
---

# Implementation Plan: IS-1234

## 1. Scope Verification
This is a test planning artifact.

## 2. Technical Approach
Test approach details here.

## 3. File Breakdown
Test file breakdown here.
"""
        mock_archive_path.read_text.return_value = sample_content
        mock_artifact_manager_instance.get_archive_path.return_value = mock_archive_path

        result = await inspect_archived_artifact("IS-1234", "planning")

        assert result.status == "success"
        assert result.data is not None

        # Verify the response structure
        data = result.data
        assert data["task_id"] == "IS-1234"
        assert data["phase_name"] == "planning"
        assert data["artifact_content"] == sample_content

        # Verify ArtifactManager was called correctly
        mock_artifact_manager_instance.get_archive_path.assert_called_once_with("IS-1234", "planning", 1)

    async def test_all_valid_phase_names(self, mock_settings, mock_state_manager, mock_artifact_manager):
        """Test that all valid phase names are accepted."""
        # Mock StateManager to return a valid machine
        mock_state_manager_instance = MagicMock()
        mock_state_manager.return_value = mock_state_manager_instance
        mock_state_manager_instance.get_machine.return_value = MagicMock()

        # Mock ArtifactManager to return a valid archived artifact
        mock_artifact_manager_instance = MagicMock()
        mock_artifact_manager.return_value = mock_artifact_manager_instance
        mock_archive_path = MagicMock()
        mock_archive_path.exists.return_value = True
        mock_archive_path.read_text.return_value = "Test content"
        mock_artifact_manager_instance.get_archive_path.return_value = mock_archive_path

        valid_phases = ["gatherrequirements", "planning", "coding"]

        for phase in valid_phases:
            result = await inspect_archived_artifact("IS-1234", phase)
            assert result.status == "success"
            assert result.data["phase_name"] == phase

    async def test_exception_handling(self, mock_settings, mock_state_manager, mock_artifact_manager):
        """Test that exceptions are properly handled."""
        # Mock StateManager and ArtifactManager instances
        mock_state_manager_instance = MagicMock()
        mock_artifact_manager_instance = MagicMock()
        mock_state_manager.return_value = mock_state_manager_instance
        mock_artifact_manager.return_value = mock_artifact_manager_instance

        # Mock task exists but archive read fails with FileNotFoundError (a specific exception we catch)
        mock_machine = MagicMock()
        mock_state_manager_instance.get_machine.return_value = mock_machine

        mock_archive_path = MagicMock()
        mock_archive_path.exists.return_value = True
        mock_archive_path.read_text.side_effect = FileNotFoundError("File not found")
        mock_artifact_manager_instance.get_archive_path.return_value = mock_archive_path

        result = await inspect_archived_artifact("IS-1234", "planning")

        assert result.status == "error"
        assert "Failed to inspect archived artifact: File not found" in result.message

    async def test_response_model_validation(self, mock_settings, mock_state_manager, mock_artifact_manager):
        """Test that the response follows the Pydantic model structure."""
        # Mock StateManager to return a valid machine
        mock_state_manager_instance = MagicMock()
        mock_state_manager.return_value = mock_state_manager_instance
        mock_state_manager_instance.get_machine.return_value = MagicMock()

        # Mock ArtifactManager to return a valid archived artifact
        mock_artifact_manager_instance = MagicMock()
        mock_artifact_manager.return_value = mock_artifact_manager_instance
        mock_archive_path = MagicMock()
        mock_archive_path.exists.return_value = True
        mock_archive_path.read_text.return_value = "Test artifact content"
        mock_artifact_manager_instance.get_archive_path.return_value = mock_archive_path

        result = await inspect_archived_artifact("EP-456", "gatherrequirements")

        # Verify the response can be parsed by the Pydantic model
        assert result.status == "success"
        response_data = result.data

        # Validate that the response data contains expected fields
        assert response_data["task_id"] == "EP-456"
        assert response_data["phase_name"] == "gatherrequirements"
        assert response_data["artifact_content"] == "Test artifact content"
