# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

The test results have been analyzed and are ready for your review.

**Test Command:** `{{ additional_context.test_artifact.command }}`

**Exit Code:** {{ additional_context.test_artifact.exit_code }} ({{ "PASS" if additional_context.test_artifact.exit_code == 0 else "FAIL" }})

**Test Output:**
```
{{ additional_context.test_artifact.output }}
```

---
### **Required Action**

Based on the test results:
- If tests are satisfactory, call `alfred.provide_review` with `is_approved=True`
- If tests need to be re-run or modified, call `alfred.provide_review` with `is_approved=False` and provide feedback