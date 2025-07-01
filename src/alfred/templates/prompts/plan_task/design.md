# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Translate the approved technical strategy into a detailed, file-level implementation design.

# BACKGROUND
The technical strategy has been approved and provides the high-level approach. You must now create a comprehensive design that:
- Breaks down the strategy into specific file changes
- Provides clear implementation guidance for each component
- Ensures all acceptance criteria can be met
- Maintains consistency with the existing codebase

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Review the approved strategy and task requirements
2. For each component in the strategy, determine the specific files that need to be created or modified
3. For each file, provide a clear summary of the required changes
4. Ensure the design covers all acceptance criteria
5. Consider the order of implementation and any dependencies between changes
6. Create a comprehensive design document

# CONSTRAINTS
- Be specific about file paths and change details
- Ensure consistency with existing code patterns
- Consider backward compatibility where applicable
- Design should be implementable without ambiguity

# OUTPUT
Create a DesignArtifact with:
- `design_summary`: Overview of the implementation approach
- `file_breakdown`: Array of file changes, each containing:
  - `file_path`: Full path to the file
  - `change_summary`: Description of changes needed
  - `operation`: Either "create" or "modify"

**Required Action:** Call `alfred.submit_work` with a `DesignArtifact`