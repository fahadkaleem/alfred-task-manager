# ROLE: {{ persona.name }}, {{ persona.title }}
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

Critically evaluate the ContextAnalysisArtifact above against the original goal of understanding the codebase and identifying ambiguities.

**Review Checklist:**
1. **Context Summary Completeness:** Does the summary accurately capture the existing codebase relevant to the task?
2. **Affected Files Coverage:** Are all relevant files identified? Are any missing or unnecessary?
3. **Question Quality:** Are the questions specific, actionable, and focused on genuine ambiguities?
4. **Accuracy:** Is all technical information correct based on the codebase analysis?

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