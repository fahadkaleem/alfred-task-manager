# tests/tools/test_progress.py
"""Tests for progress tracking tools."""
from unittest.mock import MagicMock, patch

import pytest

from src.alfred.tools.progress import mark_subtask_complete_impl
from src.alfred.core.workflow import BaseWorkflowTool


class TestMarkSubtaskComplete:
    """Test cases for mark_subtask_complete_impl function."""

    def test_no_active_tool(self):
        """Test when no active tool exists for the task."""
        result = mark_subtask_complete_impl("nonexistent-task", "subtask-1")
        assert result.status == "error"
        assert "No active tool found" in result.message

    @patch("src.alfred.tools.progress.orchestrator")
    def test_no_execution_plan(self, mock_orchestrator):
        """Test when no execution plan exists in the active tool."""
        # Create a mock tool without execution plan
        mock_tool = MagicMock(spec=BaseWorkflowTool)
        mock_tool.context_store = {}
        mock_orchestrator.active_tools = {"task-1": mock_tool}

        result = mark_subtask_complete_impl("task-1", "subtask-1")
        assert result.status == "error"
        assert "No execution plan found" in result.message

    @patch("src.alfred.tools.progress.orchestrator")
    def test_invalid_subtask_id(self, mock_orchestrator):
        """Test when subtask_id is not in the execution plan."""
        # Create a mock tool with execution plan
        mock_tool = MagicMock(spec=BaseWorkflowTool)
        mock_tool.context_store = {
            "execution_plan_artifact": {
                "subtasks": [
                    {"subtask_id": "subtask-1"},
                    {"subtask_id": "subtask-2"},
                ]
            }
        }
        mock_orchestrator.active_tools = {"task-1": mock_tool}

        result = mark_subtask_complete_impl("task-1", "invalid-subtask")
        assert result.status == "error"
        assert "Invalid subtask_id" in result.message

    @patch("src.alfred.tools.progress.orchestrator")
    def test_already_completed_subtask(self, mock_orchestrator):
        """Test when subtask is already marked as complete."""
        # Create a mock tool with completed subtask
        mock_tool = MagicMock(spec=BaseWorkflowTool)
        mock_tool.context_store = {
            "execution_plan_artifact": {
                "subtasks": [
                    {"subtask_id": "subtask-1"},
                    {"subtask_id": "subtask-2"},
                ]
            },
            "completed_subtasks": ["subtask-1"]
        }
        mock_orchestrator.active_tools = {"task-1": mock_tool}

        result = mark_subtask_complete_impl("task-1", "subtask-1")
        assert result.status == "success"
        assert "already marked complete" in result.message

    @patch("src.alfred.tools.progress.orchestrator")
    @patch("src.alfred.tools.progress.state_manager")
    def test_successful_completion(self, mock_state_manager, mock_orchestrator):
        """Test successful subtask completion with state update."""
        # Create a mock tool
        mock_tool = MagicMock(spec=BaseWorkflowTool)
        mock_tool.context_store = {
            "execution_plan_artifact": {
                "subtasks": [
                    {"subtask_id": "subtask-1"},
                    {"subtask_id": "subtask-2"},
                    {"subtask_id": "subtask-3"},
                ]
            }
        }
        mock_orchestrator.active_tools = {"task-1": mock_tool}

        result = mark_subtask_complete_impl("task-1", "subtask-1")
        
        # Verify success
        assert result.status == "success"
        assert "subtask-1" in result.message
        assert "1/3" in result.message
        assert "33%" in result.message
        
        # Verify data
        assert result.data["completed_count"] == 1
        assert result.data["total_count"] == 3
        assert result.data["progress_percentage"] == pytest.approx(33.33, rel=0.1)
        
        # Verify state manager was called
        mock_state_manager.update_tool_state.assert_called_once_with("task-1", mock_tool)
        
        # Verify context was updated
        assert mock_tool.context_store["completed_subtasks"] == ["subtask-1"]

    @patch("src.alfred.tools.progress.orchestrator")
    @patch("src.alfred.tools.progress.state_manager")
    def test_multiple_completions(self, mock_state_manager, mock_orchestrator):
        """Test marking multiple subtasks as complete."""
        # Create a mock tool with one already completed
        mock_tool = MagicMock(spec=BaseWorkflowTool)
        mock_tool.context_store = {
            "execution_plan_artifact": {
                "subtasks": [
                    {"subtask_id": "subtask-1"},
                    {"subtask_id": "subtask-2"},
                    {"subtask_id": "subtask-3"},
                ]
            },
            "completed_subtasks": ["subtask-1"]
        }
        mock_orchestrator.active_tools = {"task-1": mock_tool}

        result = mark_subtask_complete_impl("task-1", "subtask-2")
        
        # Verify success
        assert result.status == "success"
        assert "2/3" in result.message
        assert "67%" in result.message
        
        # Verify context was updated with both subtasks
        completed = set(mock_tool.context_store["completed_subtasks"])
        assert completed == {"subtask-1", "subtask-2"}