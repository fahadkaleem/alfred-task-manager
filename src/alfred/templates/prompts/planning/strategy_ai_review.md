# AI Review: Strategy Phase - Task {{ task_id }}

You are reviewing your own strategy artifact as {{ persona.title }} {{ persona.name }}.

## Your Submitted Strategy
```json
{{ artifact_content_for_review }}
```

## Review Criteria

Please critically evaluate your strategy against these criteria:

1. **Completeness**: Does the strategy address all aspects of the task requirements?
2. **Technical Soundness**: Is the proposed approach architecturally sound and feasible?
3. **Risk Coverage**: Have all major risks been identified with appropriate mitigations?
4. **Component Design**: Are the key components well-defined and properly scoped?
5. **Architectural Clarity**: Are the architectural decisions clear and well-justified?

## Self-Review Questions
- Is the high-level strategy clear and actionable?
- Are there any missing components or considerations?
- Do the architectural decisions follow best practices?
- Is the risk analysis comprehensive?
- Will this strategy lead to a maintainable and scalable solution?

## Action Required
Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If the strategy is comprehensive and ready for human review
- **REQUEST REVISION** (is_approved=false): If significant improvements are needed (provide specific feedback)

Be critical but fair in your assessment. The goal is to ensure high quality before human review.
