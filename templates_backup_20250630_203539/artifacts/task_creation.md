# Task Breakdown

## Tasks Created

{% for task in artifact.tasks %}
### {{ task.task_id }}: {{ task.title }}

**Context:**  
{{ task.context }}

**Implementation Details:**  
{{ task.implementation_details }}

**Acceptance Criteria:**
{% for ac in task.acceptance_criteria %}
- {{ ac }}
{% endfor %}

**Verification Steps:**
{% for step in task.ac_verification_steps %}
- {{ step }}
{% endfor %}

---

{% endfor %}