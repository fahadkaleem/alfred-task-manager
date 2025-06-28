# AI Review: Execution Plan Phase - Task {{ task_id }}

You are reviewing your execution plan as {{ persona.title }} {{ persona.name }}.

## Your Submitted Plan
```json
{{ artifact_content_for_review }}
```

## Review Criteria

Evaluate your execution plan against:

1. **Design Coverage**: Does the plan implement all aspects of the approved design?
2. **Step Clarity**: Is each implementation step clear and actionable?
3. **Dependency Order**: Are steps arranged in the correct order?
4. **File Accuracy**: Do file modifications match the solution design?
5. **Testing Completeness**: Is the testing strategy comprehensive?
6. **Success Criteria**: Are the criteria measurable and complete?

## Self-Review Questions
- Can a developer follow these steps without ambiguity?
- Have I included all necessary implementation details?
- Will executing these steps result in a working implementation?
- Are there any missing steps or dependencies?
- Is the testing strategy sufficient to validate the implementation?

## Action Required
Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If the plan is complete and ready for human review
- **REQUEST REVISION** (is_approved=false): If improvements are needed (provide specific feedback)

This is your final check before the plan is handed to the developer persona.
