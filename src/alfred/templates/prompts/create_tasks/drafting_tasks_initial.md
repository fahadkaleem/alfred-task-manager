# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Break down an Engineering Specification into individual, actionable tasks that cover the entire implementation.

# BACKGROUND
You have an approved Engineering Specification that needs to be decomposed into manageable tasks. Each task should be:
- **Atomic**: A single, focused piece of work
- **Actionable**: Clear about what needs to be done
- **Measurable**: Has clear completion criteria
- **Ordered**: Consider dependencies between tasks

**Engineering Specification Available:**
${artifact_json}

# INSTRUCTIONS
1. Analyze the technical specification thoroughly
2. Identify all work that needs to be done across:
   - Data model/schema changes
   - API endpoints
   - Business logic
   - UI components
   - Testing
   - Documentation
   - DevOps/Infrastructure
3. Create tasks with appropriate granularity (1-3 days of work each)
4. Establish logical dependencies between tasks
5. Ensure complete coverage of the specification

Don't forget to include tasks for:
- Database migrations
- API documentation
- Unit and integration tests
- Error handling
- Logging and monitoring
- Security implementation
- Performance optimizations

# CONSTRAINTS
- Every aspect of the spec must be covered by at least one task
- Tasks should be independent when possible
- Dependencies should be clearly stated
- Estimates should be realistic

# OUTPUT
Create a TaskCreationArtifact containing an array of Task objects. Each task should have:
- `id`: Unique identifier (e.g., "TASK-001", "TASK-002")
- `title`: Clear, concise title
- `description`: Detailed description of work
- `acceptance_criteria`: List of completion criteria
- `dependencies`: List of task IDs this depends on
- `estimated_effort`: "Small", "Medium", or "Large"
- `technical_notes`: Any technical considerations

**Required Action:** Call `alfred.submit_work` with a `TaskCreationArtifact`

# EXAMPLES
```json
{
  "id": "TASK-001",
  "title": "Create User Authentication Schema",
  "description": "Design and implement the database schema for user authentication including users table, sessions table, and required indexes",
  "acceptance_criteria": [
    "Users table created with email, password_hash, created_at fields",
    "Sessions table created with user_id, token, expires_at fields",
    "Appropriate indexes added for performance",
    "Migration script created and tested"
  ],
  "dependencies": [],
  "estimated_effort": "Small",
  "technical_notes": "Use bcrypt for password hashing, consider UUID for session tokens"
}
```