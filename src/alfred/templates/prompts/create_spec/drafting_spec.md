# Review Your Engineering Specification

You previously created an engineering specification. Please review it carefully and consider if any improvements are needed.

## Task ID: ${task_id}

## Your Engineering Specification

${task_artifact_content}

## Review Checklist

Consider the following:

1. **Completeness**: Are all required fields populated with meaningful content?
2. **Requirements Coverage**: Does the spec fully address all aspects of the PRD?
3. **Technical Accuracy**: Are the technical choices appropriate and well-justified?
4. **Success Metrics**: Are both product and engineering success criteria clearly defined?
5. **API Design**: Are all API changes clearly documented with methods and descriptions?
6. **Data Model**: Is the data storage design complete with all fields specified?
7. **Observability**: Are failure scenarios, logging, metrics, and monitoring adequately planned?
8. **Testing Strategy**: Is the testing approach comprehensive?
9. **Rollout Plan**: Is there a safe, staged rollout strategy?
10. **Dependencies**: Are all dependencies and dependents identified?

## Quality Standards

- Each section should provide actionable information
- No placeholder or vague content
- All lists should have concrete items, not generic statements
- Technical decisions should be justified
- Edge cases and failure modes should be considered

## Next Steps

If you're satisfied with the specification:
- Call `provide_review` with `is_approved=true`

If you want to make improvements:
- Call `provide_review` with `is_approved=false` and provide specific feedback
- You'll have the opportunity to revise the specification