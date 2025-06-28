"""
Unit tests for the provide_review tool implementation.
"""

import pytest
from unittest.mock import Mock, patch

from src.alfred.tools.provide_review import provide_review_impl
from src.alfred.models.schemas import ToolResponse
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
        mock_tool.machine = Mock()
        mock_tool.machine.ai_approve = Mock()
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Execute
            result = provide_review_impl(task_id, is_approved, feedback_notes)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "success"
            assert "approved" in result.message.lower()
            assert "strategize" in result.message
            assert result.next_prompt is not None
            
            # Verify state machine was triggered
            mock_tool.machine.ai_approve.assert_called_once()
    
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
        mock_tool.machine = Mock()
        mock_tool.machine.request_revision = Mock()
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Execute
            result = provide_review_impl(task_id, is_approved, feedback_notes)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "success"
            assert "revisions" in result.message.lower()
            assert feedback_notes in result.next_prompt
            assert result.next_prompt is not None
            
            # Verify state machine was triggered
            mock_tool.machine.request_revision.assert_called_once()
    
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
        mock_tool.machine = Mock()
        mock_tool.machine.ai_approve = Mock()
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Execute
            result = provide_review_impl(task_id, is_approved, feedback_notes)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "success"
            assert "completed" in result.message.lower()
            assert "verified" in result.message
            assert result.next_prompt is not None
            
            # Verify tool was removed from active tools
            assert task_id not in mock_orchestrator.active_tools
            
            # Verify state machine was triggered
            mock_tool.machine.ai_approve.assert_called_once()
    
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
    
    def test_provide_review_no_current_state(self):
        """Test error handling when active tool has no current state."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""
        
        # Mock active tool without state
        mock_tool = Mock()
        mock_tool.state = None
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Execute
            result = provide_review_impl(task_id, is_approved, feedback_notes)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "error"
            assert "no current state" in result.message
    
    def test_provide_review_invalid_trigger(self):
        """Test error handling when trigger doesn't exist on machine."""
        # Setup
        task_id = "TEST-01"
        is_approved = True
        feedback_notes = ""
        
        # Mock active tool without the required trigger
        mock_tool = Mock()
        mock_tool.state = "some_state"
        mock_tool.machine = Mock()
        
        # Mock hasattr to return False for the trigger
        with patch('builtins.hasattr', return_value=False):
            # Mock orchestrator
            with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
                mock_orchestrator.active_tools = {task_id: mock_tool}
                
                # Execute
                result = provide_review_impl(task_id, is_approved, feedback_notes)
                
                # Verify
                assert isinstance(result, ToolResponse)
                assert result.status == "error"
                assert "Invalid state transition" in result.message
                assert "ai_approve" in result.message
    
    def test_provide_review_machine_exception(self):
        """Test error handling when state machine trigger raises exception."""
        # Setup
        task_id = "TEST-01"
        is_approved = False
        feedback_notes = "Test feedback"
        
        # Mock active tool that raises exception
        mock_tool = Mock()
        mock_tool.state = "review_context"
        mock_tool.machine = Mock()
        mock_tool.machine.request_revision = Mock(side_effect=Exception("State machine error"))
        
        # Mock orchestrator
        with patch('src.alfred.tools.provide_review.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Execute
            result = provide_review_impl(task_id, is_approved, feedback_notes)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "error"
            assert "Failed to process review" in result.message
            assert "State machine error" in result.message