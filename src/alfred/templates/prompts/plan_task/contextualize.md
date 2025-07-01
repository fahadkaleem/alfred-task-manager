# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Analyze the existing codebase and identify any ambiguities or questions that need clarification before planning can begin.

# BACKGROUND
You are beginning the planning process for a new task. Before creating a technical strategy, you must understand:
- The current codebase structure and relevant components
- Any existing patterns or conventions to follow
- Potential areas of ambiguity that need clarification

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Analyze the codebase starting from the project root
2. Identify all files and components relevant to this task
3. Note any existing patterns or conventions that should be followed
4. Create a list of specific questions about any ambiguities or unclear requirements
5. Prepare a comprehensive context analysis

# CONSTRAINTS
- Focus only on understanding, not designing solutions yet
- Questions should be specific and actionable
- Identify actual ambiguities, not hypothetical issues
- Consider both technical and business context

# OUTPUT
Create a ContextAnalysisArtifact with:
- `context_summary`: Your understanding of the existing code and how the new feature will integrate
- `affected_files`: List of files that will likely need modification
- `questions_for_developer`: Specific questions that need answers before proceeding

**Required Action:** Call `alfred.submit_work` with a `ContextAnalysisArtifact`

# EXAMPLES
Good question: "Should the new authentication system integrate with the existing UserService or create a separate AuthService?"
Bad question: "How should I implement this?" (too vague)