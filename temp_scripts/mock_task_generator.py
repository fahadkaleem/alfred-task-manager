#!/usr/bin/env python3
"""Mock task generator for test tasks."""

import os
from pathlib import Path


def generate_test_task(task_id: str, title: str, context: str, implementation_details: str, acceptance_criteria: list) -> str:
    """Returns properly formatted markdown for a test task."""
    template = f"""# TASK: {task_id}

## Title
{title}

## Context
{context}

## Implementation Details
{implementation_details}

## Acceptance Criteria
"""

    # Add acceptance criteria as bullet points
    for ac in acceptance_criteria:
        template += f"- {ac}\n"

    return template


def create_test_task_file(task_id: str, **kwargs) -> str:
    """Writes test task to .alfred/tasks/{task_id}.md and returns file path."""
    # Default values
    title = kwargs.get("title", f"Test Task {task_id}")
    context = kwargs.get("context", f"Test context for {task_id}")
    implementation_details = kwargs.get("implementation_details", f"Test implementation for {task_id}")
    acceptance_criteria = kwargs.get("acceptance_criteria", [f"Test criteria for {task_id}"])

    # Generate content
    content = generate_test_task(task_id, title, context, implementation_details, acceptance_criteria)

    # Write to file
    tasks_dir = Path(".alfred/tasks")
    tasks_dir.mkdir(parents=True, exist_ok=True)

    file_path = tasks_dir / f"{task_id}.md"
    file_path.write_text(content, encoding="utf-8")

    return str(file_path)


def cleanup_test_task(task_id: str) -> None:
    """Removes test task file."""
    file_path = Path(f".alfred/tasks/{task_id}.md")
    if file_path.exists():
        file_path.unlink()
