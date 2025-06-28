# Strategy Phase - {{ persona.name }}

## Task Overview
**Task ID:** {{ task.task_id }}
**Title:** {{ task.title }}

## Context
{{ task.context }}

## Implementation Details
{{ task.implementation_details }}

{% if task.dev_notes %}
## Developer Notes
{{ task.dev_notes }}
{% endif %}

## Acceptance Criteria
{% for criteria in task.acceptance_criteria %}
- {{ criteria }}
{% endfor %}

## Current Tool: {{ tool_name }}
## Current State: {{ state }}

## Persona Configuration
**Name:** {{ persona.name }}
**Description:** {{ persona.description }}

{% if additional_context %}
## Additional Context
{{ additional_context }}
{% endif %}

---
*This is a test template for the Prompter engine verification.*