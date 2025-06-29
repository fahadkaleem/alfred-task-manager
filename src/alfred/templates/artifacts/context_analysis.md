### Context Analysis for `{{ task.task_id }}`
*State: `contextualize`*

**Analysis Summary:**
{{ artifact.context_summary }}

**Identified Affected Files:**
{% for file in artifact.affected_files -%}
- `{{ file }}`
{% endfor %}
**Questions for Developer:**
{% for question in artifact.questions_for_developer -%}
- {{ question }}
{% endfor %}