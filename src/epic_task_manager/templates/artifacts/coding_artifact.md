---
{{ metadata }}
---

# Implementation: {{ task_id }}

## 1. Implementation Summary
{{ implementation_summary }}

## 2. Execution Steps Completed
{% for prompt_id in execution_steps_completed %}
- {{ prompt_id }}
{% endfor %}

## 3. Testing Notes
{{ testing_notes }}

## 4. Acceptance Criteria Met
{{ acceptance_criteria_met }}
