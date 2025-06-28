"""
Local file-based task provider implementation for Epic Task Manager.

This provider reads task definitions from markdown files in the
.epictaskmanager/tasks/ inbox directory.
"""

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from epic_task_manager.task_sources.base import LocalTaskProvider
from epic_task_manager.task_sources.constants import (
    COMMENT_SECTION_HEADER,
    COMMENT_TEMPLATE,
    COMMENT_TIMESTAMP_FORMAT,
    DEFAULT_LOCAL_TASK_STATUS,
    IGNORED_TASK_FILES,
    STATUS_UPDATE_TEMPLATE,
    TASK_FILE_EXTENSION,
)


class LocalProvider(LocalTaskProvider):
    """Local markdown file-based task provider"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.tasks_inbox = Path(config.get("tasks_inbox_directory", ".epictaskmanager/tasks"))

    def get_task_details(self, task_id: str) -> dict[str, Any]:
        """
        Retrieve task details from local markdown file

        Args:
            task_id: Filename (with or without .md extension)

        Returns:
            Dict containing parsed task details

        Raises:
            ValueError: If task_id is empty or invalid
            FileNotFoundError: If task file doesn't exist
            PermissionError: If file cannot be read due to permissions
            UnicodeDecodeError: If file encoding is invalid
        """
        if not task_id or not task_id.strip():
            raise ValueError("task_id cannot be empty")

        # Ensure task_id has .md extension
        if not task_id.endswith(TASK_FILE_EXTENSION):
            task_id = f"{task_id}{TASK_FILE_EXTENSION}"

        task_file = self.tasks_inbox / task_id

        if not task_file.exists():
            raise FileNotFoundError(f"Task file not found: {task_file}")

        try:
            content = task_file.read_text(encoding="utf-8")
        except PermissionError as e:
            raise PermissionError(f"Cannot read task file {task_file}: Permission denied") from e
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, f"Invalid encoding in task file {task_file}: {e.reason}") from e

        return self._parse_markdown_task(content, task_id)

    def _parse_markdown_task(self, content: str, filename: str) -> dict[str, Any]:
        """Parse markdown task file into structured data"""
        lines = content.split("\n")

        # Extract title (first heading)
        title = filename.replace(".md", "")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract description
        description_lines = []
        in_description = False
        for line in lines:
            if line.startswith("## Description"):
                in_description = True
                continue
            if line.startswith("## ") and in_description:
                break
            if in_description:
                description_lines.append(line)

        description = "\n".join(description_lines).strip()

        # Extract acceptance criteria
        acceptance_criteria = []
        in_criteria = False
        for line in lines:
            if line.startswith("## Acceptance Criteria"):
                in_criteria = True
                continue
            if line.startswith("## ") and in_criteria:
                break
            if in_criteria and (line.startswith(("- [ ]", "- [x]", "-"))):
                # Clean up checkbox format
                criteria = re.sub(r"^-\s*\[.\]\s*", "", line.strip())
                criteria = re.sub(r"^-\s*", "", criteria)
                if criteria:
                    acceptance_criteria.append(criteria)

        return {
            "summary": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "status": DEFAULT_LOCAL_TASK_STATUS,
            "assignee": None,
            "labels": [],
            "source_file": filename,
        }

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status in local file (adds status comment)

        Args:
            task_id: Task filename
            status: New status

        Returns:
            bool: True if update successful, False otherwise
        """
        if not task_id or not task_id.strip():
            return False

        if not status or not status.strip():
            return False

        try:
            if not task_id.endswith(TASK_FILE_EXTENSION):
                task_id = f"{task_id}{TASK_FILE_EXTENSION}"

            task_file = self.tasks_inbox / task_id
            if not task_file.exists():
                return False

            content = task_file.read_text(encoding="utf-8")

            # Add status update as comment at the end
            status_comment = STATUS_UPDATE_TEMPLATE.format(status)
            if status_comment not in content:
                content += status_comment
                task_file.write_text(content, encoding="utf-8")

            return True
        except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError):
            return False

    def add_task_comment(self, task_id: str, comment: str) -> bool:
        """
        Add comment to local task file

        Args:
            task_id: Task filename
            comment: Comment to add

        Returns:
            bool: True if comment added successfully, False otherwise
        """
        if not task_id or not task_id.strip():
            return False

        if not comment or not comment.strip():
            return False

        try:
            if not task_id.endswith(TASK_FILE_EXTENSION):
                task_id = f"{task_id}{TASK_FILE_EXTENSION}"

            task_file = self.tasks_inbox / task_id
            if not task_file.exists():
                return False

            content = task_file.read_text(encoding="utf-8")

            # Add comment section if it doesn't exist
            if "## Comments" not in content:
                content += COMMENT_SECTION_HEADER

            # Add the new comment
            timestamp = datetime.now().strftime(COMMENT_TIMESTAMP_FORMAT)
            new_comment = COMMENT_TEMPLATE.format(timestamp, comment)
            content += new_comment

            task_file.write_text(content, encoding="utf-8")
            return True
        except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError):
            return False

    def list_available_tasks(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        List all markdown task files in the inbox directory

        Args:
            filters: Optional filters (not implemented for local provider)

        Returns:
            List of task summaries
        """
        tasks: list[dict[str, Any]] = []

        if not self.tasks_inbox.exists():
            return tasks

        for task_file in self.tasks_inbox.glob(f"*{TASK_FILE_EXTENSION}"):
            if task_file.name in IGNORED_TASK_FILES:
                continue  # Skip ignored files

            try:
                task_details = self.get_task_details(task_file.name)
                tasks.append(
                    {
                        "id": task_file.stem,
                        "summary": task_details["summary"],
                        "status": task_details["status"],
                        "file": task_file.name,
                    }
                )
            except (ValueError, FileNotFoundError, PermissionError, UnicodeDecodeError):
                # Skip files that can't be parsed
                continue

        return tasks

    def get_provider_capabilities(self) -> dict[str, bool]:
        """Return capabilities of the local provider"""
        return {
            "status_updates": True,  # Can add status comments
            "comments": True,  # Can add comments
            "task_creation": True,  # Can create new markdown files
            "task_deletion": True,  # Can delete markdown files
            "file_attachments": False,  # No attachment support
        }
