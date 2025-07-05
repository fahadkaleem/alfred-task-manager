"""Test the provide_review_logic function, especially the feedback override behavior."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from alfred.models.schemas import ToolResponse, TaskStatus
from alfred.models.state import TaskState, WorkflowState
from alfred.tools.provide_review_logic import provide_review_logic


@pytest.mark.asyncio
async def test_provide_review_with_feedback_overrides_approval():
    """Test that providing feedback_notes with is_approved=True forces a revision."""

    # Mock task
    mock_task = Mock()
    mock_task.task_id = "TEST-001"
    mock_task.task_status = TaskStatus.IN_REVIEW

    # Mock workflow state
    mock_workflow_state = Mock(spec=WorkflowState)
    mock_workflow_state.tool_name = "review_task"
    mock_workflow_state.current_state = "reviewing_awaiting_human_review"
    mock_workflow_state.context_store = {}

    # Mock task state
    mock_task_state = Mock(spec=TaskState)
    mock_task_state.active_tool_state = mock_workflow_state

    # Create a mock workflow engine that tracks state transitions
    mock_engine = Mock()
    mock_engine.execute_trigger = Mock(return_value="reviewing")
    mock_engine.is_terminal_state = Mock(return_value=False)

    with (
        patch("alfred.tools.provide_review_logic.load_task", return_value=mock_task),
        patch("alfred.tools.provide_review_logic.state_manager") as mock_state_manager,
        patch("alfred.tools.tool_definitions.TOOL_DEFINITIONS", {"review_task": Mock(tool_class=Mock)}),
        patch("alfred.core.workflow_engine.WorkflowEngine", return_value=mock_engine),
        patch("alfred.tools.provide_review_logic.generate_prompt", return_value="Next prompt"),
        patch("alfred.tools.provide_review_logic.turn_manager") as mock_turn_manager,
    ):
        # Configure state manager
        mock_state_manager.load_or_create.return_value = mock_task_state
        mock_state_manager.save_task_state = Mock()

        # Configure turn manager
        mock_turn = Mock()
        mock_turn.turn_number = 1
        mock_turn_manager.request_revision.return_value = mock_turn

        # Call with is_approved=True BUT with feedback_notes
        feedback = "Please add more test coverage for edge cases"
        result = await provide_review_logic(
            task_id="TEST-001",
            is_approved=True,  # This should be overridden
            feedback_notes=feedback,
        )

        # Assert the result indicates revision was requested
        assert result.status == "success"
        assert "Revision requested" in result.message

        # Verify revision was recorded
        mock_turn_manager.request_revision.assert_called_once_with(task_id="TEST-001", state_to_revise="reviewing", feedback=feedback, requested_by="human")

        # Verify state transition was for revision, not approval
        mock_engine.execute_trigger.assert_called_once()
        call_args = mock_engine.execute_trigger.call_args
        assert call_args[0][0] == "reviewing_awaiting_human_review"
        assert call_args[0][1] == "request_revision"  # Should be revision trigger, not approval

        # Verify feedback was stored in context
        assert mock_workflow_state.context_store["feedback_notes"] == feedback
        assert mock_workflow_state.context_store["revision_turn_number"] == 1


@pytest.mark.asyncio
async def test_provide_review_approval_without_feedback():
    """Test that approval without feedback works normally."""

    # Mock task
    mock_task = Mock()
    mock_task.task_id = "TEST-002"
    mock_task.task_status = TaskStatus.IN_REVIEW

    # Mock workflow state
    mock_workflow_state = Mock(spec=WorkflowState)
    mock_workflow_state.tool_name = "review_task"
    mock_workflow_state.current_state = "reviewing_awaiting_human_review"
    mock_workflow_state.context_store = {}

    # Mock task state
    mock_task_state = Mock(spec=TaskState)
    mock_task_state.active_tool_state = mock_workflow_state

    # Create a mock workflow engine
    mock_engine = Mock()
    mock_engine.execute_trigger = Mock(return_value="reviewing_complete")
    mock_engine.is_terminal_state = Mock(return_value=False)

    with (
        patch("alfred.tools.provide_review_logic.load_task", return_value=mock_task),
        patch("alfred.tools.provide_review_logic.state_manager") as mock_state_manager,
        patch("alfred.tools.tool_definitions.TOOL_DEFINITIONS", {"review_task": Mock(tool_class=Mock)}),
        patch("alfred.core.workflow_engine.WorkflowEngine", return_value=mock_engine),
        patch("alfred.tools.provide_review_logic.generate_prompt", return_value="Next prompt"),
        patch("alfred.tools.provide_review_logic.ConfigManager") as mock_config_manager,
    ):
        # Configure state manager
        mock_state_manager.load_or_create.return_value = mock_task_state

        # Configure config manager for non-autonomous mode
        mock_config = Mock()
        mock_config.features.autonomous_mode = False
        mock_config_manager.return_value.load.return_value = mock_config

        # Call with is_approved=True and NO feedback_notes
        result = await provide_review_logic(
            task_id="TEST-002",
            is_approved=True,
            feedback_notes="",  # Empty feedback
        )

        # Assert the result indicates approval
        assert result.status == "success"
        assert "Human review approved" in result.message

        # Verify state transition was for approval
        mock_engine.execute_trigger.assert_called_once()
        call_args = mock_engine.execute_trigger.call_args
        assert call_args[0][0] == "reviewing_awaiting_human_review"
        assert call_args[0][1] == "human_approve"  # Should be approval trigger


@pytest.mark.asyncio
async def test_provide_review_explicit_revision():
    """Test that explicit revision (is_approved=False) works as expected."""

    # Mock task
    mock_task = Mock()
    mock_task.task_id = "TEST-003"
    mock_task.task_status = TaskStatus.IN_REVIEW

    # Mock workflow state
    mock_workflow_state = Mock(spec=WorkflowState)
    mock_workflow_state.tool_name = "review_task"
    mock_workflow_state.current_state = "reviewing_awaiting_ai_review"
    mock_workflow_state.context_store = {}

    # Mock task state
    mock_task_state = Mock(spec=TaskState)
    mock_task_state.active_tool_state = mock_workflow_state

    # Create a mock workflow engine
    mock_engine = Mock()
    mock_engine.execute_trigger = Mock(return_value="reviewing")
    mock_engine.is_terminal_state = Mock(return_value=False)

    with (
        patch("alfred.tools.provide_review_logic.load_task", return_value=mock_task),
        patch("alfred.tools.provide_review_logic.state_manager") as mock_state_manager,
        patch("alfred.tools.tool_definitions.TOOL_DEFINITIONS", {"review_task": Mock(tool_class=Mock)}),
        patch("alfred.core.workflow_engine.WorkflowEngine", return_value=mock_engine),
        patch("alfred.tools.provide_review_logic.generate_prompt", return_value="Next prompt"),
        patch("alfred.tools.provide_review_logic.turn_manager") as mock_turn_manager,
    ):
        # Configure state manager
        mock_state_manager.load_or_create.return_value = mock_task_state

        # Configure turn manager
        mock_turn = Mock()
        mock_turn.turn_number = 1
        mock_turn_manager.request_revision.return_value = mock_turn

        # Call with is_approved=False
        feedback = "The implementation is missing error handling"
        result = await provide_review_logic(task_id="TEST-003", is_approved=False, feedback_notes=feedback)

        # Assert the result indicates revision
        assert result.status == "success"
        assert "Revision requested" in result.message

        # Verify revision was recorded
        mock_turn_manager.request_revision.assert_called_once_with(task_id="TEST-003", state_to_revise="reviewing", feedback=feedback, requested_by="human")
