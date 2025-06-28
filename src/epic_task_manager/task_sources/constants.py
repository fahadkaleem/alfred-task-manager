"""
Constants for task source providers
"""

# Default status values
DEFAULT_LOCAL_TASK_STATUS = "To Do"

# File patterns and names
IGNORED_TASK_FILES = ["README.md"]
TASK_FILE_EXTENSION = ".md"

# Status comment templates
STATUS_UPDATE_TEMPLATE = "\n\n<!-- Status Updated: {} -->\n"
COMMENT_SECTION_HEADER = "\n\n## Comments\n"
COMMENT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
COMMENT_TEMPLATE = "\n- **{}**: {}\n"
