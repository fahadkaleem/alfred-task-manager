"""
Unit tests for the Prompter class.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from src.alfred.core.prompter import Prompter
from src.alfred.core.workflow import PlanTaskState
from src.alfred.models.schemas import Task, TaskStatus


class TestPrompter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.task = Task(
            task_id="TEST-01",
            title="Test Task Title",
            context="This is a test task context",
            implementation_details="Test implementation details",
            dev_notes="Test developer notes",
            acceptance_criteria=["Test criteria 1", "Test criteria 2"],
            ac_verification_steps=["Test verification 1", "Test verification 2"],
            task_status=TaskStatus.NEW,
        )

        self.persona_config = {"name": "Test Persona", "description": "A test persona for unit testing"}

        self.additional_context = {"review_feedback": "This is test feedback"}

    def test_successful_prompt_generation(self):
        """Test that generate_prompt correctly renders a template with context."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create the prompts directory structure
            prompt_dir = temp_path / "prompts" / "plan_task"
            prompt_dir.mkdir(parents=True)

            # Create a test template
            template_content = """# Test Template
Task: {{ task.title }}
Persona: {{ persona.name }}
State: {{ state }}
Tool: {{ tool_name }}"""

            template_file = prompt_dir / "strategize.md"
            template_file.write_text(template_content)

            # Mock the settings to use our temp directory
            with patch("src.alfred.core.prompter.settings") as mock_settings:
                mock_settings.alfred_dir = temp_path / ".alfred"
                mock_settings.packaged_templates_dir = temp_path

                # Create prompter instance
                prompter = Prompter()

                # Generate prompt
                result = prompter.generate_prompt(task=self.task, tool_name="plan_task", state=PlanTaskState.STRATEGIZE, persona_config=self.persona_config)

                # Verify the result
                self.assertIn("Test Task Title", result)
                self.assertIn("Test Persona", result)
                self.assertIn("strategize", result)
                self.assertIn("plan_task", result)

    def test_context_injection(self):
        """Test that all parts of context are available in the template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create the prompts directory structure
            prompt_dir = temp_path / "prompts" / "plan_task"
            prompt_dir.mkdir(parents=True)

            # Create a comprehensive test template
            template_content = """# Context Test
Task ID: {{ task.task_id }}
Title: {{ task.title }}
Context: {{ task.context }}
Implementation: {{ task.implementation_details }}
Dev Notes: {{ task.dev_notes }}
Criteria: {% for criteria in task.acceptance_criteria %}{{ criteria }}{% endfor %}
Persona: {{ persona.name }} - {{ persona.description }}
Tool: {{ tool_name }}
State: {{ state }}
{% if review_feedback %}Feedback: {{ review_feedback }}{% endif %}"""

            template_file = prompt_dir / "strategize.md"
            template_file.write_text(template_content)

            # Mock the settings
            with patch("src.alfred.core.prompter.settings") as mock_settings:
                mock_settings.alfred_dir = temp_path / ".alfred"
                mock_settings.packaged_templates_dir = temp_path

                prompter = Prompter()

                result = prompter.generate_prompt(task=self.task, tool_name="plan_task", state=PlanTaskState.STRATEGIZE, persona_config=self.persona_config, additional_context=self.additional_context)

                # Verify all context is injected
                self.assertIn("TEST-01", result)
                self.assertIn("Test Task Title", result)
                self.assertIn("This is a test task context", result)
                self.assertIn("Test implementation details", result)
                self.assertIn("Test developer notes", result)
                self.assertIn("Test criteria 1Test criteria 2", result)
                self.assertIn("Test Persona - A test persona for unit testing", result)
                self.assertIn("plan_task", result)
                self.assertIn("strategize", result)
                self.assertIn("This is test feedback", result)

    def test_template_not_found_error(self):
        """Test that a meaningful error is returned when template path is invalid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Mock the settings to use empty temp directory (no templates)
            with patch("src.alfred.core.prompter.settings") as mock_settings:
                mock_settings.alfred_dir = temp_path / ".alfred"
                mock_settings.packaged_templates_dir = temp_path

                prompter = Prompter()

                result = prompter.generate_prompt(task=self.task, tool_name="nonexistent_tool", state=PlanTaskState.STRATEGIZE, persona_config=self.persona_config)

                # Verify error message
                self.assertIn("CRITICAL ERROR", result)
                self.assertIn("prompts/nonexistent_tool/strategize.md", result)

    def test_singleton_instance(self):
        """Test that the singleton prompter instance is created."""
        from src.alfred.core.prompter import prompter

        self.assertIsInstance(prompter, Prompter)


if __name__ == "__main__":
    unittest.main()
