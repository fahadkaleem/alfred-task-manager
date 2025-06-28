# Human Review Required - Implementation Complete
# Task: {{ task_id }}

The implementation for task `{{ task_id }}` has been completed and validated by the AI. Please review the implementation manifest and the actual code changes.

**Implementation Manifest:**
{{ artifact_content }}

## Review Options:

1. **Approve and Handoff to QA:**
   Use `approve_and_handoff(task_id="{{ task_id }}")` to approve this work and handoff the task to the QA persona.

2. **Request Revisions:**
   Use `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")` to request specific changes.
