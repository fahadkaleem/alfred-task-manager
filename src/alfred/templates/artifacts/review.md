## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Review Summary
{{ artifact.summary }}

### Approval Status
**{{ "Approved" if artifact.approved else "Revisions Requested" }}**

### Feedback
{% if artifact.feedback %}
{% for item in artifact.feedback %}
- {{ item }}
{% endfor %}
{% else %}
- N/A
{% endif %}