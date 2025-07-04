"""
Unit tests for state machine builder functionality.
"""

import pytest
from enum import Enum
from unittest.mock import Mock, patch
from transitions.core import Machine

from src.alfred.core.state_machine_builder import workflow_builder
from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.core.discovery_workflow import PlanTaskState
from src.alfred.constants import Triggers


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
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        assert builder is not None
        assert hasattr(builder, "multi_step_with_reviews")
        assert hasattr(builder, "simple_dispatch_work_done")

    def test_multi_step_with_reviews_pattern(self):
        """Test multi-step with reviews pattern creation."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        # Create a multi-step workflow with test states
        work_states = [MockTaskState.STATE_A, MockTaskState.STATE_B, MockTaskState.STATE_C]
        terminal_state = MockTaskState.VERIFIED

        machine = builder.multi_step_with_reviews(work_states=work_states, terminal_state=terminal_state)

        assert isinstance(machine, Machine)
        assert tool.state == MockTaskState.STATE_A  # Should start at first work state

    def test_simple_dispatch_work_done_pattern(self):
        """Test simple dispatch-work-done pattern creation."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        # Create a simple workflow
        dispatch_state = MockTaskState.STATE_A
        work_state = MockTaskState.STATE_B
        terminal_state = MockTaskState.VERIFIED

        machine = builder.simple_dispatch_work_done(dispatch_state=dispatch_state, work_state=work_state, terminal_state=terminal_state)

        assert isinstance(machine, Machine)
        assert tool.state == dispatch_state  # Should start at dispatch state

    def test_multi_step_state_transitions(self):
        """Test state transitions in multi-step pattern."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        work_states = [MockTaskState.STATE_A, MockTaskState.STATE_B]
        terminal_state = MockTaskState.VERIFIED

        machine = builder.multi_step_with_reviews(work_states=work_states, terminal_state=terminal_state)

        # Test progression through states
        assert tool.state == MockTaskState.STATE_A

        # Trigger submission should move to review
        tool.submit()
        expected_review_state = f"review_{MockTaskState.STATE_A.value}"
        assert tool.state == expected_review_state

        # Approve should move to next work state
        tool.approve()
        assert tool.state == MockTaskState.STATE_B

    def test_simple_pattern_state_transitions(self):
        """Test state transitions in simple pattern."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        dispatch_state = MockTaskState.STATE_A
        work_state = MockTaskState.STATE_B
        terminal_state = MockTaskState.VERIFIED

        machine = builder.simple_dispatch_work_done(dispatch_state=dispatch_state, work_state=work_state, terminal_state=terminal_state)

        # Test progression through states
        assert tool.state == dispatch_state

        # Trigger work should move to work state
        tool.work()
        assert tool.state == work_state

        # Submit should move to review
        tool.submit()
        expected_review_state = f"review_{work_state.value}"
        assert tool.state == expected_review_state

        # Approve should move to terminal state
        tool.approve()
        assert tool.state == terminal_state

    def test_review_state_generation(self):
        """Test that review states are properly generated."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        work_states = [MockTaskState.STATE_A, MockTaskState.STATE_B]
        terminal_state = MockTaskState.VERIFIED

        machine = builder.multi_step_with_reviews(work_states=work_states, terminal_state=terminal_state)

        # Check that review states exist in the machine
        all_states = [state.name for state in machine.states]

        assert f"review_{MockTaskState.STATE_A.value}" in all_states
        assert f"review_{MockTaskState.STATE_B.value}" in all_states

    def test_invalid_state_configuration(self):
        """Test error handling for invalid state configurations."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        # Test with empty work states
        with pytest.raises(ValueError):
            builder.multi_step_with_reviews(work_states=[], terminal_state=MockTaskState.VERIFIED)

        # Test with None terminal state
        with pytest.raises(ValueError):
            builder.multi_step_with_reviews(work_states=[MockTaskState.STATE_A], terminal_state=None)

    def test_trigger_validation(self):
        """Test that only valid triggers are accepted."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        work_states = [MockTaskState.STATE_A]
        terminal_state = MockTaskState.VERIFIED

        machine = builder.multi_step_with_reviews(work_states=work_states, terminal_state=terminal_state)

        # Valid triggers should work
        assert hasattr(tool, Triggers.SUBMIT.value)
        assert hasattr(tool, Triggers.APPROVE.value)
        assert hasattr(tool, Triggers.REQUEST_REVISION.value)

        # Invalid triggers should raise AttributeError
        with pytest.raises(AttributeError):
            tool.invalid_trigger()

    def test_state_persistence(self):
        """Test that state changes are persisted."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        work_states = [MockTaskState.STATE_A, MockTaskState.STATE_B]
        terminal_state = MockTaskState.VERIFIED

        machine = builder.multi_step_with_reviews(work_states=work_states, terminal_state=terminal_state)

        initial_state = tool.state

        # Make a state change
        tool.submit()

        # Verify state changed and is different from initial
        assert tool.state != initial_state

        # Verify state is saved (through mock)
        assert tool.test_data != {}

    def test_revision_cycle(self):
        """Test revision request and reversion to work state."""
        tool = MockWorkflowTool("TEST-001")
        builder = workflow_builder(tool)

        work_states = [MockTaskState.STATE_A]
        terminal_state = MockTaskState.VERIFIED

        machine = builder.multi_step_with_reviews(work_states=work_states, terminal_state=terminal_state)

        # Start in work state
        assert tool.state == MockTaskState.STATE_A

        # Submit work for review
        tool.submit()
        review_state = tool.state
        assert "review_" in review_state

        # Request revision - should go back to work state
        tool.request_revision()
        assert tool.state == MockTaskState.STATE_A

    def test_real_plan_task_states(self):
        """Test builder with actual Discovery Planning states."""
        # Use the actual PlanTaskTool to test the real state machine
        from src.alfred.core.discovery_workflow import PlanTaskTool

        tool = PlanTaskTool("PLAN-001")

        # Test that the state machine was created successfully
        assert tool.machine is not None
        assert tool.state == PlanTaskState.DISCOVERY.value

        # Test that required triggers exist
        assert hasattr(tool, "submit_discovery")
        assert hasattr(tool, "submit_clarification")
        assert hasattr(tool, "submit_contracts")
        assert hasattr(tool, "submit_implementation_plan")
        assert hasattr(tool, "submit_validation")

        # Test artifact mapping
        expected_mappings = {
            PlanTaskState.DISCOVERY: "ContextDiscoveryArtifact",
            PlanTaskState.CLARIFICATION: "ClarificationArtifact",
            PlanTaskState.CONTRACTS: "ContractDesignArtifact",
            PlanTaskState.IMPLEMENTATION_PLAN: "ImplementationPlanArtifact",
            PlanTaskState.VALIDATION: "ValidationArtifact",
        }

        for state, expected_class in expected_mappings.items():
            assert state in tool.artifact_map
            assert tool.artifact_map[state].__name__ == expected_class
