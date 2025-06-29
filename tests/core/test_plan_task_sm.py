# tests/core/test_plan_task_sm.py
import pytest
from src.alfred.core.workflow import PlanTaskTool, PlanTaskState


class TestPlanTaskStateMachine:
    """Test suite for PlanTaskTool state machine behavior."""

    def test_initial_state(self):
        """Test that PlanTaskTool starts in CONTEXTUALIZE state."""
        tool = PlanTaskTool(task_id="TS-01")
        assert tool.state == PlanTaskState.CONTEXTUALIZE.value

    def test_full_success_flow(self):
        """Test the complete success path through all states to VERIFIED."""
        tool = PlanTaskTool(task_id="TS-01")

        # Start in CONTEXTUALIZE
        assert tool.state == PlanTaskState.CONTEXTUALIZE.value

        # CONTEXTUALIZE -> REVIEW_CONTEXT -> STRATEGIZE
        tool.submit_contextualize()
        assert tool.state == PlanTaskState.REVIEW_CONTEXT.value
        tool.ai_approve()
        assert tool.state == PlanTaskState.STRATEGIZE.value

        # STRATEGIZE -> REVIEW_STRATEGY -> DESIGN
        tool.submit_strategize()
        assert tool.state == PlanTaskState.REVIEW_STRATEGY.value
        tool.ai_approve()
        assert tool.state == PlanTaskState.DESIGN.value

        # DESIGN -> REVIEW_DESIGN -> GENERATE_SUBTASKS
        tool.submit_design()
        assert tool.state == PlanTaskState.REVIEW_DESIGN.value
        tool.ai_approve()
        assert tool.state == PlanTaskState.GENERATE_SUBTASKS.value

        # GENERATE_SUBTASKS -> REVIEW_PLAN -> VERIFIED
        tool.submit_generate_subtasks()
        assert tool.state == PlanTaskState.REVIEW_PLAN.value
        tool.ai_approve()
        assert tool.state == PlanTaskState.VERIFIED.value

    def test_rejection_at_design_review(self):
        """Test request_revision from REVIEW_DESIGN state returns to DESIGN."""
        tool = PlanTaskTool(task_id="TS-01")

        # Move to DESIGN state
        tool.submit_contextualize()
        tool.ai_approve()
        tool.submit_strategize()
        tool.ai_approve()
        assert tool.state == PlanTaskState.DESIGN.value

        # Submit design for review
        tool.submit_design()
        assert tool.state == PlanTaskState.REVIEW_DESIGN.value

        # Request revision - should go back to DESIGN
        tool.request_revision()
        assert tool.state == PlanTaskState.DESIGN.value

    def test_revision_cycle_contextualize(self):
        """Test revision cycle at contextualize stage."""
        tool = PlanTaskTool(task_id="TS-01")

        # Submit contextualize work
        tool.submit_contextualize()
        assert tool.state == PlanTaskState.REVIEW_CONTEXT.value

        # Request revision - should go back to CONTEXTUALIZE
        tool.request_revision()
        assert tool.state == PlanTaskState.CONTEXTUALIZE.value

        # Can resubmit and proceed
        tool.submit_contextualize()
        assert tool.state == PlanTaskState.REVIEW_CONTEXT.value
        tool.ai_approve()
        assert tool.state == PlanTaskState.STRATEGIZE.value

    def test_revision_cycle_strategize(self):
        """Test revision cycle at strategize stage."""
        tool = PlanTaskTool(task_id="TS-01")

        # Move to STRATEGIZE state
        tool.submit_contextualize()
        tool.ai_approve()
        assert tool.state == PlanTaskState.STRATEGIZE.value

        # Submit strategize work
        tool.submit_strategize()
        assert tool.state == PlanTaskState.REVIEW_STRATEGY.value

        # Request revision - should go back to STRATEGIZE
        tool.request_revision()
        assert tool.state == PlanTaskState.STRATEGIZE.value

    def test_revision_cycle_generate_subtasks(self):
        """Test revision cycle at generate_subtasks stage."""
        tool = PlanTaskTool(task_id="TS-01")

        # Move to GENERATE_SUBTASKS state
        tool.submit_contextualize()
        tool.ai_approve()
        tool.submit_strategize()
        tool.ai_approve()
        tool.submit_design()
        tool.ai_approve()
        assert tool.state == PlanTaskState.GENERATE_SUBTASKS.value

        # Submit generate_subtasks work
        tool.submit_generate_subtasks()
        assert tool.state == PlanTaskState.REVIEW_PLAN.value

        # Request revision - should go back to GENERATE_SUBTASKS
        tool.request_revision()
        assert tool.state == PlanTaskState.GENERATE_SUBTASKS.value
