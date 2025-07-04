Add a specific memory or note to a module's Claude.md file.

Usage: `/project:add-module-memory <module_path> <memory_to_add>`

## Instructions:

1. Parse the arguments to extract:
   - Module path (e.g., `alfred/models`)
   - Memory content to add

2. Navigate to the specified module directory

3. If Claude.md doesn't exist, create it with basic structure

4. Add the new memory under an appropriate section:
   - If it's about a pattern, add to "Patterns & Conventions"
   - If it's about a gotcha, add to "Important Notes"
   - If it's about testing, add to "Testing"
   - Otherwise, add to a "Additional Notes" section

5. Format the memory as a bullet point

6. Confirm what was added and where

Example usage:
- `/project:add-module-memory alfred/models Always use Pydantic BaseModel for request/response models`
- `/project:add-module-memory alfred/database Repository methods should return domain models, not SQLAlchemy objects`

$ARGUMENTS
