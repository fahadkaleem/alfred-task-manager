# AI Review: Solution Design Phase - Task {{ task_id }}

You are reviewing your solution design as {{ persona.title }} {{ persona.name }}.

## Your Submitted Design
```json
{{ artifact_content_for_review }}
```

## Review Criteria

Evaluate your solution design against:

1. **Strategy Alignment**: Does the design fully implement the approved strategy?
2. **Completeness**: Are all components from the strategy addressed?
3. **File Coverage**: Have all necessary files been identified?
4. **Technical Accuracy**: Are the proposed changes technically correct?
5. **Implementation Order**: Can the changes be implemented in the order specified?
6. **Design Clarity**: Is each file change clearly described?

## Self-Review Questions
- Have I translated every aspect of the strategy into concrete file changes?
- Are there any missing files or components?
- Will developers understand exactly what to implement?
- Are the dependencies complete and accurate?
- Is this the most efficient design to achieve the strategy?

## Action Required
Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If the design is complete and ready for human review
- **REQUEST REVISION** (is_approved=false): If improvements are needed (provide specific feedback)

Focus on ensuring the design is implementable and complete.
