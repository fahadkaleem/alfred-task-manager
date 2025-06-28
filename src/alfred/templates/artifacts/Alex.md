---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: reviewed
---

{# This template conditionally renders the correct artifact based on the model type #}
{%- if artifact.high_level_strategy is defined %}
{# This is a StrategyArtifact #}
# Strategy: {{ task_id }}

## 1. High-Level Strategy
{{ artifact.high_level_strategy }}

## 2. Key Components
{%- for component in artifact.key_components %}
- {{ component }}
{%- endfor %}

## 3. Architectural Decisions
{{ artifact.architectural_decisions }}

## 4. Risk Analysis
{{ artifact.risk_analysis }}
{%- elif artifact.detailed_design is defined %}
{# This is a SolutionDesignArtifact #}
# Solution Design: {{ task_id }}

## 1. Approved Strategy Summary
{{ artifact.approved_strategy_summary }}

## 2. Detailed Design
{{ artifact.detailed_design }}

## 3. File Breakdown
| File Path | Action | Change Summary |
|-----------|--------|----------------|
{%- for item in artifact.file_breakdown %}
| `{{ item.file_path }}` | {{ item.action }} | {{ item.change_summary }} |
{%- endfor %}

## 4. Dependencies
{%- if artifact.dependencies %}
{%- for dependency in artifact.dependencies %}
- {{ dependency }}
{%- endfor %}
{%- else %}
None
{%- endif %}
{%- elif artifact.implementation_steps is defined %}
{# This is an ExecutionPlanArtifact #}
# Execution Plan: {{ task_id }}

## 1. Implementation Steps
{%- for step in artifact.implementation_steps %}
{{ loop.index }}. {{ step }}
{%- endfor %}

## 2. File Modifications
| File Path | Action | Description |
|-----------|--------|-------------|
{%- for mod in artifact.file_modifications %}
| `{{ mod.path }}` | {{ mod.action }} | {{ mod.description }} |
{%- endfor %}

## 3. Testing Strategy
{{ artifact.testing_strategy }}

## 4. Success Criteria
{%- for criterion in artifact.success_criteria %}
- {{ criterion }}
{%- endfor %}
{%- endif %}

---
*Phase completed by {{ persona.name }} ({{ persona.title }})*