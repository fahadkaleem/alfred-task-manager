# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

My self-review is complete and approved. The artifact is now ready for your final human review and approval.

**Artifact for Your Review:**
```json
{{ additional_context.artifact_content | fromjson if additional_context.artifact_content else {} }}
```

---
### **Directive: Await Human Approval**

Present the ContextAnalysisArtifact to the human developer for their review and approval. They will provide feedback on whether the codebase analysis and ambiguity questions are satisfactory.

**What to look for in the human's response:**
- Simple approval signals like "yes", "approve", "looks good", "LGTM"
- Specific feedback requesting changes to the context summary, affected files, or questions
- Additional requirements or clarifications they want to add

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

Based on the human developer's response:
- If they approve, call `alfred.provide_review` with `is_approved=True`
- If they request changes, call `alfred.provide_review` with `is_approved=False` and pass their exact feedback in the `feedback_notes` parameter