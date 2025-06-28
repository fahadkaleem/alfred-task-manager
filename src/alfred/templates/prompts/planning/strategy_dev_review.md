# Human Review Required: Strategy Phase - Task {{ task_id }}

{{ persona.name }} ({{ persona.title }}) has completed the strategy phase and it's ready for your review.

## Current Strategy Artifact
The AI has developed a high-level strategic plan for implementing this task.

## Review Guidance
Please review the strategy focusing on:
- Alignment with business requirements
- Technical feasibility of the proposed approach
- Completeness of the component breakdown
- Adequacy of risk analysis and mitigations
- Overall architectural soundness

## Available Actions
- To **approve this stage** and proceed to Solution Design, call: `approve_and_advance_stage(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

**Note**: This is a critical gate. The strategy sets the foundation for all subsequent work. Ensure it's correct before approving.
