# TASK: SAMPLE-001

## Title
Example task demonstrating the correct format

## Context
This is a sample task file that demonstrates the correct markdown format expected by Alfred. It shows all required and optional sections that can be used when creating tasks.

## Implementation Details
Create a well-formatted markdown file that follows the exact structure expected by the MarkdownTaskParser. The file should include all required sections and demonstrate optional sections as well.

## Acceptance Criteria
- Task file must start with "# TASK: <task_id>" format
- Must include Title, Context, Implementation Details, and Acceptance Criteria sections
- Should follow the exact section headers expected by the parser
- Must be parseable by the MarkdownTaskParser without errors

## AC Verification
- Verify that the md_parser can successfully parse the file
- Confirm all required fields are extracted correctly
- Test that the Task pydantic model can be created from parsed data
- Ensure no validation errors occur during task loading

## Dev Notes
This file serves as both documentation and a working example. When creating new tasks, copy this format and modify the content as needed.