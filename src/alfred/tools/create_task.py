"""
Create Task Tool - Standardized task creation within Alfred
"""

import os
from pathlib import Path
from typing import Dict, Any
from src.alfred.lib.logger import get_logger
from src.alfred.lib.md_parser import MarkdownTaskParser
from src.alfred.models.schemas import ToolResponse
from src.alfred.config.settings import settings

logger = get_logger(__name__)

TASK_TEMPLATE = """# TASK: SAMPLE-001

## Title
Example task demonstrating the correct format

## Context
This is a sample task file that demonstrates the correct markdown format expected by Alfred. It shows all required and optional sections that can be used when creating tasks.

## Implementation Details
Create a well-formatted markdown file that follows the exact structure expected by the MarkdownTaskParser. The file should include all required sections and demonstrate optional sections as well.

## Acceptance Criteria
- Task file must start with "# TASK: <task_id>" format
- Must include Title, Context, Implementation Details, and Acceptance Criteria sections
- Should follow the exact section headers expected by the parser
- Must be parseable by the MarkdownTaskParser without errors

## AC Verification
- Verify that the md_parser can successfully parse the file
- Confirm all required fields are extracted correctly
- Test that the Task pydantic model can be created from parsed data
- Ensure no validation errors occur during task loading

## Dev Notes
This file serves as both documentation and a working example. When creating new tasks, copy this format and modify the content as needed."""


def create_task_impl(task_content: str) -> ToolResponse:
    """
    Creates a new task in the Alfred system by validating the format and saving to .alfred/tasks/.

    Args:
        task_content: Raw markdown content for the task in the expected template format

    Returns:
        ToolResponse with success/error status and guidance
    """
    try:
        # Initialize parser
        parser = MarkdownTaskParser()

        # Validate format first
        is_valid, error_msg = parser.validate_format(task_content)
        if not is_valid:
            return ToolResponse(
                status="error",
                message="Task content format is invalid.",
                data={
                    "validation_error": error_msg,
                    "template": TASK_TEMPLATE,
                    "help": "Your task content must follow the exact template format shown above. Key requirements:\n"
                    "1. First line must be '# TASK: <task_id>'\n"
                    "2. Must include sections: Title, Context, Implementation Details, Acceptance Criteria\n"
                    "3. Sections must use '##' headers\n"
                    "4. Content cannot be empty",
                },
            )

        # Parse to extract task_id and validate structure
        try:
            parsed_data = parser.parse(task_content)
            task_id = parsed_data.get("task_id")
            if not task_id:
                return ToolResponse(
                    status="error", message="Unable to extract task_id from content.", data={"template": TASK_TEMPLATE, "help": "Ensure the first line follows the format: # TASK: <task_id>"}
                )
        except Exception as e:
            return ToolResponse(
                status="error", message="Failed to parse task content.", data={"parse_error": str(e), "template": TASK_TEMPLATE, "help": "Ensure your task content follows the exact template format."}
            )

        # Ensure .alfred/tasks directory exists
        tasks_dir = Path(settings.alfred_dir) / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)

        # Create task file path
        task_file_path = tasks_dir / f"{task_id}.md"

        # Check if task already exists
        if task_file_path.exists():
            return ToolResponse(
                status="error", message=f"Task '{task_id}' already exists.", data={"existing_file": str(task_file_path), "help": "Choose a different task_id or update the existing task manually."}
            )

        # Write the task file
        task_file_path.write_text(task_content, encoding="utf-8")

        logger.info(f"Created new task file: {task_file_path}")

        return ToolResponse(
            status="success",
            message=f"Task '{task_id}' created successfully.",
            data={"task_id": task_id, "file_path": str(task_file_path), "task_title": parsed_data.get("title", ""), "next_action": "Use work_on_task(task_id) to start working on this task."},
        )

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return ToolResponse(
            status="error",
            message="An unexpected error occurred while creating the task.",
            data={"error": str(e), "template": TASK_TEMPLATE, "help": "Please check the task content format and try again."},
        )
