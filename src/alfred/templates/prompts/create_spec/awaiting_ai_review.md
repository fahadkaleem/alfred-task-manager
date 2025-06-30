# AI Review: Engineering Specification

## Task ID: {{ task.task_id }}

Please review the engineering specification for completeness and quality.

## Specification to Review

{{ additional_context.drafting_spec_artifact | tojson(indent=2) }}

## Review Guidelines

Evaluate the specification for:
1. Completeness of all required fields
2. Clarity and specificity
3. Technical soundness
4. Alignment with PRD requirements

Call `provide_review` with your assessment.