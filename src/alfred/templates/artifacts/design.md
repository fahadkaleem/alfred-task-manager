### Design for `{{ task.task_id }}`
*State: `design`*

**Design Summary:**
{{ artifact.design_summary }}

**File Breakdown:**
{% for file_change in artifact.file_breakdown -%}
**{{ file_change.file_path }}** ({{ file_change.operation }})
{{ file_change.change_summary }}

{% endfor %}