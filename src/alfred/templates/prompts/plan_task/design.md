# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: design

The technical strategy has been approved. Now, you must translate this strategy into a detailed, file-level implementation design.

**Approved Strategy:**
```json
{{ additional_context.strategy_artifact | tojson(indent=2) }}
```

{% if additional_context.feedback_notes %}
---
### **Iterating on Your Design**

Your DesignArtifact has been carefully reviewed, and there are some valuable suggestions to make it even stronger. Here's your current design:

```json
{{ additional_context.design_artifact | tojson(indent=2) if additional_context.design_artifact else "No artifact data available" }}
```

The review highlighted these areas for enhancement:

> {{ additional_context.feedback_notes }}

Please refine your DesignArtifact by incorporating these insights. Think about how these suggestions can improve the clarity, completeness, and implementability of your design while preserving the strong elements you've already developed.

{% endif %}
---
### **Directive: Create Detailed Design**

Based on the approved strategy, create a comprehensive, file-by-file breakdown of all necessary changes. For each file that needs to be created or modified, provide a clear summary of the required changes.

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

You MUST now call `alfred.submit_work` with a `DesignArtifact`.

**Required Artifact Structure:**
```json
{
  "design_summary": "string",
  "file_breakdown": [
    {
      "file_path": "string",
      "change_summary": "string",
      "operation": "create | modify"
    }
  ]
}
```