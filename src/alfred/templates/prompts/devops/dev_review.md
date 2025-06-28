# Role: DevOps Manager Review
# Task: {{ task_id }}

The DevOps Engineer has completed the finalization process. Please review the submission below:

---
**Submitted Artifact:**
{{ artifact_content_for_review }}
---

## Review Instructions:

1. **Verify the commit hash** appears to be a valid 40-character hexadecimal string
2. **Verify the pull request URL** follows a proper GitHub URL format
3. **Confirm completion** of the workflow finalization

## Available Actions:

- **Approve:** Call `provide_review(task_id="{{ task_id }}", is_approved=True)` if the artifact looks correct
- **Request Changes:** Call `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="Your specific feedback here")` if changes are needed

This is the final review step before task completion.
