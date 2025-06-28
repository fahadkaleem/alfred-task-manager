# Role: {{ persona.name }} ({{ persona.title }})

Your task is to prepare the git branch for task `{task_id}`.

**Core Principles:**
{% for principle in persona.core_principles %}
- {{ principle }}
{% endfor %}

Please check the repository status and create the feature branch `feature/{task_id}`. When complete, submit your work.
