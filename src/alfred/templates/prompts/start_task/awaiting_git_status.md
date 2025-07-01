# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Assess the current git repository state to ensure a clean working environment before starting the task.

# BACKGROUND
Before beginning work on a new task, we must establish that:
- The working directory is clean (no uncommitted changes)
- We know the current branch
- Any existing changes are properly handled

This prevents accidental mixing of changes between different tasks.

# INSTRUCTIONS
1. Execute `git status` to check the repository state
2. Analyze the output to determine:
   - Whether the working directory is clean
   - The name of the current branch
   - List of any uncommitted files
3. Report the findings in a structured artifact
4. The workflow will determine next steps based on the repository state

# CONSTRAINTS
- Accurately report the git status
- Do not make any changes to the repository at this stage
- List all uncommitted files if any exist

# OUTPUT
Create a GitStatusArtifact with:
- `is_clean`: Boolean - True if working directory has no uncommitted changes
- `current_branch`: String - The name of the current git branch
- `uncommitted_changes`: List[String] - List of files with uncommitted changes, if any

**Required Action:** Call `alfred.submit_work` with a `GitStatusArtifact`