# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: contextualize

I am beginning the planning process for '{{ task.title }}'.

**Task Context:**
- **Goal:** {{ task.context }}
- **Implementation Overview:** {{ task.implementation_details }}
- **Acceptance Criteria:**
{% for criterion in task.acceptance_criteria %}
  - {{ criterion }}
{% endfor %}

{% if additional_context.feedback_notes %}
---
### **Building on Your Previous Analysis**

Your earlier ContextAnalysisArtifact has been reviewed and needs some refinements. Here's what you submitted:

```json
{{ additional_context.context_artifact | tojson(indent=2) if additional_context.context_artifact else "No artifact data available" }}
```

The reviewer provided this feedback to help strengthen your analysis:

> {{ additional_context.feedback_notes }}

Please refine your ContextAnalysisArtifact by incorporating these suggestions. Focus on addressing the specific areas highlighted while maintaining the quality of your existing work.

{% endif %}
---
### **Directive: Codebase Analysis & Ambiguity Detection**

Your mission is to become the expert on this task. You must:
1.  **Analyze the existing codebase.** Start from the project root. Identify all files and code blocks relevant to the provided Task Context.
2.  **Identify Ambiguities.** Compare the task goal with your code analysis. Create a list of precise questions for the human developer to resolve any uncertainties or missing requirements.

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

You MUST now call `alfred.submit_work` with a `ContextAnalysisArtifact`.

**Required Artifact Structure:**
```json
{
  "context_summary": "string - A summary of your understanding of the existing code and how the new feature will integrate.",
  "affected_files": ["string - A list of files you have identified as relevant."],
  "questions_for_developer": ["string - Your list of precise questions for the human developer."]
}
```