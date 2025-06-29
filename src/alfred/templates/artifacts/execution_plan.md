## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Implementation Plan

Total SLOTs: **{{ artifact | length }}**

{% for slot in artifact %}
#### SLOT {{ slot.slot_id }}: {{ slot.title }}

**Specification:**
{{ slot.spec }}

**Acceptance Criteria:**
{% for criteria in slot.acceptance_criteria -%}
- {{ criteria }}
{% endfor %}

**Task Type:** {{ slot.taskflow.value }}
{% if slot.dependencies %}
**Dependencies:** {{ slot.dependencies|join(", ") }}
{% endif %}

{% endfor %}