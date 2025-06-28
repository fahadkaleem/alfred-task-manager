"""
Jira-specific schemas and models
"""

from enum import StrEnum


class JiraStatus(StrEnum):
    """Enum for Jira status values"""

    TO_DO = "TO DO"
    IN_PROGRESS = "In Progress"
    CODE_REVIEW = "Code Review"
    DONE = "Done"
