"""
Utility commands for tool management.
"""

from typing import List, Dict, Any

from src.alfred.tools.tool_definitions import TOOL_DEFINITIONS
from src.alfred.tools.tool_factory import ToolFactory


def list_tools() -> List[Dict[str, Any]]:
    """List all available tools with their information."""
    return [ToolFactory.get_tool_info(name) for name in sorted(TOOL_DEFINITIONS.keys())]


def validate_tools() -> Dict[str, List[str]]:
    """Validate all tool definitions and return any issues."""
    issues = {}

    for name, definition in TOOL_DEFINITIONS.items():
        tool_issues = []

        # Check for common issues
        if not definition.description:
            tool_issues.append("Missing description")

        if definition.work_states and not definition.terminal_state:
            tool_issues.append("Has work states but no terminal state")

        if definition.entry_statuses and not definition.exit_status:
            tool_issues.append("Has entry statuses but no exit status")

        # Try to create handler
        try:
            ToolFactory.create_handler(name)
        except Exception as e:
            tool_issues.append(f"Handler creation failed: {e}")

        if tool_issues:
            issues[name] = tool_issues

    return issues


def generate_tool_documentation() -> str:
    """Generate markdown documentation for all tools."""
    lines = ["# Alfred Tools Documentation\n"]

    for name in sorted(TOOL_DEFINITIONS.keys()):
        definition = TOOL_DEFINITIONS[name]
        info = ToolFactory.get_tool_info(name)

        lines.append(f"## {name}\n")
        lines.append(f"{definition.description}\n")
        lines.append(f"- **Entry Statuses**: {', '.join(info['entry_statuses'])}")
        lines.append(f"- **Required Status**: {info['required_status'] or 'None'}")
        lines.append(f"- **Work States**: {', '.join(info['work_states'])}")
        lines.append(f"- **Auto-dispatch**: {info['dispatch_on_init']}")
        lines.append("")

    return "\n".join(lines)
