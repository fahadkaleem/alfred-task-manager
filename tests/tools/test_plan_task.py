# tests/tools/test_plan_task.py
import pytest
from pathlib import Path
from unittest.mock import patch

from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.plan_task import plan_task_impl
from src.alfred.orchestration.orchestrator import orchestrator
from tests.conftest import AlfredTestProject


@pytest.mark.asyncio
async def test_plan_task_success(alfred_test_project: AlfredTestProject):
    """
    Tests the full success path of plan_task using a real file system.
    Uses minimal patching only for settings redirection - NO business logic mocking.
    """
    # --- ARRANGE ---
    # 1. Initialize a real project in a temporary directory
    alfred_test_project.initialize()

    # 2. Create a dummy persona and prompt template file
    (alfred_test_project.alfred_dir / "personas").mkdir(exist_ok=True)
    (alfred_test_project.alfred_dir / "personas" / "planning.yml").write_text("name: Alex")
    (alfred_test_project.alfred_dir / "templates" / "prompts" / "plan_task").mkdir(parents=True, exist_ok=True)
    (alfred_test_project.alfred_dir / "templates" / "prompts" / "plan_task" / "contextualize.md").write_text("Prompt for {{ task.title }}")

    # 3. Create a valid Task object and save it to the test project's file system
    task = Task(task_id="AL-01", title="My Test Task", context="Test context", implementation_details="Test implementation")
    alfred_test_project.create_task_file(task)

    # 4. Patch the global settings and create a test-specific prompter
    with (
        patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings),
        patch("src.alfred.orchestration.persona_loader.settings", alfred_test_project.settings),
        patch("src.alfred.core.prompter.settings", alfred_test_project.settings),
    ):
        # Create a new prompter instance that will use the patched settings
        from src.alfred.core.prompter import Prompter

        test_prompter = Prompter()

        with patch("src.alfred.tools.plan_task.prompter", test_prompter):
            # --- ACT ---
            # 5. Run the actual tool implementation
            result: ToolResponse = await plan_task_impl("AL-01")

            # --- ASSERT ---
            # 6. Assert the tool response is correct
            assert result.status == "success"
            assert "Planning initiated" in result.message
            assert result.next_prompt == "Prompt for My Test Task"

            # 7. Assert against the real file system state
            updated_task = alfred_test_project.load_task("AL-01")
            assert updated_task is not None
            assert updated_task.task_status == TaskStatus.PLANNING

            # 8. Assert against the real orchestrator state
            assert "AL-01" in orchestrator.active_tools
            assert orchestrator.active_tools["AL-01"].task_id == "AL-01"


@pytest.mark.asyncio
async def test_plan_task_invalid_status(alfred_test_project: AlfredTestProject):
    """
    Tests that plan_task correctly fails if the task is not in 'new' state.
    Uses minimal patching only for settings redirection - NO business logic mocking.
    """
    # --- ARRANGE ---
    alfred_test_project.initialize()
    task = Task(
        task_id="AL-02",
        title="A Task In Progress",
        context="Test context",
        implementation_details="Test implementation",
        task_status=TaskStatus.IN_DEVELOPMENT,  # Invalid initial state
    )
    alfred_test_project.create_task_file(task)

    # Patch the global settings to point to our test directory during the tool execution
    with patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings):
        # --- ACT ---
        result: ToolResponse = await plan_task_impl("AL-02")

        # --- ASSERT ---
        assert result.status == "error"
        assert "status 'in_development'" in result.message


@pytest.mark.asyncio
async def test_plan_task_not_found(alfred_test_project: AlfredTestProject):
    """
    Tests that plan_task correctly fails if the task file does not exist.
    Uses minimal patching only for settings redirection - NO business logic mocking.
    """
    # --- ARRANGE ---
    alfred_test_project.initialize()

    # Patch the global settings to point to our test directory during the tool execution
    with patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings):
        # --- ACT ---
        result: ToolResponse = await plan_task_impl("AL-99")  # This task does not exist

        # --- ASSERT ---
        assert result.status == "error"
        assert "Task 'AL-99' not found" in result.message


@pytest.mark.asyncio
async def test_plan_task_persona_not_found(alfred_test_project: AlfredTestProject):
    """
    Tests that plan_task correctly fails if the persona config doesn't exist.
    Uses minimal patching only for settings redirection - NO business logic mocking.
    """
    # --- ARRANGE ---
    alfred_test_project.initialize()

    # Create task
    task = Task(task_id="AL-03", title="Test Task Without Persona", context="Test context", implementation_details="Test implementation")
    alfred_test_project.create_task_file(task)

    # Mock load_persona to raise FileNotFoundError
    def mock_load_persona(persona_name):
        raise FileNotFoundError(f"Persona config '{persona_name}.yml' not found.")

    with patch("src.alfred.lib.task_utils.settings", alfred_test_project.settings), patch("src.alfred.tools.plan_task.load_persona", side_effect=mock_load_persona):
        # --- ACT ---
        result: ToolResponse = await plan_task_impl("AL-03")

        # --- ASSERT ---
        assert result.status == "error"
        assert "Persona config 'planning.yml' not found" in result.message
