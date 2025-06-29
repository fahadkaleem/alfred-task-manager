# Code Guidelines

- Follow coding standards in `ai/guidelines/coding_guidelines.md`
- Follow testing standards in `ai/guidelines/testing_guidelines.md`

# MCP Server Management

- MCP servers cannot be restarted via commands
- If MCP restart is needed, stop and ask the user to restart the MCP server

# Testing and Development Commands

- Use `uv run python -m pytest tests/ -v` to run tests
- Use `uv` package manager for all Python operations instead of pip/python directly

# Debugging

- Debug logs are stored in `.alfred/debug` directory
- Logs are organized by task ID for easy tracking