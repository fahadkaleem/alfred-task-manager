# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have submitted the review artifact. I must now perform a self-review to ensure the feedback is clear, actionable, and fair.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content | tojson(indent=2) }}
```

---
### **Directive: AI Self-Review**

**Review Checklist:**
1. **Clarity:** Is the `summary` clear? Is the `feedback` specific and easy to understand?
2. **Actionability:** If `approved` is false, does the feedback give the developer a clear path to fixing the issues?
3. **Tone:** Is the feedback constructive and professional?

---
### **Required Action**
Call `alfred.provide_review` with `is_approved=True` if the review artifact is high quality.