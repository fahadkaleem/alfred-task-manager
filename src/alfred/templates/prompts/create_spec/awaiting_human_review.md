# Human Review: Engineering Specification

## Task ID: {{ task.task_id }}

Please review the engineering specification that has been created.

## Specification

{{ additional_context.drafting_spec_artifact | tojson(indent=2) }}

## Your Options

1. **Approve**: Call `provide_review` with `is_approved=true`
2. **Request Changes**: Call `provide_review` with `is_approved=false` and specific feedback

The specification should be complete, technically sound, and ready for task breakdown.