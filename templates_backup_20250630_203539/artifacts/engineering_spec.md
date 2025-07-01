# Engineering Specification: {{ artifact.project_name }}

## Overview
{{ artifact.overview }}

## Definition of Success

### Product Perspective
{{ artifact.definition_of_success.product_perspective }}

### Engineering Perspective
{{ artifact.definition_of_success.engineering_perspective }}

## Functional Requirements
{% for req in artifact.functional_requirements %}
- {{ req.story }}
{% endfor %}

## Non-Functional Requirements
{% for req in artifact.non_functional_requirements %}
- {{ req }}
{% endfor %}

## Assumptions
{% for assumption in artifact.assumptions %}
- {{ assumption }}
{% endfor %}

## Major Design Considerations
{{ artifact.major_design_considerations }}

## Architecture
{{ artifact.architecture_diagrams }}

## API Changes
{% for api in artifact.api_changes %}
- {{ api }}
{% endfor %}

## Data Storage
{% for storage in artifact.data_storage %}
- {{ storage }}
{% endfor %}

## Dependencies
{% for dep in artifact.dependencies %}
- {{ dep }}
{% endfor %}

## Testing Approach
{{ artifact.testing_approach }}

## Rollout Plan
{{ artifact.rollout_plan }}

## Alternatives Considered
{{ artifact.alternatives_considered }}