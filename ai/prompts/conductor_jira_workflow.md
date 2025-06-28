# Epic Task Manager Workflow with Jira Integration

## Overview

This prompt guides you through using Epic Task Manager MCP together with Atlassian MCP to manage a complete development workflow from Jira ticket to deployment.

## Prerequisites

Ensure you have both MCPs available:
- `atlassian-mcp` - For Jira integration
- `epic-task-manager` - For workflow orchestration

## Step 1: Initialize Epic Task Manager

First, let's make sure the Epic Task Manager system is initialized:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_initialize_epic_task_manager
```

This creates the `.epic` directory structure if it doesn't exist.

## Step 2: Get Jira Ticket Details

Ask me: "Which Jira issue would you like to work on? Please provide the issue key (e.g., EP-35):"

Once I provide the issue key, fetch the details:

```
Use the atlassian-mcp to call mcp_atlassian_getJiraIssue with:
- issueIdOrKey: [the issue key I provided]
- cloudId: "your-cloud-id" (or use mcp_atlassian_getAccessibleAtlassianResources first if needed)
```

## Step 3: Start Work on the Task

With the Jira details fetched, start the task in Epic Task Manager:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_start_new_task with:
- task_id: [the Jira issue key]
```

This will create a context file and set the task to "retrieved" phase.

## Step 4: Update Context with Jira Details

The task is now in "retrieved" phase. You should:

1. Open the context file at `.epictaskmanager/contexts/[ISSUE-KEY].md`
2. Replace the placeholder "[Fetch from Jira MCP and add details here]" with the actual Jira ticket information including:
   - Summary
   - Description
   - Acceptance Criteria
   - Priority
   - Any other relevant details

## Step 5: Planning Phase

Once the Jira details are added to the context, advance to planning:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_approve_and_advance
```

Now you're in the planning phase. The prompt file at `.epictaskmanager/prompts/planning.md` will guide you. Create a comprehensive implementation plan and add it to the context file.

## Step 6: Coding Phase

After completing the plan, advance to coding:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_approve_and_advance
```

**IMPORTANT: Update Jira status to "In Progress"**

```
Use the atlassian-mcp to call mcp_atlassian_transitionJiraIssue with:
- issueIdOrKey: [the issue key]
- transition: { "id": "[in-progress-transition-id]" }
```

Now implement the solution according to your plan. The coding prompt will guide you.

## Step 7: Self-Review Phase

Once implementation is complete:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_approve_and_advance
```

Perform a thorough self-review following the self_review prompt guidelines. Test the implementation locally and document findings.

## Step 8: Mark Ready for PR

After self-review is done:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_mark_task_ready_for_pr with:
- task_id: [the issue key]
```

Create a pull request for your changes, then:

**IMPORTANT: Update Jira status to "Code Review"**

1. Update the Jira ticket status:
```
Use the atlassian-mcp to call mcp_atlassian_transitionJiraIssue with:
- issueIdOrKey: [the issue key]
- transition: { "id": "[code-review-transition-id]" }
```

2. Add a comment to Jira with PR link:
```
Use the atlassian-mcp to call mcp_atlassian_addCommentToJiraIssue with:
- issueIdOrKey: [the issue key]
- commentBody: "Development completed through Epic Task Manager workflow. PR: [ADD PR LINK]. Ready for team review and verification."
```

**Note:** MCP workflow ends here. Team review, final testing, and deployment happen outside MCP.

## Workflow Summary

The complete workflow is:
1. Initialize Epic Task Manager → 2. Fetch Jira → 3. Start Task → 4. Add Jira Details → 5. Plan → 6. Code (→ Jira: In Progress) → 7. Self-Review → 8. Ready for PR (→ Jira: Code Review)

**MCP Phase Progression:** retrieved → planning → coding → self_review → ready_for_pr
**Jira Status Progression:** TO DO → TO DO → In Progress → In Progress → Code Review

## Status Checking

At any time, you can check the current status:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_get_current_status
```

Or continue work on the current task:

```
Use the epic-task-manager MCP to call mcp_epic-task-manager_continue_current_task
```

## Important Notes

- Each phase transition opens a new context for focused work
- The context file (`.epictaskmanager/contexts/[ISSUE-KEY].md`) maintains the complete development history
- Edit the context file directly to add domain knowledge or corrections
- Follow the prompts in `.epictaskmanager/prompts/[phase].md` for guidance in each phase
- The workflow enforces linear progression - you cannot skip phases

## Error Handling

If you encounter errors:
- "No active task found" - Use `mcp_epic-task-manager_start_new_task` with the Jira issue key
- "Cannot advance from [phase]" - The task may be complete or you need to complete the current phase
- Jira connection issues - Check your Atlassian MCP configuration

Now, let's begin the workflow. Which Jira issue would you like to work on?
