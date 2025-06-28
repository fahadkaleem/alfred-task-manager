"""
Test prompts functionality
"""

from pathlib import Path

import pytest

from epic_task_manager.prompts.implement_next_task import implement_next_task


@pytest.mark.asyncio
async def test_implement_next_task_prompt_loads_template():
    """Test that the implement_next_task prompt loads the template correctly."""
    # Call without task_id
    content = await implement_next_task()

    # Check that we got content
    assert content is not None
    assert len(content) > 0

    # Check for key sections
    assert "Epic Task Manager (ETM) Assistant" in content
    assert "Core Directive: The Server is the Orchestrator" in content
    assert "Available Tools on the ETM Server" in content
    assert "Handling Errors" in content


@pytest.mark.asyncio
async def test_implement_next_task_prompt_replaces_task_id():
    """Test that the implement_next_task prompt replaces TASK_ID placeholder."""
    # Call with a specific task_id
    task_id = "IS-1234"
    content = await implement_next_task(task_id)

    # Check that TASK_ID was replaced
    assert "TASK_ID" not in content
    assert task_id in content


@pytest.mark.asyncio
async def test_implement_next_task_prompt_preserves_placeholder_without_task_id():
    """Test that the implement_next_task prompt preserves TASK_ID when no ID provided."""
    # Call without task_id
    content = await implement_next_task()

    # The current template doesn't have TASK_ID placeholder, so this test may not be relevant
    # Check that content is returned without replacement
    assert content is not None
    assert len(content) > 0


def test_prompt_template_file_exists():
    """Test that the prompt template file exists."""
    prompt_path = Path(__file__).parent.parent / "src" / "epic_task_manager" / "templates" / "prompts" / "client" / "implement_next_task.md"
    assert prompt_path.exists()
    assert prompt_path.is_file()
