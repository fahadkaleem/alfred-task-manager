# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Execute the implementation phase by completing all subtasks from the approved execution plan.

# BACKGROUND
You are now in the implementation phase. An execution plan with detailed subtasks has been created and approved. Your role is to:
- Work through each subtask systematically
- Track progress as you complete each one
- Ensure all acceptance criteria are met
- Create a comprehensive implementation manifest when done

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

**Execution Plan:**
${artifact_json}

# INSTRUCTIONS
1. Review the execution plan and subtasks
2. Implement each subtask in order, following the LOST specifications
3. After completing each subtask, call `alfred.mark_subtask_complete` with the task_id and subtask_id
4. Test your implementation as you go
5. Once all subtasks are complete, create an implementation manifest
6. Submit the final manifest for review

# CONSTRAINTS
- Follow the execution plan precisely
- Each subtask must be fully completed before moving to the next
- Maintain code quality and follow project conventions
- Ensure all tests pass before marking subtasks complete

# OUTPUT
When all subtasks are complete, create an ImplementationManifestArtifact with:
- `summary`: Brief summary of what was implemented
- `completed_subtasks`: List of completed subtask IDs
- `testing_notes`: Any notes about testing or validation

**Required Action:** Call `alfred.submit_work` with your `ImplementationManifestArtifact`