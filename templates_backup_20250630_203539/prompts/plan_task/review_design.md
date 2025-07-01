# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_design

The detailed design has been drafted. I will now perform a self-review to ensure it fully implements the approved strategy.

---
### **Directive: AI Self-Review**

Critically evaluate the design against the original strategy.

**Review Checklist:**
1. **Strategy Coverage:** Does the `file_breakdown` fully and accurately implement every `key_component` mentioned in the strategy?
2. **Clarity:** Is the `change_summary` for each file clear, specific, and actionable?
3. **Correctness:** Are the file paths and proposed operations logical and correct?

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

If the design is sound, call `alfred.provide_review` with `is_approved=True` and a brief confirmation in `feedback_notes`.

If the design is flawed or incomplete, call `alfred.provide_review` with `is_approved=False` and detailed `feedback_notes` on the necessary corrections.