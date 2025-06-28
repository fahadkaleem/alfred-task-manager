"""
Constants for Epic Task Manager
"""

# Phase numbering for archives
PHASE_NUMBERS = {
    "gatherrequirements": 1,
    "gitsetup": 2,
    "planning": 3,
    "scaffolding": 4,
    "coding": 5,
    "testing": 6,
    "finalize": 7,
}

# State transition triggers
ADVANCE_TRIGGERS = {
    "gatherrequirements_verified": "advance",
    "gitsetup_verified": "advance",
    "planning_verified": "advance_to_code",  # Will be overridden by conditional logic
    "scaffolding_verified": "advance_from_scaffold",
    "coding_verified": "advance",
    "testing_verified": "advance",
    "finalize_verified": "advance",
    # Planning substage devreview states use human_approves trigger
    "planning_strategydevreview": "human_approves",
    "planning_solutiondesigndevreview": "human_approves",
    "planning_executionplandevreview": "human_approves",
}

# Default values
DEFAULT_AI_MODEL = "claude-3.5-sonnet"
DEFAULT_ARTIFACT_VERSION = "1.0"

# File patterns
ARTIFACT_FILENAME = "scratchpad.md"
ARCHIVE_DIR_NAME = "archive"
WORKSPACE_DIR_NAME = "workspace"
TASKS_INBOX_DIR_NAME = "tasks"

# Response status values
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
