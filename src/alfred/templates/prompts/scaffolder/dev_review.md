# Human Review Required: Scaffolding Phase - Task {{ task_id }}

Scaffy (Code Scaffolder) has completed the scaffolding phase and it's ready for your review.

## Current ScaffoldingManifest Artifact
The AI has processed the execution plan and inserted TODO comments throughout the codebase to guide implementation.

## Review Guidance

Please review the scaffolding work focusing on:

### 1. TODO Comment Quality
- Are the TODO comments clear and actionable?
- Do they provide sufficient context for implementation?
- Are they properly formatted with step IDs and descriptions?

### 2. Coverage and Completeness
- Have all files mentioned in the execution plan been scaffolded?
- Are all execution plan steps properly represented?
- Is the scaffolding comprehensive enough to guide development?

### 3. Separation of Concerns
- Verify that only TODO comments were added (no implementation code)
- Ensure scaffolding maintains clear boundaries with actual development
- Check that the scaffolding provides guidance without being prescriptive

### 4. Developer Readiness
- Will the TODO comments help a developer understand what to implement?
- Are the comments organized logically within each file?
- Is there sufficient detail to proceed with confidence?

## What to Look For

**Good Scaffolding:**
- Clear, actionable TODO items with specific guidance
- Proper organization within files
- Helpful implementation notes and context
- Complete coverage of execution plan requirements

**Issues to Flag:**
- Vague or unclear TODO comments
- Missing scaffolding for required files
- Implementation code mixed with scaffolding
- Insufficient detail for development

## Available Actions

- To **approve this phase** and proceed to Development, call: `approve_and_handoff(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

## Review Files

You may want to examine the scaffolded files directly to verify:
- TODO comment format and clarity
- Implementation guidance quality
- Complete coverage of planned changes

**Note**: This is the final gate before development begins. Ensure the scaffolding provides clear direction for implementation.
