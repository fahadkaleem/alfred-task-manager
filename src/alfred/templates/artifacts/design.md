## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Design Summary
{{ artifact.design_summary }}

### File-Level Implementation
{%- for file_change in artifact.file_breakdown %}
#### {{ file_change.file_path }} ({{ file_change.operation | upper }})
{{ file_change.change_summary }}
{% endfor %}