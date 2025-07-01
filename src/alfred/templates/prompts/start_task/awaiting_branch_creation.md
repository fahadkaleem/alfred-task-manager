# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Create and switch to a new feature branch for the task implementation.

# BACKGROUND
The human operator has approved the branch creation. You must now:
- Create a new feature branch named `feature/${task_id}`
- Switch to this branch
- Verify the operation was successful

This ensures all work for this task is isolated in its own branch.

# INSTRUCTIONS
1. Execute the git command to create and switch to the new branch:
   ```bash
   git checkout -b feature/${task_id}
   ```
2. If the branch already exists, use:
   ```bash
   git checkout feature/${task_id}
   ```
3. Capture the command output
4. Verify you are now on the correct branch
5. Report the outcome in a structured artifact

# CONSTRAINTS
- Use the exact branch naming convention: `feature/${task_id}`
- Handle both cases: branch creation and switching to existing branch
- Accurately report success or failure

# OUTPUT
Create a BranchCreationArtifact with:
- `branch_name`: String - The name of the branch (should be `feature/${task_id}`)
- `success`: Boolean - True if the command executed without errors
- `details`: String - The output from the git command

**Required Action:** Call `alfred.submit_work` with a `BranchCreationArtifact`