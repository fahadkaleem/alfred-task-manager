Generate or update Claude.md memory files throughout the project to provide context-aware assistance for each module.

## Instructions:

1. **Scan the project structure** starting from the current directory
2. **For each significant module/directory**:
   - Check if a Claude.md file exists
   - If missing, create one with appropriate context
   - If exists, review and update with any missing best practices
3. **Include in each Claude.md**:
   - Module purpose and responsibility
   - Key files and their roles
   - Common operations and commands specific to that module
   - Important patterns or conventions used
   - Dependencies and relationships with other modules
   - Testing approach for that module
   - Any gotchas or special considerations

## Best Practices to Follow:
- Keep each file concise and focused on its specific module
- Use clear headings and bullet points
- Include specific examples rather than generic advice
- Reference the main CLAUDE.md for project-wide conventions
- Update existing files intelligently without removing valid content
- Skip directories that don't need context (e.g., __pycache__, .git)

## Module Types to Consider:
- **models/**: Data models and validation rules
- **database/**: Database interactions and repositories
- **services/**: Business logic and workflows
- **tools/**: MCP tool implementations
- **tests/**: Testing strategies and patterns
- **config/**: Configuration management
- **utils/**: Shared utilities and helpers

Start by analyzing the project structure and create/update Claude.md files as needed. Show a summary of what was created or updated.
