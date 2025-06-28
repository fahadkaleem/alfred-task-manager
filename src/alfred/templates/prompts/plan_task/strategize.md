# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: strategize

Context is verified. The human developer has provided all necessary clarifications. We will now create the high-level technical strategy for '{{ task.title }}'. This strategy will serve as the guiding principle for the detailed design.

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