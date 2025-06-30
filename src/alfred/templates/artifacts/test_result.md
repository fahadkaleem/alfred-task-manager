## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Test Execution Summary
**Command:** `{{ artifact.command }}`
**Exit Code:** {{ artifact.exit_code }} ({{ "Success" if artifact.exit_code == 0 else "Failure" }})

### Full Output
```
{{ artifact.output }}
```