# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.start_task`
# TASK: {{ task.task_id }}
# STATE: branch_created

Excellent. The human operator has approved the action.

---
### **Directive: Create and Verify Branch**

Please execute the proposed git command to create and switch to the new feature branch:
`git checkout -b feature/{{ task.task_id }}`

If the branch already exists, use `git checkout feature/{{ task.task_id }}` instead.

After executing the command, please report the outcome.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

You MUST now call `alfred.submit_work` with a `BranchCreationArtifact`.

**Required Artifact Structure:**
```json
{
  "branch_name": "string - The name of the new branch, 'feature/{{ task.task_id }}'.",
  "success": "boolean - True if the command executed without errors.",
  "details": "string - The output from the git command."
}
```