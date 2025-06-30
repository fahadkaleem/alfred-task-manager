"""Base task provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.alfred.models.schemas import Task, ToolResponse


class BaseTaskProvider(ABC):
    """Abstract base class for all task providers.

    This defines the contract that all task providers must implement,
    ensuring a consistent interface regardless of the underlying data source.
    """

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:
        """Fetches the details for a single task.

        Args:
            task_id: The unique identifier for the task

        Returns:
            Task object if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all_tasks(self) -> List[Task]:
        """Fetches all available tasks from the source.

        Returns:
            List of all tasks from the provider
        """
        pass

    @abstractmethod
    def get_next_task(self) -> ToolResponse:
        """Intelligently determines and returns the next recommended task.

        Returns:
            ToolResponse containing the recommended task and reasoning
        """
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Updates the status of a task.

        Args:
            task_id: The unique identifier for the task
            new_status: The new status to set

        Returns:
            True if update was successful, False otherwise
        """
        pass
