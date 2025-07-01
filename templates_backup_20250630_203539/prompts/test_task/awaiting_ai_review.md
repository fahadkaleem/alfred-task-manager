# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have submitted the test results. I must now perform an automated analysis of the results to determine the pass/fail status.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content | tojson(indent=2) }}
```

---
### **Directive: Automated Test Result Analysis**

**Analysis Rule:**
- Examine the `exit_code` field in the artifact.
- If `exit_code` is `0`, the test run is considered a **PASS**.
- If `exit_code` is anything other than `0`, the test run is a **FAIL**.

---
### **Required Action**
Call `alfred.provide_review`.
- Set `is_approved=True` if `exit_code` is `0`.
- Set `is_approved=False` if `exit_code` is not `0`. Provide `feedback_notes` stating "Tests failed with exit code [exit_code]. See output for details."