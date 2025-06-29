"""
Unit tests for the provide_review tool implementation.
"""

import pytest
from unittest.mock import Mock, patch, PropertyMock
from pathlib import Path
from contextlib import ExitStack

from src.alfred.tools.provide_review import provide_review_impl
from src.alfred.models.schemas import ToolResponse, Task, TaskStatus
from src.alfred.core.workflow import PlanTaskTool
from src.alfred.constants import ResponseStatus, ToolName


class TestProvideReview:
    """Test cases for provide_review_impl function."""

    def _create_mock_tool(self, state="strategize", next_state="design", is_terminal=False):
        """Helper to create a properly configured mock tool."""
        mock_tool = Mock(spec=PlanTaskTool)
        mock_tool.state = state
        mock_tool.is_terminal = is_terminal
        mock_tool.ai_approve = Mock()
        mock_tool.request_revision = Mock()
        mock_tool.tool_name = ToolName.PLAN_TASK
        mock_tool.persona_name = "planning"
        mock_tool.context_store = {"test_key": "test_value"}

        # Mock the state machine
        mock_transition = Mock()
        mock_transition.dest = next_state
        mock_tool.machine = Mock()
        mock_tool.machine.get_transitions.return_value = [mock_transition]

        return mock_tool

    def test_provide_review_approval_success(self):
        """Test successful review approval that transitions to next state."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""

        # Mock active tool in non-terminal state
        mock_tool = self._create_mock_tool(state="strategize", next_state="design", is_terminal=False)

        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id

        # Mock orchestrator
        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}

            # Mock task loading
            with patch("src.alfred.tools.provide_review.load_task", return_value=mock_task):
                # Mock persona loader and prompter
                with patch("src.alfred.tools.provide_review.load_persona", return_value={"name": "planning"}):
                    with patch("src.alfred.tools.provide_review.prompter") as mock_prompter:
                        mock_prompter.generate_prompt.return_value = "Test prompt"

                        # Mock state manager
                        with patch("src.alfred.tools.provide_review.state_manager") as mock_state_manager:
                            mock_state_manager.save_tool_state = Mock()

                            # Execute
                            result = provide_review_impl(task_id, is_approved, feedback_notes)

                        # Verify
                        assert isinstance(result, ToolResponse)
                        assert result.status == ResponseStatus.SUCCESS
                        assert "approved" in result.message.lower()
                        assert result.next_prompt == "Test prompt"

                        # Verify state machine was triggered
                        mock_tool.ai_approve.assert_called_once()

    def test_provide_review_rejection_success(self):
        """Test successful review rejection that returns to working state."""
        # Setup
        task_id = "TEST-01"
        is_approved = False
        feedback_notes = "Please revise the context section"

        # Mock active tool - for rejection, next state goes back to contextualize
        mock_tool = self._create_mock_tool(state="review_context", next_state="contextualize", is_terminal=False)

        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id

        # Mock orchestrator
        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}

            # Mock task loading
            with patch("src.alfred.tools.provide_review.load_task", return_value=mock_task):
                # Mock persona loader and prompter
                with patch("src.alfred.tools.provide_review.load_persona", return_value={"name": "planning"}):
                    with patch("src.alfred.tools.provide_review.prompter") as mock_prompter:
                        mock_prompter.generate_prompt.return_value = "Test prompt with feedback"

                        # Mock state manager
                        with patch("src.alfred.tools.provide_review.state_manager") as mock_state_manager:
                            mock_state_manager.save_tool_state = Mock()

                            # Execute
                            result = provide_review_impl(task_id, is_approved, feedback_notes)

                        # Verify
                        assert isinstance(result, ToolResponse)
                        assert result.status == ResponseStatus.SUCCESS
                        assert "revision" in result.message.lower()
                        assert result.next_prompt == "Test prompt with feedback"

                        # Verify state machine was triggered
                        mock_tool.request_revision.assert_called_once()

    def test_provide_review_terminal_state_completion(self):
        """Test tool completion when review leads to terminal state."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""

        # Mock active tool that will transition to terminal state
        mock_tool = self._create_mock_tool(state="review_plan", next_state="verified", is_terminal=False)

        # After transition, it becomes terminal
        def set_terminal():
            mock_tool.is_terminal = True
            mock_tool.state = "verified"

        mock_tool.ai_approve.side_effect = set_terminal

        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id

        # Mock orchestrator
        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}

            # Mock task loading and status update
            with patch("src.alfred.tools.provide_review.load_task", return_value=mock_task):
                with patch("src.alfred.tools.provide_review.update_task_status") as mock_update:
                    with patch("src.alfred.tools.provide_review.state_manager") as mock_state_manager:
                        mock_state_manager.save_tool_state = Mock()
                        mock_state_manager.clear_tool_state = Mock()

                        with patch("src.alfred.tools.provide_review.cleanup_task_logging") as mock_cleanup:
                            # Execute
                            result = provide_review_impl(task_id, is_approved, feedback_notes)

                    # Verify
                    assert isinstance(result, ToolResponse)
                    assert result.status == ResponseStatus.SUCCESS
                    assert "completed" in result.message.lower()
                    assert result.next_prompt is not None
                    assert "implement_task" in result.next_prompt

                    # Verify tool was removed from active tools
                    assert task_id not in mock_orchestrator.active_tools

                    # Verify task status was updated
                    mock_update.assert_called_once_with(task_id, TaskStatus.READY_FOR_DEVELOPMENT)

                    # Verify state machine was triggered
                    mock_tool.ai_approve.assert_called_once()

    def test_provide_review_no_active_tool(self):
        """Test error handling when no active tool exists for task."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""

        # Mock orchestrator with no active tools
        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            mock_orchestrator.active_tools = {}

            # Execute
            result = provide_review_impl(task_id, is_approved, feedback_notes)

            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == ResponseStatus.ERROR
            assert "No active tool found" in result.message
            assert task_id in result.message

    def test_provide_review_no_task_found(self):
        """Test error handling when task is not found."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""

        # Mock active tool
        mock_tool = Mock()
        mock_tool.state = "review_context"

        # Mock orchestrator
        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}

            # Mock task loading to return None
            with patch("src.alfred.tools.provide_review.load_task", return_value=None):
                # Execute
                result = provide_review_impl(task_id, is_approved, feedback_notes)

                # Verify
                assert isinstance(result, ToolResponse)
                assert result.status == ResponseStatus.ERROR
                assert "not found" in result.message
                assert task_id in result.message

    def test_provide_review_invalid_trigger(self):
        """Test error handling when trigger doesn't exist on tool."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""

        # Mock active tool without the required trigger
        mock_tool = Mock()
        mock_tool.state = "some_state"

        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id

        # Mock orchestrator
        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}

            # Mock task loading
            with patch("src.alfred.tools.provide_review.load_task", return_value=mock_task):
                # Mock hasattr to return False for the trigger
                with patch("builtins.hasattr", return_value=False):
                    # Execute
                    result = provide_review_impl(task_id, is_approved, feedback_notes)

                    # Verify
                    assert isinstance(result, ToolResponse)
                    assert result.status == ResponseStatus.ERROR
                    assert "Invalid action" in result.message
                    assert "ai_approve" in result.message


class TestFullPlanningLifecycle:
    """Integration test for the complete plan_task lifecycle."""

    def test_full_planning_lifecycle_completes_successfully(self):
        """
        Comprehensive integration test that simulates the entire plan_task lifecycle.
        Tests plan_task → submit_work → provide_review cycles through all states.
        """
        task_id = "TEST-01"

        # Mock the orchestrator and tools
        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            # Create a mock tool that transitions through states
            mock_tool = Mock(spec=PlanTaskTool)
            mock_tool.tool_name = ToolName.PLAN_TASK
            mock_tool.persona_name = "planning"
            mock_tool.context_store = {"test_key": "test_value"}
            mock_orchestrator.active_tools = {task_id: mock_tool}

            # Add machine mock
            mock_transition = Mock()
            mock_tool.machine = Mock()

            # Mock task
            mock_task = Mock(spec=Task)
            mock_task.task_id = task_id

            # Mock states progression through review states
            states = ["review_context", "review_strategy", "review_design", "review_plan"]
            terminal_flags = [False, False, False, False]

            for i, (state, is_terminal) in enumerate(zip(states, terminal_flags)):
                mock_tool.state = state
                type(mock_tool).is_terminal = PropertyMock(return_value=is_terminal)
                mock_tool.ai_approve = Mock()

                # For review_plan state, add execution plan artifact
                if state == "review_plan":
                    mock_tool.context_store["execution_plan_artifact"] = {"subtasks": [{"subtask_id": "ST-1", "title": "Test"}]}

                # Set up next state for transition
                if i < len(states) - 1:
                    next_state = states[i + 1]
                    mock_transition.dest = next_state
                    mock_tool.machine.get_transitions.return_value = [mock_transition]
                else:
                    # For review_plan (last state), next state is verified
                    next_state = "verified"
                    mock_transition.dest = next_state
                    mock_tool.machine.get_transitions.return_value = [mock_transition]

                    # Mock ai_approve to update state and set terminal
                    def approve_and_set_terminal():
                        mock_tool.state = next_state
                        type(mock_tool).is_terminal = PropertyMock(return_value=True)

                    mock_tool.ai_approve.side_effect = approve_and_set_terminal

                with patch("src.alfred.tools.provide_review.load_task", return_value=mock_task):
                    # All states are non-terminal for this test
                    # Non-terminal state - should generate next prompt
                    with patch("src.alfred.tools.provide_review.load_persona", return_value={"name": "planning"}):
                        with patch("src.alfred.tools.provide_review.prompter") as mock_prompter:
                            mock_prompter.generate_prompt.return_value = f"Prompt for {state}"

                            with patch("src.alfred.tools.provide_review.state_manager") as mock_state_manager:
                                mock_state_manager.save_tool_state = Mock()
                                mock_state_manager.clear_tool_state = Mock()

                                # For review_plan, also mock update_task_status
                                additional_patches = []
                                if state == "review_plan":
                                    update_patch = patch("src.alfred.tools.provide_review.update_task_status")
                                    cleanup_patch = patch("src.alfred.tools.provide_review.cleanup_task_logging")
                                    additional_patches = [update_patch, cleanup_patch]

                                with ExitStack() as stack:
                                    # Apply additional patches if needed
                                    for p in additional_patches:
                                        stack.enter_context(p)

                                    result = provide_review_impl(task_id, True, "")

                                assert result.status == ResponseStatus.SUCCESS

                                # Special handling for review_plan which leads to terminal state
                                if state == "review_plan":
                                    # After approving review_plan, tool becomes terminal
                                    assert "completed" in result.message.lower()
                                    assert "Planning for task TEST-01 is complete" in result.next_prompt
                                    assert "implement_task" in result.next_prompt
                                    # Verify tool was removed from active tools
                                    assert task_id not in mock_orchestrator.active_tools
                                else:
                                    assert "approved" in result.message.lower()
                                    assert result.next_prompt == f"Prompt for {state}"

                                mock_tool.ai_approve.assert_called()

    def test_review_rejection_reverts_state(self):
        """Test that rejection properly handles feedback and reverts to working state."""
        task_id = "TEST-01"
        feedback_notes = "The design needs more detail on error handling"

        # Mock active tool in review_design state
        mock_tool = Mock(spec=PlanTaskTool)
        mock_tool.state = "review_design"
        type(mock_tool).is_terminal = PropertyMock(return_value=False)
        mock_tool.request_revision = Mock()
        mock_tool.tool_name = ToolName.PLAN_TASK
        mock_tool.context_store = {"test_key": "test_value"}
        mock_tool.persona_name = "planning"
        mock_tool.machine = Mock()
        # Set up transition back to design state for rejection
        mock_transition = Mock()
        mock_transition.dest = "design"
        mock_tool.machine.get_transitions.return_value = [mock_transition]

        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id

        with patch("src.alfred.tools.provide_review.orchestrator") as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}

            with patch("src.alfred.tools.provide_review.load_task", return_value=mock_task):
                with patch("src.alfred.tools.provide_review.load_persona", return_value={"name": "planning"}):
                    with patch("src.alfred.tools.provide_review.prompter") as mock_prompter:
                        mock_prompter.generate_prompt.return_value = "Revised prompt with feedback"

                        with patch("src.alfred.tools.provide_review.state_manager") as mock_state_manager:
                            mock_state_manager.save_tool_state = Mock()

                            # Execute rejection
                            result = provide_review_impl(task_id, False, feedback_notes)

                        # Verify
                        assert result.status == ResponseStatus.SUCCESS
                        assert "revision" in result.message.lower()
                        assert result.next_prompt == "Revised prompt with feedback"

                        # Verify state machine was triggered
                        mock_tool.request_revision.assert_called_once()

                        # Verify feedback was passed to prompter
                        mock_prompter.generate_prompt.assert_called_once()
                        call_args = mock_prompter.generate_prompt.call_args
                        assert call_args[1]["additional_context"]["feedback_notes"] == feedback_notes
