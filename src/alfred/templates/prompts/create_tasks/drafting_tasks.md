# Review Your Task Breakdown

You previously created a task breakdown from the technical specification. Please review it carefully.

## Task ID: {{ task.task_id }}

## Your Task List

{{ additional_context.artifact_content }}

## Review Checklist

Consider the following:

1. **Completeness**: Do the tasks cover all aspects of the technical specification?
2. **Dependencies**: Are task dependencies correctly identified and ordered?
3. **Granularity**: Are tasks appropriately sized (1-3 days of work)?
4. **Clarity**: Is each task clear and actionable?
5. **Technical Accuracy**: Are the technical details correct?
6. **Missing Tasks**: Are there any gaps? Consider:
   - Error handling tasks
   - Testing tasks
   - Documentation tasks
   - Migration tasks
   - Monitoring/logging tasks

## Validation Questions

- Can these tasks be executed in the specified order?
- Are acceptance criteria measurable and clear?
- Would a developer understand exactly what to do for each task?
- Are effort estimates reasonable?

## Next Steps

If you're satisfied with the task breakdown:
- Call `provide_review` with `is_approved=true`

If you want to make improvements:
- Call `provide_review` with `is_approved=false` and provide specific feedback
- You'll have the opportunity to revise the task list