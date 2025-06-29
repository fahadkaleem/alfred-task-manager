### Execution Plan for `{{ task.task_id }}`
*State: `generate_slots`*

**Implementation Plan:**

{% for slot in artifact %}
#### Slot {{ slot.slot_id }}: {{ slot.title }}

**Specification:**
{{ slot.spec }}

**Acceptance Criteria:**
{% for criteria in slot.acceptance_criteria -%}
- {{ criteria }}
{% endfor %}

**Task Flow:** {{ slot.taskflow.value }}
{% if slot.dependencies %}
**Dependencies:** {{ slot.dependencies|join(", ") }}
{% endif %}

{% endfor %}