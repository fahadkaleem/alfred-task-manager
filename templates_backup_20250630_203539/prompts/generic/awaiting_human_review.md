# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

My self-review is complete. The artifact for the `{{ additional_context.last_state | replace("_", " ") | title }}` step is now ready for your final approval.

**Artifact for Your Review:**
```json
{{ additional_context.artifact_content }}
```

---
### **Directive: Await Human Approval**

Present the artifact to the human developer for their review and approval. They will provide a simple "yes/no" or "approve/reject" decision.

-   If they approve, call `alfred.provide_review` with `is_approved=True`.
-   If they request changes, call `alfred.provide_review` with `is_approved=False` and pass their exact feedback in the `feedback_notes` parameter.