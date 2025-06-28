"""
Unit tests for the submit_work tool implementation.
"""

import json

from src.alfred.core.workflow import PlanTaskState
from src.alfred.models.schemas import Task
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.tools.submit_work import submit_work_impl


class TestSubmitWork:
    """Test cases for submit_work_impl function."""
    
    def test_submit_work_advances_state(self):
        """
        Comprehensive integration test that follows the AC Verification steps using mocked components:
        1. Mock the necessary components
        2. Set up a PlanTaskTool in the orchestrator
        3. Call submit_work_impl("TS-01", artifact={"context_summary": "..."})
        4. Assert successful response and next_prompt for review_context
        5. Check orchestrator.active_tools state is now REVIEW_CONTEXT
        6. Verify artifact was persisted to scratchpad
        """
        from unittest.mock import patch
        
        # 1. Set up test task and tool
        task_id = "TS-01"
        test_task = Task(
            task_id=task_id,
            title="Test Task for Submit Work",
            context="Testing the submit_work tool functionality in the Alfred workflow",
            implementation_details="Verify that work artifacts can be submitted and state transitions work correctly"
        )
        
        # 2. Create and register a PlanTaskTool instance
        from src.alfred.core.workflow import PlanTaskTool
        tool_instance = PlanTaskTool(task_id=task_id, persona_name="planning")
        orchestrator.active_tools[task_id] = tool_instance
        
        # Verify initial state
        assert tool_instance.state == PlanTaskState.CONTEXTUALIZE.value
        
        # 3. Mock dependencies for submit_work_impl
        with (
            patch('src.alfred.tools.submit_work.load_task', return_value=test_task),
            patch('src.alfred.tools.submit_work.artifact_manager') as mock_artifact_manager,
            patch('src.alfred.tools.submit_work.load_persona', return_value={"name": "planning"}),
            patch('src.alfred.tools.submit_work.prompter') as mock_prompter
        ):
            mock_prompter.generate_prompt.return_value = "Please review the submitted context analysis"
            
            # 4. Call submit_work_impl
            test_artifact = {"context_summary": "Analyzed requirements and identified key components"}
            submit_response = submit_work_impl(task_id, test_artifact)
            
            # 5. Assert successful response
            assert submit_response.status == "success"
            assert "Work submitted. Awaiting review." in submit_response.message
            assert submit_response.next_prompt is not None
            
            # 6. Check state transition occurred
            assert tool_instance.state == PlanTaskState.REVIEW_CONTEXT.value
            
            # 7. Verify artifact was persisted
            mock_artifact_manager.append_to_scratchpad.assert_called_once()
            call_args = mock_artifact_manager.append_to_scratchpad.call_args
            assert call_args[0][0] == task_id  # task_id argument
            assert "### Submission for State: `contextualize`" in call_args[0][1]  # rendered content
            assert json.dumps(test_artifact, indent=2) in call_args[0][1]
            
            # 8. Verify prompter was called with artifact content
            mock_prompter.generate_prompt.assert_called_once()
            prompt_call_args = mock_prompter.generate_prompt.call_args
            assert prompt_call_args[1]['additional_context']['artifact_content'] == json.dumps(test_artifact, indent=2)
        
        # Clean up
        orchestrator.active_tools.pop(task_id, None)
    
    def test_submit_work_fails_if_no_active_tool(self):
        """Test that submit_work_impl fails gracefully when no active tool exists."""
        # Clear any existing active tools
        orchestrator.active_tools.clear()
        
        # Attempt to submit work for non-existent task
        artifact = {"test": "data"}
        result = submit_work_impl("NONEXISTENT-01", artifact)
        
        # Verify error response
        assert result.status == "error"
        assert "No active tool found for task 'NONEXISTENT-01'" in result.message
        assert "Cannot submit work" in result.message
