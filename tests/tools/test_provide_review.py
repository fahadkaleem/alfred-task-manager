"""
Unit tests for the provide_review tool implementation.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.alfred.tools.provide_review import provide_review_impl
from src.alfred.models.schemas import ToolResponse, Task, TaskStatus
from src.alfred.core.workflow import PlanTaskTool


class TestProvideReview:
    """Test cases for provide_review_impl function."""
    
    def test_provide_review_approval_success(self):
        """Test successful review approval that transitions to next state."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""
        
        # Mock active tool in non-terminal state
        mock_tool = Mock(spec=PlanTaskTool)
        mock_tool.state = "strategize"  # After approval, not terminal
        mock_tool.is_terminal = False
        mock_tool.ai_approve = Mock()
        mock_tool.tool_name = "plan_task"
        mock_tool.persona_name = "planning"
        mock_tool.context_store = {"test_key": "test_value"}
        
        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Mock task loading
            with patch('src.alfred.tools.provide_review.load_task', return_value=mock_task):
                # Mock persona loader and prompter
                with patch('src.alfred.tools.provide_review.load_persona', return_value={"name": "planning"}):
                    with patch('src.alfred.tools.provide_review.prompter') as mock_prompter:
                        mock_prompter.generate_prompt.return_value = "Test prompt"
                        
                        # Execute
                        result = provide_review_impl(task_id, is_approved, feedback_notes)
                        
                        # Verify
                        assert isinstance(result, ToolResponse)
                        assert result.status == "success"
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
        
        # Mock active tool
        mock_tool = Mock(spec=PlanTaskTool)
        mock_tool.state = "contextualize"  # Returned to working state
        mock_tool.is_terminal = False
        mock_tool.request_revision = Mock()
        mock_tool.tool_name = "plan_task"
        mock_tool.persona_name = "planning"
        mock_tool.context_store = {"test_key": "test_value"}
        
        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Mock task loading
            with patch('src.alfred.tools.provide_review.load_task', return_value=mock_task):
                # Mock persona loader and prompter
                with patch('src.alfred.tools.provide_review.load_persona', return_value={"name": "planning"}):
                    with patch('src.alfred.tools.provide_review.prompter') as mock_prompter:
                        mock_prompter.generate_prompt.return_value = "Test prompt with feedback"
                        
                        # Execute
                        result = provide_review_impl(task_id, is_approved, feedback_notes)
                        
                        # Verify
                        assert isinstance(result, ToolResponse)
                        assert result.status == "success"
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
        
        # Mock active tool in terminal state after approval
        mock_tool = Mock(spec=PlanTaskTool)
        mock_tool.state = "verified"
        mock_tool.is_terminal = True
        mock_tool.ai_approve = Mock()
        mock_tool.tool_name = "plan_task"
        mock_tool.context_store = {"test_key": "test_value"}
        
        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Mock task loading and status update
            with patch('src.alfred.tools.provide_review.load_task', return_value=mock_task):
                with patch('src.alfred.tools.provide_review.update_task_status') as mock_update:
                    # Execute
                    result = provide_review_impl(task_id, is_approved, feedback_notes)
                    
                    # Verify
                    assert isinstance(result, ToolResponse)
                    assert result.status == "success"
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
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {}
            
            # Execute
            result = provide_review_impl(task_id, is_approved, feedback_notes)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "error"
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
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Mock task loading to return None
            with patch('src.alfred.tools.provide_review.load_task', return_value=None):
                # Execute
                result = provide_review_impl(task_id, is_approved, feedback_notes)
                
                # Verify
                assert isinstance(result, ToolResponse)
                assert result.status == "error"
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
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Mock task loading
            with patch('src.alfred.tools.provide_review.load_task', return_value=mock_task):
                # Mock hasattr to return False for the trigger
                with patch('builtins.hasattr', return_value=False):
                    # Execute
                    result = provide_review_impl(task_id, is_approved, feedback_notes)
                    
                    # Verify
                    assert isinstance(result, ToolResponse)
                    assert result.status == "error"
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
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            # Create a mock tool that transitions through states
            mock_tool = Mock(spec=PlanTaskTool)
            mock_tool.tool_name = "plan_task"
            mock_tool.persona_name = "planning"
            mock_tool.context_store = {"test_key": "test_value"}
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Mock task
            mock_task = Mock(spec=Task)
            mock_task.task_id = task_id
            
            # Mock states progression: contextualize → strategize → design → generate_slots → verified
            states = ["contextualize", "strategize", "design", "generate_slots", "verified"]
            terminal_flags = [False, False, False, False, True]
            
            for i, (state, is_terminal) in enumerate(zip(states, terminal_flags)):
                mock_tool.state = state
                mock_tool.is_terminal = is_terminal
                mock_tool.ai_approve = Mock()
                
                with patch('src.alfred.tools.provide_review.load_task', return_value=mock_task):
                    if not is_terminal:
                        # Non-terminal state - should generate next prompt
                        with patch('src.alfred.tools.provide_review.load_persona', return_value={"name": "planning"}):
                            with patch('src.alfred.tools.provide_review.prompter') as mock_prompter:
                                mock_prompter.generate_prompt.return_value = f"Prompt for {state}"
                                
                                result = provide_review_impl(task_id, True, "")
                                
                                assert result.status == "success"
                                assert "approved" in result.message.lower()
                                assert result.next_prompt == f"Prompt for {state}"
                                mock_tool.ai_approve.assert_called()
                    else:
                        # Terminal state - should complete tool
                        with patch('src.alfred.tools.provide_review.update_task_status') as mock_update:
                            result = provide_review_impl(task_id, True, "")
                            
                            # Verify terminal state handling
                            assert result.status == "success"
                            assert "completed" in result.message.lower()
                            assert "implement_task" in result.next_prompt
                            
                            # Verify task status update
                            mock_update.assert_called_once_with(task_id, TaskStatus.READY_FOR_DEVELOPMENT)
                            
                            # Verify tool removed from active tools
                            assert task_id not in mock_orchestrator.active_tools
                            
                            mock_tool.ai_approve.assert_called()
    
    def test_review_rejection_reverts_state(self):
        """Test that rejection properly handles feedback and reverts to working state."""
        task_id = "TEST-01"
        feedback_notes = "The design needs more detail on error handling"
        
        # Mock active tool in design state
        mock_tool = Mock(spec=PlanTaskTool)
        mock_tool.state = "design"
        mock_tool.is_terminal = False
        mock_tool.request_revision = Mock()
        mock_tool.tool_name = "plan_task"
        mock_tool.context_store = {"test_key": "test_value"}
        mock_tool.persona_name = "planning"
        
        # Mock task
        mock_task = Mock(spec=Task)
        mock_task.task_id = task_id
        
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            with patch('src.alfred.tools.provide_review.load_task', return_value=mock_task):
                with patch('src.alfred.tools.provide_review.load_persona', return_value={"name": "planning"}):
                    with patch('src.alfred.tools.provide_review.prompter') as mock_prompter:
                        mock_prompter.generate_prompt.return_value = "Revised prompt with feedback"
                        
                        # Execute rejection
                        result = provide_review_impl(task_id, False, feedback_notes)
                        
                        # Verify
                        assert result.status == "success"
                        assert "revision" in result.message.lower()
                        assert result.next_prompt == "Revised prompt with feedback"
                        
                        # Verify state machine was triggered
                        mock_tool.request_revision.assert_called_once()
                        
                        # Verify feedback was passed to prompter
                        mock_prompter.generate_prompt.assert_called_once()
                        call_args = mock_prompter.generate_prompt.call_args
                        assert call_args[1]['additional_context']['feedback_notes'] == feedback_notes