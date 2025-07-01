## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Strategy Overview
{{ artifact.high_level_strategy }}

### Key Components
{%- for component in artifact.key_components %}
- {{ component }}
{%- endfor %}
{%- if artifact.new_dependencies %}

### New Dependencies
{%- for dependency in artifact.new_dependencies %}
- {{ dependency }}
{%- endfor %}
{%- endif %}
{%- if artifact.risk_analysis %}

### Risk Analysis
{{ artifact.risk_analysis }}
{%- endif %}