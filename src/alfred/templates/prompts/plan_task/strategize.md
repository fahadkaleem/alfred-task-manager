# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Create a high-level technical strategy that will guide the detailed design and implementation of the task.

# BACKGROUND
Context has been verified and any necessary clarifications have been provided. You must now develop a technical strategy that:
- Defines the overall approach to solving the problem
- Identifies key components that need to be created or modified
- Considers dependencies and potential risks
- Serves as the foundation for detailed design

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Review the verified context and requirements
2. Define the overall technical approach (e.g., "Create a new microservice," "Refactor the existing UserService," "Add a new middleware layer")
3. List the major components, classes, or modules that will be created or modified
4. Identify any new third-party libraries or dependencies required
5. Analyze potential risks or important architectural trade-offs
6. Create a concise technical strategy document

# CONSTRAINTS
- Focus on high-level approach, not implementation details
- Ensure the strategy aligns with existing architecture patterns
- Consider scalability, maintainability, and performance
- Be realistic about risks and trade-offs

# OUTPUT
Create a StrategyArtifact with:
- `high_level_strategy`: Overall technical approach description
- `key_components`: List of major new or modified components
- `new_dependencies`: Optional list of new third-party libraries
- `risk_analysis`: Optional analysis of potential risks or trade-offs

**Required Action:** Call `alfred.submit_work` with a `StrategyArtifact`