# Code Guidelines

- Follow coding standards in `ai/guidelines/coding_guidelines.md`
- Follow testing standards in `ai/guidelines/testing_guidelines.md`

# Core Principles (MANDATORY)

**CRITICAL**: All principles in `docs/principles/` are MANDATORY and non-negotiable:

- `docs/principles/state_machine_principles.md` - State machine architecture rules
- `docs/principles/handler_principles.md` - Handler design principles  
- `docs/principles/template_system_principles.md` - Template system guidelines

These principles override any other guidance and must be followed exactly.

# MCP Server Management

- MCP servers cannot be restarted via commands
- If MCP restart is needed, stop and ask the user to restart the MCP server

# Testing and Development Commands

- Use `uv run python -m pytest tests/ -v` to run tests
- Use `uv` package manager for all Python operations instead of pip/python directly

# Debugging

- Debug logs are stored in `.alfred/debug` directory
- Logs are organized by task ID for easy tracking

# Task Management

- New tasks should always be created inside .alfred/tasks directory in the format mentioned in md_parser.py