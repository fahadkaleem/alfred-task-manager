# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_strategy

The initial technical strategy has been drafted. I will now perform a self-review to ensure its quality and alignment with the project goals before presenting it for human approval.

---
### **Directive: AI Self-Review**

Critically evaluate the strategy you just created.

**Review Checklist:**
1.  **Goal Alignment:** Does the strategy directly address all acceptance criteria for '{{ task.title }}'?
2.  **Feasibility:** Is the strategy technically sound and achievable within a reasonable scope?
3.  **Completeness:** Are all key components and potential dependencies identified?
4.  **Simplicity:** Is this the simplest viable approach, or is there a less complex alternative?

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

If the strategy passes your self-review, call `alfred.provide_review` with `is_approved=True`. The `feedback_notes` should contain a brief summary of your review (e.g., "Strategy is sound and covers all ACs.").

If the strategy is flawed, call `alfred.provide_review` with `is_approved=False` and provide detailed `feedback_notes` on what needs to be corrected. You will then be prompted to create a new strategy.