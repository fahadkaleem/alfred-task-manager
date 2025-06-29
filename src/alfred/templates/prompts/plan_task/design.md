# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: design

The technical strategy has been approved. Now, you must translate this strategy into a detailed, file-level implementation design.

**Approved Strategy:**
```json
{{ additional_context.strategize_artifact | tojson(indent=2) }}
```

---
### **Directive: Create Detailed Design**

Based on the approved strategy, create a comprehensive, file-by-file breakdown of all necessary changes. For each file that needs to be created or modified, provide a clear summary of the required changes.

---
### **Required Action**

You MUST now call `alfred.submit_work` with a `DesignArtifact`.

**Required Artifact Structure:**
```json
{
  "design_summary": "string",
  "file_breakdown": [
    {
      "file_path": "string",
      "change_summary": "string",
      "operation": "create | modify"
    }
  ]
}
```