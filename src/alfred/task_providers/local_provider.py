"""Local file system task provider implementation."""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.lib.md_parser import MarkdownTaskParser
from alfred.lib.structured_logger import get_logger
from alfred.config.settings import settings
from alfred.state.manager import state_manager
from .base import BaseTaskProvider

logger = get_logger(__name__)


class LocalTaskProvider(BaseTaskProvider):
    """Task provider that reads tasks from local markdown files.

    This provider implements the BaseTaskProvider interface for local
    file system based task management, reading from .alfred/tasks/*.md files.
    """

    def __init__(self):
        """Initialize the local task provider."""
        self.tasks_dir = settings.alfred_dir / "tasks"
        self.parser = MarkdownTaskParser()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Fetches the details for a single task from markdown file.

        Args:
            task_id: The unique identifier for the task

        Returns:
            Task object if found, None otherwise
        """
        task_md_path = self.tasks_dir / f"{task_id}.md"

        if not task_md_path.exists():
            logger.warning(f"Task file not found: {task_md_path}")
            return None

        try:
            # Read and validate the markdown file
            content = task_md_path.read_text()

            # Validate format first
            is_valid, error_msg = self.parser.validate_format(content)
            if not is_valid:
                logger.error(f"Task file {task_md_path} has invalid format: {error_msg}")
                logger.error(f"Please refer to .alfred/tasks/README.md for the correct task file format.")
                logger.error(f"See .alfred/tasks/SAMPLE-FORMAT.md for a working example.")
                return None

            # Parse the markdown file
            task_data = self.parser.parse(content)

            # Validate required fields and provide helpful error if missing
            if not task_data.get("task_id"):
                logger.error(f"Task file {task_md_path} is missing task_id. Expected format: '# TASK: {task_id}'")
                logger.error(f"Current format in file: {content.split('\\n')[0] if content else 'Empty file'}")
                return None

            task_model = Task(**task_data)

            # Load and merge the dynamic state
            task_state = state_manager.load_or_create(task_id)
            task_model.task_status = task_state.task_status

            return task_model
        except ValueError as e:
            logger.error(f"Task file {task_md_path} has invalid format: {e}")
            logger.error(f"Please refer to .alfred/tasks/README.md for the correct task file format.")
            logger.error(f"See .alfred/tasks/SAMPLE-FORMAT.md for a working example.")
            return None
        except Exception as e:
            logger.error(f"Failed to load task {task_id} from {task_md_path}: {e}")
            return None

    def get_task_with_error_details(self, task_id: str) -> tuple[Optional[Task], Optional[str]]:
        """Fetches the details for a single task with detailed error information.

        Args:
            task_id: The unique identifier for the task

        Returns:
            Tuple of (Task object if found or None, error message if failed or None)
        """
        task_md_path = self.tasks_dir / f"{task_id}.md"

        if not task_md_path.exists():
            # Read the template content to show the user
            template_path = Path(__file__).parent.parent / "templates" / "task_template.md"
            template_content = ""
            if template_path.exists():
                template_content = template_path.read_text()
                # Replace the sample task ID with the requested one
                template_content = template_content.replace("SAMPLE-001", task_id)

            error_msg = f"Task '{task_id}' doesn't exist.\n\n"
            error_msg += f"To create it, save this content as:\n{task_md_path}\n\n"
            error_msg += f"--- TEMPLATE ---\n{template_content}\n--- END TEMPLATE ---"
            return None, error_msg

        try:
            # Read and validate the markdown file
            content = task_md_path.read_text()

            # Validate format first
            is_valid, error_msg = self.parser.validate_format(content)
            if not is_valid:
                # Read the template content to show the user
                template_path = Path(__file__).parent.parent / "templates" / "task_template.md"
                template_content = ""
                if template_path.exists():
                    template_content = template_path.read_text()
                    # Replace the sample task ID with the requested one
                    template_content = template_content.replace("SAMPLE-001", task_id)

                detailed_error = f"Task file has invalid format: {error_msg}\n\n"
                detailed_error += f"File location: {task_md_path}\n\n"
                detailed_error += f"Expected format:\n"
                detailed_error += f"--- TEMPLATE ---\n{template_content}\n--- END TEMPLATE ---"
                return None, detailed_error

            # Parse the markdown file
            task_data = self.parser.parse(content)

            # Validate required fields and provide helpful error if missing
            if not task_data.get("task_id"):
                error_msg = f"Task file is missing task_id.\n\n"
                error_msg += f"Expected format: '# TASK: {task_id}'\n"
                error_msg += f"Current first line: {content.split('\\n')[0] if content else 'Empty file'}\n"
                error_msg += f"File location: {task_md_path}"
                return None, error_msg

            task_model = Task(**task_data)

            # Load and merge the dynamic state
            task_state = state_manager.load_or_create(task_id)
            task_model.task_status = task_state.task_status

            return task_model, None
        except ValueError as e:
            detailed_error = f"Task file has invalid format: {e}\n\n"
            detailed_error += f"File location: {task_md_path}\n"
            detailed_error += f"Template reference: src/alfred/templates/task_template.md"
            return None, detailed_error
        except Exception as e:
            error_msg = f"Failed to load task {task_id} from {task_md_path}: {e}"
            return None, error_msg

    def get_all_tasks(self) -> List[Task]:
        """Fetches all available tasks from the tasks directory.

        Returns:
            List of all tasks found in the .alfred/tasks directory
        """
        tasks = []

        if not self.tasks_dir.exists():
            logger.warning(f"Tasks directory does not exist: {self.tasks_dir}")
            return tasks

        for task_file in self.tasks_dir.glob("*.md"):
            task_id = task_file.stem
            task = self.get_task(task_id)
            if task:
                tasks.append(task)

        return tasks

    def get_next_task(self) -> ToolResponse:
        """Intelligently determines and returns the next recommended task.

        This implementation uses the AL-61 ranking algorithm to prioritize tasks.

        Returns:
            ToolResponse containing the recommended task and reasoning
        """
        try:
            all_tasks = self.get_all_tasks()

            if not all_tasks:
                return ToolResponse(status="success", message="No tasks found in the system. Please create tasks first.", data={"tasks_found": 0})

            # Filter out completed tasks
            active_tasks = [t for t in all_tasks if t.task_status != TaskStatus.DONE]

            if not active_tasks:
                return ToolResponse(status="success", message="All tasks are completed! Great work!", data={"tasks_found": len(all_tasks), "active_tasks": 0})

            # Rank tasks using our prioritization algorithm
            ranked_tasks = self._rank_tasks(active_tasks)

            # Get the top task
            recommended_task = ranked_tasks[0]

            # Generate reasoning for the recommendation
            reasoning = self._generate_recommendation_reasoning(recommended_task, ranked_tasks)

            return ToolResponse(
                status="success",
                message=f"Recommended task: {recommended_task.task_id} - {recommended_task.title}",
                data={
                    "task_id": recommended_task.task_id,
                    "title": recommended_task.title,
                    "status": recommended_task.task_status.value,
                    "reasoning": reasoning,
                    "total_active_tasks": len(active_tasks),
                    "alternatives": [
                        {"task_id": t.task_id, "title": t.title, "status": t.task_status.value}
                        for t in ranked_tasks[1:4]  # Show top 3 alternatives
                    ],
                },
                next_prompt=f"Task {recommended_task.task_id} is ready. Use 'work_on {recommended_task.task_id}' to begin.",
            )
        except Exception as e:
            logger.error(f"Failed to get next task: {e}")
            return ToolResponse(status="error", message=f"Failed to determine next task: {str(e)}")

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Updates the status of a task.

        Args:
            task_id: The unique identifier for the task
            new_status: The new status to set

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Convert string to TaskStatus enum
            status_enum = TaskStatus(new_status)

            # Update via state manager
            state_manager.update_task_status(task_id, status_enum)

            return True
        except Exception as e:
            logger.error(f"Failed to update task {task_id} status to {new_status}: {e}")
            return False

    def _rank_tasks(self, tasks: List[Task]) -> List[Task]:
        """Rank tasks based on the AL-61 prioritization algorithm.

        Priority factors:
        1. In-progress tasks (highest priority)
        2. Tasks ready for action
        3. Priority level (if available)
        4. Task age (older tasks get slight boost)
        """

        def calculate_score(task: Task) -> tuple:
            # Score is a tuple for stable sorting (higher is better)

            # First priority: In-progress tasks
            in_progress_score = (
                1 if task.task_status in [TaskStatus.IN_DEVELOPMENT, TaskStatus.IN_REVIEW, TaskStatus.IN_TESTING, TaskStatus.PLANNING, TaskStatus.CREATING_SPEC, TaskStatus.CREATING_TASKS] else 0
            )

            # Second priority: Ready for action
            ready_score = (
                1
                if task.task_status
                in [TaskStatus.NEW, TaskStatus.READY_FOR_DEVELOPMENT, TaskStatus.READY_FOR_REVIEW, TaskStatus.READY_FOR_TESTING, TaskStatus.READY_FOR_FINALIZATION, TaskStatus.REVISIONS_REQUESTED]
                else 0
            )

            # Third priority: Task ID numeric value (lower ID = older task = higher priority)
            # Extract numeric part from task ID (e.g., "AL-42" -> 42)
            try:
                task_number = int(task.task_id.split("-")[-1])
                # Invert so lower numbers get higher scores
                age_score = 1000 - task_number
            except:
                age_score = 0

            return (in_progress_score, ready_score, age_score)

        # Sort tasks by score (descending)
        return sorted(tasks, key=calculate_score, reverse=True)

    def _generate_recommendation_reasoning(self, task: Task, all_ranked: List[Task]) -> str:
        """Generate human-readable reasoning for why this task was recommended."""
        reasons = []

        # Check if it's in progress
        if task.task_status in [TaskStatus.IN_DEVELOPMENT, TaskStatus.IN_REVIEW, TaskStatus.IN_TESTING, TaskStatus.PLANNING]:
            reasons.append(f"Task is already in progress ({task.task_status.value})")

        # Check if it's ready for action
        elif task.task_status in [TaskStatus.NEW, TaskStatus.READY_FOR_DEVELOPMENT]:
            reasons.append(f"Task is ready to start ({task.task_status.value})")

        # Check if it needs attention
        elif task.task_status == TaskStatus.REVISIONS_REQUESTED:
            reasons.append("Task has requested revisions that need to be addressed")

        # Add context about alternatives
        if len(all_ranked) > 1:
            reasons.append(f"Selected from {len(all_ranked)} active tasks based on priority")

        return ". ".join(reasons) + "."
