# tests/tools/test_planning_lifecycle.py
import pytest
from pathlib import Path
from unittest.mock import patch

from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.models.planning_artifacts import StrategyArtifact
from src.alfred.tools.plan_task import plan_task_impl
from src.alfred.tools.submit_work import submit_work_impl
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.core.workflow import PlanTaskState
from tests.conftest import AlfredTestProject


@pytest.mark.asyncio
async def test_strategy_phase_submission_and_review(alfred_test_project: AlfredTestProject):
    """
    Tests the strategy phase of the plan_task lifecycle.
    Advances through CONTEXTUALIZE phase and into STRATEGIZE state.
    Tests submission of StrategyArtifact and transition to REVIEW_STRATEGY.
    """
    # --- ARRANGE ---
    # 1. Initialize a real project in a temporary directory
    alfred_test_project.initialize()

    # 2. Create persona and prompt template files
    personas_dir = alfred_test_project.alfred_dir / "personas"
    personas_dir.mkdir(exist_ok=True)
    (personas_dir / "planning.yml").write_text("""
name: Alex
title: Senior Software Engineer
thinking_methodology:
  - Break down complex problems into smaller components
  - Consider architectural trade-offs and maintainability
  - Always validate assumptions before proceeding
""")

    # 3. Create prompt template files
    prompts_dir = alfred_test_project.alfred_dir / "templates" / "prompts" / "plan_task"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    # Create contextualize prompt (needed to get past the first phase)
    (prompts_dir / "contextualize.md").write_text("""
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: contextualize

Analyze the task context for {{ task.title }}.
""")

    # Create strategize prompt
    (prompts_dir / "strategize.md").write_text("""
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: strategize

Context is verified. Create the high-level technical strategy for '{{ task.title }}'.

### **Required Action**
You MUST now call `alfred.submit_work` with a `StrategyArtifact`.
""")

    # Create review_context prompt
    (prompts_dir / "review_context.md").write_text("""
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_context

Review the context and call `alfred.provide_review`.
""")

    # Create review_strategy prompt
    (prompts_dir / "review_strategy.md").write_text("""
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_strategy

Review the strategy and call `alfred.provide_review`.
""")

    # 4. Create a valid Task object and save it to the test project's file system
    task = Task(
        task_id="AL-STRAT-01",
        title="Test Strategy Implementation",
        context="Implement a new user authentication system",
        implementation_details="Add JWT-based authentication with role-based access control",
    )
    alfred_test_project.create_task_file(task)

    # 5. Patch the global settings and create a test-specific prompter
    with (
        patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings),
        patch("src.alfred.orchestration.persona_loader.settings", alfred_test_project.settings),
        patch("src.alfred.core.prompter.settings", alfred_test_project.settings),
        patch("src.alfred.lib.artifact_manager.settings", alfred_test_project.settings),
    ):
        # Create a new prompter instance that will use the patched settings
        from src.alfred.core.prompter import Prompter

        test_prompter = Prompter()

        # Create a new artifact_manager instance that will use the patched settings
        from src.alfred.lib.artifact_manager import ArtifactManager

        test_artifact_manager = ArtifactManager()

        with (
            patch("src.alfred.tools.plan_task.prompter", test_prompter),
            patch("src.alfred.tools.submit_work.prompter", test_prompter),
            patch("src.alfred.tools.submit_work.artifact_manager", test_artifact_manager),
        ):
            # --- ACT PHASE 1: Start planning ---
            # 6. Run the plan_task tool to initiate planning
            result: ToolResponse = await plan_task_impl("AL-STRAT-01")

            # --- ASSERT PHASE 1: Verify initial state ---
            assert result.status == "success"
            assert "Planning initiated" in result.message

            # Verify the orchestrator has the tool in CONTEXTUALIZE state
            assert "AL-STRAT-01" in orchestrator.active_tools
            plan_tool = orchestrator.active_tools["AL-STRAT-01"]
            assert plan_tool.state == PlanTaskState.CONTEXTUALIZE.value

            # --- ACT PHASE 2: Submit context analysis to move to STRATEGIZE ---
            # 7. Submit a mock context analysis artifact to advance to STRATEGIZE
            from src.alfred.models.planning_artifacts import ContextAnalysisArtifact

            context_artifact = ContextAnalysisArtifact(context_summary="User authentication system needed", affected_files=["src/auth/", "src/models/user.py"], questions_for_developer=[])

            context_result = submit_work_impl("AL-STRAT-01", context_artifact.model_dump())
            assert context_result.status == "success"

            # Simulate AI self-approval to move to STRATEGIZE
            plan_tool.ai_approve()
            assert plan_tool.state == PlanTaskState.STRATEGIZE.value

            # --- ACT PHASE 3: Submit strategy artifact ---
            # 8. Submit a valid StrategyArtifact
            strategy_artifact = StrategyArtifact(
                high_level_strategy="Implement JWT-based authentication with middleware",
                key_components=["AuthMiddleware", "JWTTokenManager", "UserRoleService"],
                new_dependencies=["pyjwt", "passlib"],
                risk_analysis="JWT secret key management and token refresh strategy needed",
            )

            strategy_result = submit_work_impl("AL-STRAT-01", strategy_artifact.model_dump())

            # --- ASSERT PHASE 3: Verify strategy submission ---
            assert strategy_result.status == "success"
            assert "Work submitted. Awaiting review." in strategy_result.message

            # Verify the state machine transitioned to REVIEW_STRATEGY
            assert plan_tool.state == PlanTaskState.REVIEW_STRATEGY.value

            # --- ASSERT PHASE 4: Verify scratchpad contains strategy ---
            # 9. Verify the scratchpad.md file contains the rendered StrategyArtifact
            scratchpad_path = alfred_test_project.settings.workspace_dir / "AL-STRAT-01" / "scratchpad.md"
            assert scratchpad_path.exists()

            scratchpad_content = scratchpad_path.read_text()
            assert "JWT-based authentication with middleware" in scratchpad_content
            assert "AuthMiddleware" in scratchpad_content
            assert "pyjwt" in scratchpad_content
            assert "JWT secret key management" in scratchpad_content
