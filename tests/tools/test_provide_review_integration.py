# tests/tools/test_provide_review_integration.py
"""
Integration tests for provide_review tool using real file system and workflow.
"""

import pytest
from pathlib import Path

from src.alfred.models.schemas import Task, TaskStatus
from src.alfred.tools.plan_task import plan_task_impl
from src.alfred.tools.submit_work import submit_work_impl
from src.alfred.tools.provide_review import provide_review_impl
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.constants import ResponseStatus, PlanTaskStates, ToolName
from tests.conftest import AlfredTestProject


class TestProvideReviewIntegration:
    """Integration tests for provide_review functionality."""

    def setup_method(self):
        """Clear orchestrator state before each test."""
        orchestrator.active_tools.clear()

    def setup_test_environment(self, alfred_test_project: AlfredTestProject):
        """Set up the test environment with necessary files and directories."""
        # Initialize project
        alfred_test_project.initialize()

        # Create persona file
        personas_dir = alfred_test_project.alfred_dir / "personas"
        personas_dir.mkdir(exist_ok=True)
        (personas_dir / "planning.yml").write_text("""
name: Alex
title: Solution Architect
greeting: "Hey there! I'm Alex. Let's build something great together."
style: "Professional yet approachable. I explain complex technical concepts in simple terms."
thinking_methodology:
  - Break down complex problems into smaller components
  - Consider architectural trade-offs and maintainability
  - Always validate assumptions before proceeding
""")

        # Create prompt templates
        prompts_dir = alfred_test_project.alfred_dir / "templates" / "prompts" / "plan_task"
        prompts_dir.mkdir(parents=True, exist_ok=True)

        # Create all necessary prompt templates
        prompt_templates = {
            "contextualize": """# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: contextualize

Analyze the task context for {{ task.title }}.
{% if additional_context.feedback_notes %}
### Revision Feedback
{{ additional_context.feedback_notes }}
{% endif %}
Submit your context analysis.""",
            "review_context": """# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_context

Review the context analysis.
{% if additional_context.feedback_notes %}
Feedback: {{ additional_context.feedback_notes }}
{% endif %}""",
            "strategize": """# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: strategize

Create technical strategy for {{ task.title }}.""",
            "review_strategy": """# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_strategy

Review the strategy.""",
        }

        for template_name, content in prompt_templates.items():
            (prompts_dir / f"{template_name}.md").write_text(content)

        # Create artifact templates
        artifacts_dir = alfred_test_project.alfred_dir / "templates" / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

    @pytest.mark.asyncio
    async def test_provide_review_approval_transitions_state(self, alfred_test_project: AlfredTestProject):
        """Test that approval correctly transitions the workflow state."""
        # Setup environment
        self.setup_test_environment(alfred_test_project)

        # Create a test task
        task = Task(
            task_id="TEST-001",
            title="Create User Authentication Service",
            context="Need to implement user authentication",
            implementation_details="Use JWT tokens for authentication",
            acceptance_criteria=["Users can log in", "Users can log out"],
            task_status=TaskStatus.NEW,
        )
        alfred_test_project.create_task_file(task)

        # Patch all required modules with test settings
        from unittest.mock import patch

        with (
            patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings),
            patch("src.alfred.orchestration.persona_loader.settings", alfred_test_project.settings),
            patch("src.alfred.core.prompter.settings", alfred_test_project.settings),
            patch("src.alfred.lib.artifact_manager.settings", alfred_test_project.settings),
            patch("src.alfred.state.manager.settings", alfred_test_project.settings),
        ):
            # Create new instances that will use the patched settings
            from src.alfred.core.prompter import Prompter
            from src.alfred.lib.artifact_manager import ArtifactManager

            test_prompter = Prompter()
            test_artifact_manager = ArtifactManager()

            # Patch state recovery to prevent loading persisted state
            with patch("src.alfred.state.recovery.ToolRecovery.recover_tool", return_value=None):
                with (
                    patch("src.alfred.tools.plan_task.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.artifact_manager", test_artifact_manager),
                    patch("src.alfred.tools.provide_review.prompter", test_prompter),
                    patch("src.alfred.config.settings.settings", alfred_test_project.settings),
                ):
                    # Start planning
                    result = await plan_task_impl("TEST-001")
                    assert result.status == ResponseStatus.SUCCESS
                    assert "TEST-001" in orchestrator.active_tools

                    # Submit context analysis
                    context_artifact = {
                        "context_summary": "Building a JWT-based authentication service",
                        "affected_files": ["src/auth/service.py", "src/auth/models.py"],
                        "questions_for_developer": [],
                    }

                    result = submit_work_impl("TEST-001", context_artifact)
                    assert result.status == ResponseStatus.SUCCESS

                    # Get current tool state
                    tool = orchestrator.active_tools["TEST-001"]
                    assert tool.state == PlanTaskStates.REVIEW_CONTEXT

                    # Approve the context
                    result = provide_review_impl("TEST-001", is_approved=True, feedback_notes="")
                    assert result.status == ResponseStatus.SUCCESS
                    assert "approved" in result.message.lower()

                    # Check state transitioned
                    assert tool.state == PlanTaskStates.STRATEGIZE
                    assert result.next_prompt is not None
                    assert "strategize" in result.next_prompt.lower()

    @pytest.mark.asyncio
    async def test_provide_review_rejection_returns_to_working_state(self, alfred_test_project: AlfredTestProject):
        """Test that rejection returns to the working state with feedback."""
        # Setup environment
        self.setup_test_environment(alfred_test_project)

        # Create a test task
        task = Task(
            task_id="TEST-002",
            title="Implement Data Export Feature",
            context="Users need to export their data",
            implementation_details="Support CSV and JSON formats",
            acceptance_criteria=["Export to CSV", "Export to JSON"],
            task_status=TaskStatus.NEW,
        )
        alfred_test_project.create_task_file(task)

        # Patch all required modules with test settings
        from unittest.mock import patch

        with (
            patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings),
            patch("src.alfred.orchestration.persona_loader.settings", alfred_test_project.settings),
            patch("src.alfred.core.prompter.settings", alfred_test_project.settings),
            patch("src.alfred.lib.artifact_manager.settings", alfred_test_project.settings),
            patch("src.alfred.state.manager.settings", alfred_test_project.settings),
        ):
            # Create new instances that will use the patched settings
            from src.alfred.core.prompter import Prompter
            from src.alfred.lib.artifact_manager import ArtifactManager

            test_prompter = Prompter()
            test_artifact_manager = ArtifactManager()

            # Patch state recovery to prevent loading persisted state
            with patch("src.alfred.state.recovery.ToolRecovery.recover_tool", return_value=None):
                with (
                    patch("src.alfred.tools.plan_task.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.artifact_manager", test_artifact_manager),
                    patch("src.alfred.tools.provide_review.prompter", test_prompter),
                    patch("src.alfred.config.settings.settings", alfred_test_project.settings),
                ):
                    # Start planning and submit initial work
                    await plan_task_impl("TEST-002")

                    context_artifact = {"context_summary": "Data export feature", "affected_files": ["src/export/service.py"], "questions_for_developer": []}
                    result = submit_work_impl("TEST-002", context_artifact)
                    assert result.status == ResponseStatus.SUCCESS

                    # Verify we're in review state
                    tool = orchestrator.active_tools["TEST-002"]
                    assert tool.state == PlanTaskStates.REVIEW_CONTEXT

                    # Reject with feedback
                    feedback = "Please provide more detail about the export formats and data structure"
                    result = provide_review_impl("TEST-002", is_approved=False, feedback_notes=feedback)

                    assert result.status == ResponseStatus.SUCCESS
                    assert "revision" in result.message.lower()

                    # Check state returned to contextualize
                    assert tool.state == PlanTaskStates.CONTEXTUALIZE

                    # Check feedback is in the prompt
                    assert feedback in result.next_prompt

    @pytest.mark.asyncio
    async def test_provide_review_saves_execution_plan_on_approval(self, alfred_test_project: AlfredTestProject):
        """Test that execution plan is saved to JSON when plan is approved."""
        # Setup environment
        self.setup_test_environment(alfred_test_project)

        # Add missing prompt templates for full workflow
        prompts_dir = alfred_test_project.alfred_dir / "templates" / "prompts" / "plan_task"

        additional_templates = {"design": "Design template", "review_design": "Review design template", "generate_subtasks": "Generate subtasks template", "review_plan": "Review plan template"}

        for name, content in additional_templates.items():
            (prompts_dir / f"{name}.md").write_text(content)

        # Create task
        task = Task(
            task_id="TEST-003",
            title="Add Logging System",
            context="Need comprehensive logging",
            implementation_details="Use Python logging",
            acceptance_criteria=["Log to file", "Log levels"],
            task_status=TaskStatus.NEW,
        )
        alfred_test_project.create_task_file(task)

        # Patch all required modules with test settings
        from unittest.mock import patch

        with (
            patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings),
            patch("src.alfred.orchestration.persona_loader.settings", alfred_test_project.settings),
            patch("src.alfred.core.prompter.settings", alfred_test_project.settings),
            patch("src.alfred.lib.artifact_manager.settings", alfred_test_project.settings),
            patch("src.alfred.state.manager.settings", alfred_test_project.settings),
        ):
            # Create new instances that will use the patched settings
            from src.alfred.core.prompter import Prompter
            from src.alfred.lib.artifact_manager import ArtifactManager

            test_prompter = Prompter()
            test_artifact_manager = ArtifactManager()

            # Patch state recovery to prevent loading persisted state
            with patch("src.alfred.state.recovery.ToolRecovery.recover_tool", return_value=None):
                with (
                    patch("src.alfred.tools.plan_task.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.artifact_manager", test_artifact_manager),
                    patch("src.alfred.tools.provide_review.prompter", test_prompter),
                    patch("src.alfred.config.settings.settings", alfred_test_project.settings),
                ):
                    # Progress through workflow to plan review state
                    await plan_task_impl("TEST-003")
                    tool = orchestrator.active_tools["TEST-003"]

                    # Mock progression to review_plan state with execution plan
                    tool.state = PlanTaskStates.REVIEW_PLAN
                    tool.context_store["execution_plan_artifact"] = {
                        "subtasks": [
                            {
                                "subtask_id": "ST-1",
                                "title": "Create logging configuration",
                                "location": "src/utils/logging.py",
                                "operation": "CREATE",
                                "specification": ["Create logging setup"],
                                "test": ["Verify logging works"],
                            }
                        ]
                    }

                    # Approve the plan
                    result = provide_review_impl("TEST-003", is_approved=True, feedback_notes="")
                    assert result.status == ResponseStatus.SUCCESS

                    # Check execution plan was saved
                    execution_plan_path = alfred_test_project.settings.workspace_dir / "TEST-003" / "execution_plan.json"
                    assert execution_plan_path.exists()

                    # Verify content
                    import json

                    with open(execution_plan_path) as f:
                        saved_plan = json.load(f)

                    assert "subtasks" in saved_plan
                    assert len(saved_plan["subtasks"]) == 1
                    assert saved_plan["subtasks"][0]["subtask_id"] == "ST-1"

    @pytest.mark.asyncio
    async def test_provide_review_handles_terminal_state(self, alfred_test_project: AlfredTestProject):
        """Test that terminal state completes the tool and updates task status."""
        # Setup environment
        self.setup_test_environment(alfred_test_project)

        # Create task
        task = Task(
            task_id="TEST-004",
            title="Create API Documentation",
            context="Document all API endpoints",
            implementation_details="Use OpenAPI spec",
            acceptance_criteria=["All endpoints documented"],
            task_status=TaskStatus.PLANNING,
        )
        alfred_test_project.create_task_file(task)

        # Patch all required modules with test settings
        from unittest.mock import patch

        with (
            patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings),
            patch("src.alfred.orchestration.persona_loader.settings", alfred_test_project.settings),
            patch("src.alfred.core.prompter.settings", alfred_test_project.settings),
            patch("src.alfred.lib.artifact_manager.settings", alfred_test_project.settings),
            patch("src.alfred.state.manager.settings", alfred_test_project.settings),
        ):
            # Create new instances that will use the patched settings
            from src.alfred.core.prompter import Prompter
            from src.alfred.lib.artifact_manager import ArtifactManager

            test_prompter = Prompter()
            test_artifact_manager = ArtifactManager()

            # Patch state recovery to prevent loading persisted state
            with patch("src.alfred.state.recovery.ToolRecovery.recover_tool", return_value=None):
                with (
                    patch("src.alfred.tools.plan_task.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.prompter", test_prompter),
                    patch("src.alfred.tools.submit_work.artifact_manager", test_artifact_manager),
                    patch("src.alfred.tools.provide_review.prompter", test_prompter),
                    patch("src.alfred.config.settings.settings", alfred_test_project.settings),
                ):
                    # Start planning
                    await plan_task_impl("TEST-004")
                    tool = orchestrator.active_tools["TEST-004"]

                    # Mock terminal state transition
                    tool.state = PlanTaskStates.REVIEW_PLAN

                    # Make the next state verified (terminal)
                    with patch.object(tool.machine, "get_transitions") as mock_transitions:
                        mock_transition = type("MockTransition", (), {"dest": PlanTaskStates.VERIFIED})()
                        mock_transitions.return_value = [mock_transition]

                        # Mock the state transition to set terminal
                        original_ai_approve = tool.ai_approve

                        def mock_approve():
                            original_ai_approve()
                            tool.state = PlanTaskStates.VERIFIED

                        with patch.object(tool, "ai_approve", side_effect=mock_approve):
                            # Mock is_terminal property to return True after approval
                            with patch.object(type(tool), "is_terminal", new_callable=lambda: property(lambda self: self.state == PlanTaskStates.VERIFIED)):
                                result = provide_review_impl("TEST-004", is_approved=True, feedback_notes="")

                    assert result.status == ResponseStatus.SUCCESS
                    assert "completed" in result.message.lower()
                    assert "TEST-004" not in orchestrator.active_tools

                    # Check task status was updated
                    updated_task = alfred_test_project.load_task("TEST-004")
                    assert updated_task.task_status == TaskStatus.READY_FOR_DEVELOPMENT
