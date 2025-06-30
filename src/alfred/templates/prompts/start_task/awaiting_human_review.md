# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

The AI has reviewed my submission and found it satisfactory. Now I require human approval to proceed with the next step.

**Current Artifact:**
```json
{{ additional_context.artifact_content | fromjson if additional_context.artifact_content else {} }}
```

---
### **Directive: Human Review**

Please review my submission above and confirm whether you approve proceeding to the next step.

The AI has already validated the technical accuracy. Your approval confirms that the proposed action aligns with your intentions and project requirements.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

Call `alfred.provide_review`.
- If you approve proceeding to the next step, set `is_approved=True`.
- If you need changes or have concerns, set `is_approved=False` and provide `feedback_notes` with your specific requirements.