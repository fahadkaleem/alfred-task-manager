# Epic Task Manager + Jira Workflow: Step-by-Step Instructions for Cursor

## Your Task

You will help me work on a Jira ticket using the Epic Task Manager workflow. Follow these steps exactly in order.

## Step 1: Initialize the System

Execute this MCP call:
```
mcp_epic-task-manager_initialize_epic_task_manager
```

Expected response: "Initialized .epic directory..."

## Step 2: Ask for Jira Issue

Ask me exactly this:
> "Which Jira issue would you like to work on? Please provide the issue key (e.g., EP-35):"

Wait for my response.

## Step 3: Fetch Jira Details

Once I provide the issue key (let's call it ISSUE-KEY), execute:

First, get the accessible resources:
```
mcp_atlassian_getAccessibleAtlassianResources
```

Then fetch the issue details:
```
mcp_atlassian_getJiraIssue cloudId="[use the cloudId from above]" issueIdOrKey="ISSUE-KEY"
```

## Step 4: Start the Task

Execute:
```
mcp_epic-task-manager_start_new_task task_id="ISSUE-KEY"
```

This will return paths to the context and prompt files.

## Step 5: Update Context with Jira Details

1. Read the context file at `.epictaskmanager/contexts/ISSUE-KEY.md`
2. Find the section "### Jira Details"
3. Replace "[Fetch from Jira MCP and add details here]" with:
   - Issue Summary: [from Jira]
   - Issue Type: [from Jira]
   - Priority: [from Jira]
   - Description: [from Jira]
   - Acceptance Criteria: [from Jira]
   - Any linked issues or dependencies

## Step 6: Begin Planning Phase

Execute:
```
mcp_epic-task-manager_approve_and_advance
```

Now read the planning prompt at `.epictaskmanager/prompts/planning.md` and help me create an implementation plan. The plan should include:
- Files to create/modify
- Technical approach
- Potential challenges
- Time estimates

Add this plan to the context file under the "## Planning" section.

## Step 7: Begin Coding Phase

After the plan is complete, execute:
```
mcp_epic-task-manager_approve_and_advance
```

**IMPORTANT: Update Jira status to "In Progress"**

1. Get available transitions:
```
mcp_atlassian_getTransitionsForJiraIssue cloudId="[cloudId]" issueIdOrKey="ISSUE-KEY"
```

2. Find the "In Progress" transition ID and execute:
```
mcp_atlassian_transitionJiraIssue cloudId="[cloudId]" issueIdOrKey="ISSUE-KEY" transition={"id": "[in-progress-transition-id]"}
```

Now implement the solution according to the plan. Add notes about the implementation to the context file.

## Step 8: Begin Self-Review Phase

Once coding is complete, execute:
```
mcp_epic-task-manager_approve_and_advance
```

Perform a self-review based on the self_review prompt. Test the implementation locally and document any findings in the context file.

## Step 9: Mark Ready for PR

After self-review, execute:
```
mcp_epic-task-manager_mark_task_ready_for_pr task_id="ISSUE-KEY"
```

Create a pull request for your changes.

## Step 10: Update Jira to Code Review

**IMPORTANT: Update Jira status to "Code Review"**

1. Get available transitions:
```
mcp_atlassian_getTransitionsForJiraIssue cloudId="[cloudId]" issueIdOrKey="ISSUE-KEY"
```

2. Find the "Code Review" transition ID, then execute:
```
mcp_atlassian_transitionJiraIssue cloudId="[cloudId]" issueIdOrKey="ISSUE-KEY" transition={"id": "[code-review-transition-id]"}
```

3. Add a completion comment with PR link:
```
mcp_atlassian_addCommentToJiraIssue cloudId="[cloudId]" issueIdOrKey="ISSUE-KEY" commentBody="✅ Development completed using Epic Task Manager workflow.\n\nPR: [ADD PR LINK HERE]\n\nPhases completed:\n- Retrieved: Fetched Jira details\n- Planning: Created implementation plan\n- Coding: Implemented solution\n- Self-Review: Code reviewed and tested locally\n- Ready for PR: Submitted for team review\n\nAll work tracked in Epic Task Manager. Ready for team review and verification."
```

**Note:** MCP workflow ends here. Team review, final testing, and deployment happen outside MCP.

## Status Commands

Use these anytime:
- Check status: `mcp_epic-task-manager_get_current_status`
- Continue current task: `mcp_epic-task-manager_continue_current_task`

## IMPORTANT RULES

1. **Never skip phases** - The workflow must go: retrieved → planning → coding → self_review → ready_for_pr
2. **Update Jira at key transitions** - coding phase (→ In Progress) and ready_for_pr (→ Code Review)
2. **Always update the context file** - It's the source of truth for the task
3. **Follow the prompts** - Each phase has a specific prompt file with guidelines
4. **One task at a time** - Complete or explicitly switch tasks before starting another

## Error Recovery

- If MCP calls fail, check the exact parameter names and retry
- If you lose track, use `get_current_status` to see where you are
- The context file at `.epictaskmanager/contexts/ISSUE-KEY.md` always has the history

---

Now, let's begin. Please execute Step 1 to initialize the system.
