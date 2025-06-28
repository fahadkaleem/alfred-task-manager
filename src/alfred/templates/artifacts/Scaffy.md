---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: verified
---

# Scaffolding Complete: {{ task_id }}

## Scaffolding Summary

- **Files Scaffolded**: {{ artifact.files_scaffolded | length }}
- **TODO Items Generated**: {{ artifact.todo_items_generated }}
- **Execution Steps Processed**: {{ artifact.execution_steps_processed | length }}

## Files Modified
The following files received TODO comments:
{% for file in artifact.files_scaffolded %}
- `{{ file }}`
{% endfor %}