"""
Unit tests for the submit_work tool implementation.
"""

import pytest
from unittest.mock import Mock, patch

from src.alfred.tools.submit_work import submit_work_impl
from src.alfred.models.schemas import ToolResponse
from src.alfred.core.workflow import PlanTaskTool


class TestSubmitWork:
    """Test cases for submit_work_impl function."""
    
    def test_submit_work_success_path(self):
        """Test successful work submission that transitions state."""
        # Setup
        task_id = "TEST-01"
        artifact = {"context": "This is test context"}
        
        # Mock active tool
        mock_tool = Mock(spec=PlanTaskTool)
        mock_tool.state = "contextualize"
        mock_tool.machine = Mock()
        mock_tool.machine.submit_contextualize = Mock()
        
        # Mock orchestrator
        with patch('src.alfred.tools.submit_work.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Mock artifact manager
            with patch('src.alfred.tools.submit_work.artifact_manager') as mock_artifact_manager:
                # Execute
                result = submit_work_impl(task_id, artifact)
                
                # Verify
                assert isinstance(result, ToolResponse)
                assert result.status == "success"
                assert "contextualize" in result.message
                assert result.next_prompt is not None
                
                # Verify state machine was triggered
                mock_tool.machine.submit_contextualize.assert_called_once()
                
                # Verify artifact was persisted
                mock_artifact_manager.append_to_scratchpad.assert_called_once_with(
                    task_id, "contextualize", artifact, None
                )
    
    def test_submit_work_no_active_tool(self):
        """Test error handling when no active tool exists for task."""
        # Setup
        task_id = "TEST-01"
        artifact = {"context": "This is test context"}
        
        # Mock orchestrator with no active tools
        with patch('src.alfred.tools.submit_work.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {}
            
            # Execute
            result = submit_work_impl(task_id, artifact)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "error"
            assert "No active tool found" in result.message
            assert task_id in result.message
    
    def test_submit_work_no_current_state(self):
        """Test error handling when active tool has no current state."""
        # Setup
        task_id = "TEST-01"
        artifact = {"context": "This is test context"}
        
        # Mock active tool without state
        mock_tool = Mock()
        mock_tool.state = None
        
        # Mock orchestrator
        with patch('src.alfred.tools.submit_work.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Execute
            result = submit_work_impl(task_id, artifact)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "error"
            assert "no current state" in result.message
    
    def test_submit_work_invalid_trigger(self):
        """Test error handling when trigger doesn't exist on machine."""
        # Setup
        task_id = "TEST-01"
        artifact = {"context": "This is test context"}
        
        # Mock active tool with invalid trigger
        mock_tool = Mock()
        mock_tool.state = "invalid_state"
        mock_tool.machine = Mock()
        
        # Mock hasattr to return False for the trigger
        with patch('builtins.hasattr', return_value=False):
            # Mock orchestrator
            with patch('src.alfred.tools.submit_work.orchestrator') as mock_orchestrator:
                mock_orchestrator.active_tools = {task_id: mock_tool}
                
                # Execute
                result = submit_work_impl(task_id, artifact)
                
                # Verify
                assert isinstance(result, ToolResponse)
                assert result.status == "error"
                assert "Invalid state transition" in result.message
                assert "submit_invalid_state" in result.message
    
    def test_submit_work_machine_exception(self):
        """Test error handling when state machine trigger raises exception."""
        # Setup
        task_id = "TEST-01"
        artifact = {"context": "This is test context"}
        
        # Mock active tool that raises exception
        mock_tool = Mock()
        mock_tool.state = "contextualize"
        mock_tool.machine = Mock()
        mock_tool.machine.submit_contextualize = Mock(side_effect=Exception("State machine error"))
        
        # Mock orchestrator
        with patch('src.alfred.tools.submit_work.orchestrator') as mock_orchestrator:
            mock_orchestrator.active_tools = {task_id: mock_tool}
            
            # Execute
            result = submit_work_impl(task_id, artifact)
            
            # Verify
            assert isinstance(result, ToolResponse)
            assert result.status == "error"
            assert "Failed to submit work" in result.message
            assert "State machine error" in result.message