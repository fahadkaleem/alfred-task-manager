"""
Custom exceptions for Epic Task Manager
"""

from __future__ import annotations


class EpicTaskManagerError(Exception):
    """Base exception for Epic Task Manager"""

    def __init__(self, message: str, task_id: str | None = None):
        self.task_id = task_id
        super().__init__(message)


class StateFileError(EpicTaskManagerError):
    """Error related to state file operations"""


class InitializationError(EpicTaskManagerError):
    """Error during initialization"""


class TaskNotFoundError(EpicTaskManagerError):
    """Task not found in state"""


class PhaseTransitionError(EpicTaskManagerError):
    """Invalid phase transition"""


class StateTransitionError(EpicTaskManagerError):
    """Invalid state machine transition"""

    def __init__(self, message: str, current_state: str, attempted_transition: str):
        super().__init__(message)
        self.current_state = current_state
        self.attempted_transition = attempted_transition


class ArtifactError(EpicTaskManagerError):
    """Error related to artifact operations"""


class ArtifactNotFoundError(ArtifactError):
    """Artifact file not found"""


class InvalidArtifactFormatError(ArtifactError):
    """Artifact content is malformed"""
