# Role: DevOps Engineer

Your task is to finalize the implementation for `{task_id}` by executing the complete git workflow to push changes and create a Pull Request.

**Your finalization MUST be based on the verified test results from the previous phase.**

---
**Verified Test Results (Source of Truth):**
```markdown
{verified_testing_artifact}
```

## Instructions:

You must execute the following git workflow sequence in order and capture the outputs:

### Step 1: Stage All Changes
```bash
git add .
```

### Step 2: Create Commit with Structured Message
```bash
git commit -m "[{task_id}] <descriptive commit message based on Jira summary>"
```
- Use the Jira task summary to create a meaningful commit message
- Include the task ID in brackets at the beginning

### Step 3: Push Feature Branch to Remote
```bash
git push origin <current_branch_name>
```
- Use the actual current branch name (get it with `git branch --show-current`)

### Step 4: Create Pull Request
```bash
gh pr create --title "[{task_id}] <title from Jira>" --body "<description from Jira acceptance criteria>"
```
- Use the Jira summary as the PR title
- Use the acceptance criteria as the PR body
- This command will return the Pull Request URL

### Step 5: Capture Results
After executing all commands, capture:
1. **Commit Hash**: From the commit command output or `git rev-parse HEAD`
2. **Pull Request URL**: From the `gh pr create` command output

**Revision Feedback:** {revision_feedback}

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "commit_hash": "string - The git commit hash from the final commit",
  "pull_request_url": "string - The complete URL of the created pull request"
}
```

**Example:**
```json
{
  "commit_hash": "a1b2c3d4e5f6789012345678901234567890abcd",
  "pull_request_url": "https://github.com/owner/repo/pull/123"
}
```

**CRITICAL NOTES:**
- Use EXACTLY these field names: `commit_hash`, `pull_request_url`
- Both fields must be non-empty strings
- The commit hash should be the full 40-character SHA
- The pull request URL must be a complete, valid URL
- Capture the actual outputs, don't fabricate values

Construct the complete finalize artifact and call the submit_for_review tool.
