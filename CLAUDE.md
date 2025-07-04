# Code Guidelines

- Follow coding standards in `ai/guidelines/coding_guidelines.md`
- Follow testing standards in `ai/guidelines/testing_guidelines.md`

# Core Principles (MANDATORY)

**CRITICAL**: All principles in `docs/principles/` are MANDATORY and non-negotiable. These principles override any other guidance and must be followed exactly.

## Context-Aware Principles Loading

**ALWAYS** read the relevant principles file based on your current task context:

### When working with STATE MACHINES or WORKFLOWS:
- Read `docs/principles/state_machine_principles.md` BEFORE making any state machine changes
- Read `docs/principles/workflow_configuration_principles.md` for workflow phase modifications

### When working with TOOL REGISTRATION or HANDLERS:
- Read `docs/principles/tool_registration_principles.md` for new tool creation
- Read `docs/principles/handler_principles.md` for handler modifications

### When working with TEMPLATES or PROMPTS:
- Read `docs/principles/template_system_principles.md` for template changes
- Read `docs/principles/prompt_builder_principles.md` for prompt system work

### When working with CONFIGURATION:
- Read `docs/principles/configuration_management_principles.md` for config changes

### When working with STATE MANAGEMENT or PERSISTENCE:
- Read `docs/principles/state_management_principles.md` for state operations

### When working with TASK PROVIDERS:
- Read `docs/principles/task_provider_principles.md` for provider implementations

### When working with ERROR HANDLING:
- Read `docs/principles/error_handling_principles.md` for error response patterns

### When working with DATA MODELS:
- Read `docs/principles/data_model_principles.md` for model definitions

### When working with MCP SERVER integration:
- Read `docs/principles/mcp_server_principles.md` for server modifications

### When working with LOGGING or DEBUGGING:
- Read `docs/principles/logging_debugging_principles.md` for logging changes

### When working with MCP TOOLS or CLIENT INTERFACES:
- Read `docs/principles/mcp_client_principles.md` for MCP interface standards

## Complete Principles List

All available principles documents:
- `docs/principles/state_machine_principles.md` - State machine architecture rules
- `docs/principles/handler_principles.md` - Handler design principles  
- `docs/principles/template_system_principles.md` - Template system guidelines
- `docs/principles/configuration_management_principles.md` - Configuration hierarchy rules
- `docs/principles/tool_registration_principles.md` - Tool registration patterns
- `docs/principles/state_management_principles.md` - State persistence rules
- `docs/principles/task_provider_principles.md` - Provider interface standards
- `docs/principles/prompt_builder_principles.md` - Prompt building guidelines
- `docs/principles/workflow_configuration_principles.md` - Workflow phase rules
- `docs/principles/error_handling_principles.md` - Error response standards
- `docs/principles/data_model_principles.md` - Data model design rules
- `docs/principles/mcp_server_principles.md` - MCP integration standards
- `docs/principles/logging_debugging_principles.md` - Logging system rules
- `docs/principles/mcp_client_principles.md` - MCP client interface standards

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