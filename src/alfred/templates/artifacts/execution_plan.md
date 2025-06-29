## Execution Plan

**Task:** {{ task.task_id }} - {{ task.title }}

Total Subtasks: **{{ artifact.subtasks | length }}**

{% for subtask in artifact.subtasks %}
### {{ subtask.subtask_id }}: {{ subtask.title }}
{% if subtask.summary -%}
**Summary**: {{ subtask.summary }}
{% endif -%}
**{{ subtask.operation }}** `{{ subtask.location }}`

Specification:
{%- for step in subtask.specification %}
- {{ step }}
{%- endfor %}

Test:
{%- for step in subtask.test %}
- {{ step }}
{%- endfor %}

{% endfor %}