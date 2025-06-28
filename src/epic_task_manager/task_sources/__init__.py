"""
Task source abstractions and implementations
"""

from .base import LocalTaskProvider, RemoteTaskProvider, TaskProvider
from .constants import (
    COMMENT_SECTION_HEADER,
    COMMENT_TEMPLATE,
    COMMENT_TIMESTAMP_FORMAT,
    DEFAULT_LOCAL_TASK_STATUS,
    IGNORED_TASK_FILES,
    STATUS_UPDATE_TEMPLATE,
    TASK_FILE_EXTENSION,
)

__all__ = [
    "COMMENT_SECTION_HEADER",
    "COMMENT_TEMPLATE",
    "COMMENT_TIMESTAMP_FORMAT",
    "DEFAULT_LOCAL_TASK_STATUS",
    "IGNORED_TASK_FILES",
    "STATUS_UPDATE_TEMPLATE",
    "TASK_FILE_EXTENSION",
    "LocalTaskProvider",
    "RemoteTaskProvider",
    "TaskProvider",
]
