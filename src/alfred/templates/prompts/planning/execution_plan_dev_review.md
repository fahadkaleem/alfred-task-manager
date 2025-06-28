# Human Review Required: Execution Plan Phase - Task {{ task_id }}

{{ persona.name }} ({{ persona.title }}) has completed the execution plan and it's ready for your review.

## Current Execution Plan Artifact
The AI has created a step-by-step implementation plan based on the approved solution design.

## Review Guidance
Please review the execution plan focusing on:
- Complete coverage of the solution design
- Clarity and actionability of each step
- Correct dependency ordering
- Adequacy of testing strategy
- Achievability of success criteria

## Available Actions
- To **approve and complete planning**, call: `approve_and_handoff(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

**Note**: This plan will be executed step-by-step by the developer. Ensure it's clear and complete before approval.
