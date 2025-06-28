---
{{ metadata }}
---

# Test Results: {{ task_id }}

## Test Execution Summary

**Command:** `{{ test_results.command_run }}`
**Exit Code:** {{ test_results.exit_code }}

## Test Output

```
{{ test_results.full_output }}
```