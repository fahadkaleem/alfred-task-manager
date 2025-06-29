# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have just submitted the artifact for the `{{ additional_context.last_state | replace("_", " ") | title }}` step. I must now perform a critical self-review to ensure the artifact meets all quality standards before it proceeds to human review.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content }}
```

---
### **Directive: AI Self-Review**

Critically evaluate the artifact above against the original goal of the step.

**Review Checklist:**
1.  **Completeness:** Does the artifact contain all required fields and information?
2.  **Clarity:** Is the information clear, specific, and unambiguous?
3.  **Correctness:** Does the artifact accurately reflect the work that was required?
4.  **Adherence to Standards:** Does the artifact follow all specified formatting and structural rules?

---
### **Required Action**

Call `alfred.provide_review`.
-   If the artifact is perfect, set `is_approved=True`.
-   If the artifact has any flaws, set `is_approved=False` and provide detailed `feedback_notes` explaining the necessary corrections.