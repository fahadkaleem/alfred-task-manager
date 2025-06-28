---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: verified
---

# Test Results: {{ task_id }}

## Test Execution Summary

**Command:** `{{ artifact.test_results.command_run }}`
**Exit Code:** {{ artifact.test_results.exit_code }}

## Test Output

```
{{ artifact.test_results.full_output }}
```