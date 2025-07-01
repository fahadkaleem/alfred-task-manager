# Task Breakdown from Engineering Specification

You are about to break down an Engineering Specification into individual, actionable tasks.

## Task ID: {{ additional_context.task_id }}

## Engineering Specification Summary

**Project**: {{ additional_context.technical_spec.project_name }}

**Overview**: {{ additional_context.technical_spec.overview }}

### Functional Requirements
{% for req in additional_context.technical_spec.functional_requirements %}
- {{ req.story }}
{% endfor %}

### API Changes
{% for api in additional_context.technical_spec.api_changes %}
- {{ api.name_and_method }}: {{ api.description }}
{% endfor %}

### Data Storage Requirements
{% for field in additional_context.technical_spec.data_storage %}
- {{ field.field_name }} ({{ field.data_type }}{% if field.is_required %}, required{% endif %}): {{ field.description }}
{% endfor %}

### Major Design Considerations
{{ additional_context.technical_spec.major_design_considerations }}

### Dependencies
{% for dep in additional_context.technical_spec.dependencies %}
- {{ dep }}
{% endfor %}

## Your Objective

Analyze the technical specification above and create a comprehensive list of Task objects that cover the entire implementation. Each task should be:

1. **Atomic**: A single, focused piece of work
2. **Actionable**: Clear about what needs to be done
3. **Measurable**: Has clear completion criteria
4. **Ordered**: Consider dependencies between tasks

## Task Structure

Each Task object should have:
- **id**: A unique identifier (e.g., "TASK-001", "TASK-002")
- **title**: Clear, concise title describing the work
- **description**: Detailed description of what needs to be done
- **acceptance_criteria**: List of criteria that must be met for completion
- **dependencies**: List of task IDs this task depends on (if any)
- **estimated_effort**: Rough estimate (e.g., "Small", "Medium", "Large")
- **technical_notes**: Any technical details or considerations

## Guidelines for Task Creation

1. **Coverage**: Ensure all aspects of the technical spec are covered
2. **Granularity**: Tasks should be completable in 1-3 days of work
3. **Dependencies**: Order tasks logically based on dependencies
4. **Categories**: Consider grouping by:
   - Data model/schema changes
   - API endpoints
   - Business logic
   - UI components
   - Testing
   - Documentation
   - DevOps/Infrastructure

5. **Don't Forget**:
   - Database migrations
   - API documentation
   - Unit and integration tests
   - Error handling
   - Logging and monitoring
   - Security implementation
   - Performance optimizations

## Example Task

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

Call `submit_work` with a TaskCreationArtifact containing your list of Task objects.