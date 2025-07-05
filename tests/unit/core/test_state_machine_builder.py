"""
Unit tests for state machine builder functionality.
"""

import pytest
from enum import Enum

from alfred.core.state_machine_builder import workflow_builder
from alfred.core.workflow import BaseWorkflowTool


class MockTaskState(str, Enum):
    """Mock enum for state machine testing."""

    STATE_A = "state_a"
    STATE_B = "state_b"
    STATE_C = "state_c"
    VERIFIED = "verified"


class MockWorkflowTool(BaseWorkflowTool):
    """Mock workflow tool for testing."""

    def __init__(self, task_id: str):
        super().__init__(task_id, "mock_tool")
        self.test_data = {}

    def _load_tool_state(self):
        return self.test_data

    def _save_tool_state(self, state_data):
        self.test_data = state_data


class TestWorkflowBuilder:
    """Test the workflow builder functionality."""

    def test_builder_initialization(self):
        """Test workflow builder can be initialized."""
        builder = workflow_builder

        assert builder is not None
        assert hasattr(builder, "build_workflow_with_reviews")
        assert hasattr(builder, "build_simple_workflow")

    def test_multi_step_with_reviews_pattern(self):
        """Test multi-step with reviews pattern creation."""
        builder = workflow_builder

        # Create a multi-step workflow with test states
        work_states = [MockTaskState.STATE_A, MockTaskState.STATE_B, MockTaskState.STATE_C]
        terminal_state = MockTaskState.VERIFIED
        initial_state = MockTaskState.STATE_A

        workflow_config = builder.build_workflow_with_reviews(work_states=work_states, terminal_state=terminal_state, initial_state=initial_state)

        assert isinstance(workflow_config, dict)
        assert "states" in workflow_config
        assert "transitions" in workflow_config
        assert "initial" in workflow_config
        assert workflow_config["initial"] == MockTaskState.STATE_A

    def test_simple_dispatch_work_done_pattern(self):
        """Test simple dispatch-work-done pattern creation."""
        builder = workflow_builder

        # Create a simple workflow
        dispatch_state = MockTaskState.STATE_A
        work_state = MockTaskState.STATE_B
        terminal_state = MockTaskState.VERIFIED

        workflow_config = builder.build_simple_workflow(dispatch_state=dispatch_state, work_state=work_state, terminal_state=terminal_state)

        assert isinstance(workflow_config, dict)
        assert "states" in workflow_config
        assert "transitions" in workflow_config
        assert "initial" in workflow_config
        assert workflow_config["initial"] == dispatch_state

    def test_review_state_generation(self):
        """Test that review states are properly generated."""
        builder = workflow_builder

        work_states = [MockTaskState.STATE_A, MockTaskState.STATE_B]
        terminal_state = MockTaskState.VERIFIED
        initial_state = MockTaskState.STATE_A

        workflow_config = builder.build_workflow_with_reviews(work_states=work_states, terminal_state=terminal_state, initial_state=initial_state)

        # Check that review states are created
        states = workflow_config["states"]

        # Should have the work states
        assert MockTaskState.STATE_A in states
        assert MockTaskState.STATE_B in states
        assert MockTaskState.VERIFIED in states

        # Should have AI and human review states for each work state
        assert f"{MockTaskState.STATE_A.value}_awaiting_ai_review" in states
        assert f"{MockTaskState.STATE_A.value}_awaiting_human_review" in states
        assert f"{MockTaskState.STATE_B.value}_awaiting_ai_review" in states
        assert f"{MockTaskState.STATE_B.value}_awaiting_human_review" in states

    def test_workflow_transitions_structure(self):
        """Test that transitions are properly structured."""
        builder = workflow_builder

        work_states = [MockTaskState.STATE_A]
        terminal_state = MockTaskState.VERIFIED
        initial_state = MockTaskState.STATE_A

        workflow_config = builder.build_workflow_with_reviews(work_states=work_states, terminal_state=terminal_state, initial_state=initial_state)

        transitions = workflow_config["transitions"]
        assert isinstance(transitions, list)
        assert len(transitions) > 0

        # Each transition should have required fields
        for transition in transitions:
            assert "trigger" in transition
            assert "source" in transition
            assert "dest" in transition

    def test_simple_workflow_structure(self):
        """Test simple workflow structure."""
        builder = workflow_builder

        dispatch_state = MockTaskState.STATE_A
        work_state = MockTaskState.STATE_B
        terminal_state = MockTaskState.VERIFIED

        workflow_config = builder.build_simple_workflow(dispatch_state=dispatch_state, work_state=work_state, terminal_state=terminal_state)

        # Check basic structure
        assert workflow_config["initial"] == dispatch_state
        states = workflow_config["states"]
        assert dispatch_state in states
        assert work_state in states
        assert terminal_state in states

        # Should have review states for the work state
        assert f"{work_state.value}_awaiting_ai_review" in states
        assert f"{work_state.value}_awaiting_human_review" in states
