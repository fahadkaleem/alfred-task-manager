# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

The review artifact has passed AI review and is now ready for your final approval.

**Review Summary:**
{{ additional_context.review_artifact.summary }}

**Approval Status:** {{ "Approved" if additional_context.review_artifact.approved else "Changes Requested" }}

**Feedback:**
{% for item in additional_context.review_artifact.feedback %}
- {{ item }}
{% endfor %}

---
### **Required Action**

Based on your assessment:
- If you agree with the review, call `alfred.provide_review` with `is_approved=True`
- If you want to modify the review, call `alfred.provide_review` with `is_approved=False` and provide feedback