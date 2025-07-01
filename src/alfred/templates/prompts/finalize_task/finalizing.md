# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Create a git commit and pull request for the completed implementation.

# BACKGROUND
The implementation has been completed and tested. Now create the final commit and pull request to complete the task workflow.

# INSTRUCTIONS
1. Create a descriptive git commit with all changes
2. Push the changes to a new branch or existing feature branch
3. Create a pull request with proper description
4. Capture the actual commit hash and PR URL

# CONSTRAINTS
- Use descriptive commit messages following project standards
- Include the task ID in commit message and PR title
- Ensure all changes are committed before creating PR

# OUTPUT
Create a FinalizeArtifact with these exact fields:
- **commit_hash**: The actual git SHA hash of the created commit
- **pr_url**: The actual URL of the created pull request

**Required Action:** Call `alfred.submit_work` with a `FinalizeArtifact`

# EXAMPLES
```json
{
  "commit_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "pr_url": "https://github.com/user/repo/pull/123"
}
```

```json
{
  "commit_hash": "f9e8d7c6b5a4958372615048392817465029384756",
  "pr_url": "https://github.com/myorg/myproject/pull/456"
}
```