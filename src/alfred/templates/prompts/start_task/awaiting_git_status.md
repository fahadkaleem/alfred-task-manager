# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.start_task`
# TASK: {{ task.task_id }}
# STATE: awaiting_git_status

Welcome. I am {{ persona.name }}, your {{ persona.title }}.

{{ persona.context }}

---
### **System Checkpoint: Environment Assessment**

Before we begin work on task **{{ task.task_id }}**, we must establish a clean working environment.

Please execute:
```bash
git status
```

Report the current repository state for validation.

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

You MUST now call `alfred.submit_work` with a `GitStatusArtifact`.

**Required Artifact Structure:**
```json
{
  "is_clean": "boolean - True if working directory has no uncommitted changes.",
  "current_branch": "string - The name of the current git branch.",
  "uncommitted_changes": "list[string] - List of files with uncommitted changes, if any."
}
```