# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_context

My initial analysis has generated the following questions. I must now clarify these with the human developer to ensure my understanding is complete before proceeding with the technical strategy.

---
### **Directive: User Clarification**

Present these questions to the human developer and await their answers.

**My Questions:**
{% set artifact = artifact_content | fromjson %}
{% for question in artifact.questions_for_developer %}
- {{ question }}
{% endfor %}

---
### **Required Action**

Once you have the developer's answers, you MUST call `alfred.provide_review` with `is_approved=True` and include the developer's answers in the `feedback_notes`. Format the notes as a clear Q&A string.

If the developer rejects the context and wants you to re-analyze, call `provide_review` with `is_approved=False`.