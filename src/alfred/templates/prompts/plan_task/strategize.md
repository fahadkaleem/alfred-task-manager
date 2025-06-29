# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: strategize

Context is verified. The human developer has provided all necessary clarifications. We will now create the high-level technical strategy for '{{ task.title }}'. This strategy will serve as the guiding principle for the detailed design.

---
### **Refining Your Technical Strategy**
{% if additional_context.feedback_notes %}
Your previous StrategyArtifact has been reviewed and the team has provided valuable insights to strengthen your approach. Here's your earlier strategy:

```json
{{ additional_context.strategy_artifact | tojson(indent=2) if additional_context.strategy_artifact else "No artifact data available" }}
```

The reviewer shared these insights to help you refine the strategy:

> {{ additional_context.feedback_notes }}

Please enhance your StrategyArtifact by incorporating this feedback. Consider how these suggestions can improve the overall technical approach while building on the solid foundation you've already established.
{% else %}
No specific clarifications were provided. Proceed based on the original task context and approved requirements.
{% endif %}

---
### **Thinking Methodology**
{% for principle in persona.thinking_methodology %}
- {{ principle }}
{% endfor %}

---
### **Directive: Develop Technical Strategy**

Based on the full task context, develop a concise technical strategy.

- **Strategy:** Define the overall technical approach (e.g., "Create a new microservice," "Refactor the existing `UserService`," "Add a new middleware layer").
- **Components:** List the major new or modified components, classes, or modules.
- **Dependencies (Optional):** List any new third-party libraries that will be required.
- **Risks (Optional):** Note any potential risks or important architectural trade-offs.

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

You MUST now call `alfred.submit_work` with a `StrategyArtifact`.

**Required Artifact Structure:**
```json
{
  "high_level_strategy": "string",
  "key_components": ["string"],
  "new_dependencies": ["string", "Optional"],
  "risk_analysis": "string", "Optional"
}
```