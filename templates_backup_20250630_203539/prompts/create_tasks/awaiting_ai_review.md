# AI Review: Task Breakdown

## Task ID: {{ task.task_id }}

Please review the task breakdown for completeness and quality.

## Tasks to Review

{{ additional_context.drafting_tasks_artifact | tojson(indent=2) }}

## Review Guidelines

Evaluate the task breakdown for:
1. Complete coverage of the technical specification
2. Logical ordering and dependencies
3. Appropriate task granularity (1-3 days of work)
4. Clear acceptance criteria
5. Technical feasibility

Call `provide_review` with your assessment.