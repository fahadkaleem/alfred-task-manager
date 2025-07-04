Automatically sync and maintain Claude.md documentation files across all project modules.

## Task Overview

Traverse the project structure and ensure each significant module has an up-to-date Claude.md file that helps Claude understand the module's context, patterns, and best practices.

## Process

### 1. Module Discovery

- Start from project root: `alfred/`
- Identify all Python modules (directories with `__init__.py`)
- Skip: `__pycache__`, `.git`, `node_modules`, `venv`, `.venv`

### 2. For Each Module, Generate/Update Claude.md with

#### Module Overview Section

- What this module is responsible for
- How it fits into the overall architecture
- Key abstractions and patterns used

#### File Structure Section

- List important files with one-line descriptions
- Group by functionality (e.g., models, services, utilities)

#### Code Patterns Section

- Common patterns specific to this module
- Naming conventions used
- Import organization specific to module

#### Dependencies Section

- What this module depends on
- What depends on this module
- External libraries used

#### Common Tasks Section

- How to add new functionality
- How to modify existing features
- Testing approach for this module

#### Gotchas Section

- Non-obvious behaviors
- Common mistakes to avoid
- Performance considerations

### 3. Smart Updates

- Preserve existing custom content
- Add missing sections
- Update file lists if structure changed
- Mark sections as auto-generated where appropriate

### 4. Special Handling for Key Directories

**alfred/models/**: Focus on Pydantic models, validation rules, business entities
**alfred/database/**: SQLAlchemy models, repository patterns, migrations
**alfred/services/**: Business logic, transaction handling, service patterns
**alfred/tools/**: FastMCP tool definitions, MCP patterns
**alfred/tests/**: Testing strategies, fixtures, test organization
**alfred/config/**: Configuration management, environment handling

### 5. Output Summary

Show what was created, updated, or left unchanged.

## Example Claude.md Structure

```markdown
# Module: [module_name]

## Overview
Brief description of module purpose

## Key Files
- `file1.py`: Description
- `file2.py`: Description

## Patterns & Conventions
- Pattern 1 used here
- Convention specific to module

## Dependencies
- Depends on: module1, module2
- Used by: module3, module4

## Common Tasks
- To add a new X: ...
- To modify Y: ...

## Testing
- Test files location
- Test patterns used

## Important Notes
- Special consideration 1
- Gotcha to watch for
```

Execute this task now, creating or updating Claude.md files as needed.
