# Human Review Required: Solution Design Phase - Task {{ task_id }}

{{ persona.name }} ({{ persona.title }}) has completed the solution design phase and it's ready for your review.

## Current Design Artifact
The AI has created a detailed technical design based on the approved strategy.

## Review Guidance
Please review the solution design focusing on:
- Complete implementation of the approved strategy
- Technical correctness of proposed changes
- Completeness of file breakdown
- Feasibility of implementation
- Clarity of change descriptions

## Available Actions
- To **approve this stage** and proceed to Execution Planning, call: `approve_and_advance_stage(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

**Note**: This design will directly guide the implementation. Ensure it's complete and accurate before approval.
