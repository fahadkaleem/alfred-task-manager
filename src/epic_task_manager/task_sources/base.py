"""
Base provider interface for Epic Task Manager task sources.

This module defines the abstract interface that all task source providers must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from epic_task_manager.models.config import TaskSource


class TaskProvider(ABC):
    """Abstract base class for task source providers"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the provider with configuration

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config

    @property
    @abstractmethod
    def provider_type(self) -> TaskSource:
        """Return the task source type this provider handles"""

    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that the provider configuration is correct

        Returns:
            bool: True if configuration is valid, False otherwise
        """

    @abstractmethod
    def test_connectivity(self) -> bool:
        """
        Test connectivity to the task source

        Returns:
            bool: True if connection successful, False otherwise
        """

    @abstractmethod
    def get_task_details(self, task_id: str) -> dict[str, Any]:
        """
        Retrieve task details from the task source

        Args:
            task_id: Unique identifier for the task

        Returns:
            Dict containing task details with keys:
            - summary: Task title/summary
            - description: Detailed task description
            - acceptance_criteria: List of acceptance criteria
            - status: Current task status
            - assignee: Task assignee (if any)
            - labels: List of task labels/tags
        """

    @abstractmethod
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update the status of a task in the task source

        Args:
            task_id: Unique identifier for the task
            status: New status to set

        Returns:
            bool: True if update successful, False otherwise
        """

    @abstractmethod
    def add_task_comment(self, task_id: str, comment: str) -> bool:
        """
        Add a comment to a task

        Args:
            task_id: Unique identifier for the task
            comment: Comment text to add

        Returns:
            bool: True if comment added successfully, False otherwise
        """

    @abstractmethod
    def list_available_tasks(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        List available tasks from the task source

        Args:
            filters: Optional filters to apply to task listing

        Returns:
            List of task dictionaries with basic task information
        """

    @abstractmethod
    def get_provider_capabilities(self) -> dict[str, bool]:
        """
        Return capabilities supported by this provider

        Returns:
            Dictionary of capability names and whether they're supported:
            - status_updates: Can update task status
            - comments: Can add comments to tasks
            - task_creation: Can create new tasks
            - task_deletion: Can delete tasks
            - file_attachments: Can attach files to tasks
        """


class LocalTaskProvider(TaskProvider):
    """Base class for local file-based task providers"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.tasks_dir = Path(config.get("tasks_directory", ".epictaskmanager/tasks"))

    @property
    def provider_type(self) -> TaskSource:
        return TaskSource.LOCAL

    def validate_configuration(self) -> bool:
        """Validate local provider configuration"""
        return self.tasks_dir.exists() or self.tasks_dir.parent.exists()

    def test_connectivity(self) -> bool:
        """Test local file system access"""
        try:
            self.tasks_dir.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False


class RemoteTaskProvider(TaskProvider):
    """Base class for remote API-based task providers"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url")
        self.connection_method = config.get("connection_method", "api")

    def validate_configuration(self) -> bool:
        """Validate remote provider configuration"""
        return bool(self.base_url) or self.connection_method == "mcp"

    @abstractmethod
    def test_connectivity(self) -> bool:
        """Test connectivity to remote service"""
