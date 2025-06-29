# tests/core/test_start_task_sm.py
"""Tests for the re-architected StartTaskTool state machine."""
import pytest

from src.alfred.core.workflow import StartTaskTool, StartTaskState, ReviewState


class TestStartTaskStateMachine:
    """Test the streamlined StartTaskTool state machine."""

    def test_initial_state(self):
        """Test that the tool starts in AWAITING_GIT_STATUS state."""
        tool = StartTaskTool("test-task")
        assert tool.state == StartTaskState.AWAITING_GIT_STATUS.value

    def test_artifact_map(self):
        """Test that artifact map has the correct entries."""
        tool = StartTaskTool("test-task")
        assert len(tool.artifact_map) == 2
        assert StartTaskState.AWAITING_GIT_STATUS in tool.artifact_map
        assert StartTaskState.AWAITING_BRANCH_CREATION in tool.artifact_map

    def test_streamlined_flow(self):
        """Test the streamlined two-step flow basics."""
        tool = StartTaskTool("test-task")
        
        # Verify initial state and artifact map
        assert tool.state == StartTaskState.AWAITING_GIT_STATUS.value
        assert not tool.is_terminal
        
        # Verify the tool has the expected trigger methods
        assert hasattr(tool, f"submit_{StartTaskState.AWAITING_GIT_STATUS.value}")
        assert hasattr(tool, f"submit_{StartTaskState.AWAITING_BRANCH_CREATION.value}")
        assert hasattr(tool, "ai_approve")
        assert hasattr(tool, "human_approve")
        assert hasattr(tool, "request_revision")

    def test_revision_flow(self):
        """Test revision flow sends back to working state."""
        tool = StartTaskTool("test-task")
        
        # Submit and reach AI review
        trigger_method = getattr(tool, f"submit_{StartTaskState.AWAITING_GIT_STATUS.value}")
        trigger_method()
        assert tool.state == ReviewState.AWAITING_AI_REVIEW.value
        
        # Request revision
        tool.request_revision()
        assert tool.state == StartTaskState.AWAITING_GIT_STATUS.value