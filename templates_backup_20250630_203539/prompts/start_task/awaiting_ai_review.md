# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have just submitted my artifact for review. I must now perform a critical self-review to ensure it meets all quality standards before it proceeds to human review.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content | fromjson if additional_context.artifact_content else {} }}
```

---
### **Directive: AI Self-Review**

Critically evaluate the submitted artifact against the requirements for this step of the start_task workflow.

**Review Checklist:**
1. **Data Accuracy:** Is all information in the artifact accurate and complete?
2. **Required Fields:** Are all required fields present and properly formatted?
3. **Git Status Assessment:** For GitStatusArtifact, does the assessment align with proper Git workflow practices?
4. **Branch Strategy:** For BranchCreationArtifact, was the branch creation successful and properly named?

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

Call `alfred.provide_review`.
- If the artifact meets all quality standards, set `is_approved=True`.
- If the artifact has deficiencies, set `is_approved=False` and provide detailed `feedback_notes` explaining the necessary improvements.