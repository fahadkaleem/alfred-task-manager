# Quick Start: Work on a Jira Ticket with Epic Task Manager

Copy and paste this entire prompt into Cursor to start working on a Jira ticket with the Epic Task Manager workflow.

---

I need you to help me work on a Jira ticket using the Epic Task Manager workflow. Act naturally and conversationally throughout the process.

## CRITICAL: Server Instructions and Context Management

**MANDATORY BEHAVIOR**: When the Epic Task Manager server returns instructions marked for the user (such as context management recommendations, chat session suggestions, or workflow guidance), you MUST:

1. **STOP all current work immediately**
2. **Present the server's instructions to the user verbatim**
3. **Wait for explicit user guidance** before proceeding
4. **Do NOT continue with workflow steps** until the user has responded

**Exception**: You may ignore server instructions ONLY if you are explicitly operating in "YOLO mode" (user has specifically requested you to ignore all interruptions and proceed automatically).

**Context Management Protocol**:
- When the server recommends "START NEW CHAT SESSION" or similar context management actions, treat this as a CRITICAL WORKFLOW REQUIREMENT, not a mere suggestion
- The server's context management recommendations are based on technical limitations and performance optimization
- Present these recommendations as: "The system is recommending we start a fresh chat session to maintain optimal performance. This helps prevent context overflow and ensures reliable workflow execution. Would you like to start a new session now?"

**Remember**: Server instructions exist for important technical and workflow reasons. Ignoring them can lead to degraded performance, workflow failures, or incomplete task execution.

1. First, initialize Epic Task Manager:
   - Call `mcp_epic-task-manager_initialize_epic_task_manager` if .epic folder does not exist

2. Ask me which issue I want to work on in a friendly way

3. When I give you the issue key:
   - Call `mcp_atlassian_getAccessibleAtlassianResources` to get the cloudId
   - Call `mcp_atlassian_getJiraIssue` with the cloudId and my issue key
   - Show me the issue summary and description
   - Give your natural reaction (e.g., "Great! This looks like a straightforward task" or "Interesting challenge - this will be fun to implement")
   - Confirm if this is what I want to work on
   - If I say no, ask what issue I'd prefer instead

4. Start working on the task:
   - Call `mcp_epic-task-manager_start_new_task` with task_id = the issue key
   - Mention you're getting started and updating the context

5. Update the context file:
   - Read `.epictaskmanager/contexts/[ISSUE-KEY].md`
   - Replace "[Fetch from Jira MCP and add details here]" with the actual Jira details
   - Save the file

6. Move to planning phase:
   - Call `mcp_epic-task-manager_approve_and_advance`
   - Read the planning prompt from `.epictaskmanager/prompts/planning.md`
   - Help me create an implementation plan
   - Add the plan to the context file
   - Request feedback naturally: "I've put together an implementation plan for {issue-key}. I'm thinking we should approach it by [brief summary]. What do you think about this plan? Ready to move forward with coding?"
   - Call `mcp_epic-task-manager_request_phase_review` internally
   - When I give feedback, call `mcp_epic-task-manager_provide_feedback` with my response
   - If revisions needed, address feedback and call `mcp_epic-task-manager_address_feedback`
   - Only advance when I approve

7. Move to coding phase:
   - Call `mcp_epic-task-manager_approve_and_advance`
   - **IMPORTANT: Update Jira status to "In Progress"**
   - Call `mcp_atlassian_getTransitionsForJiraIssue` to find "In Progress" transition
   - Call `mcp_atlassian_transitionJiraIssue` to move it to In Progress
   - Call `mcp_atlassian_atlassianUserInfo` to get current user's account_id
   - Call `mcp_atlassian_editJiraIssue` with fields: {"assignee": {"accountId": "USER_ACCOUNT_ID"}}
   - Say something like "Alright, moving to implementation! I've updated the Jira status and assigned it to you."
   - Implement the solution based on our plan
   - Update the context file with implementation notes
   - Request code review naturally: "I've finished implementing {brief description of what was built}. The code is working well and I've tested it locally. Could you take a look at what I've built? I'd love your feedback before we move to self-review."
   - Call `mcp_epic-task-manager_request_phase_review` internally
   - When I give feedback, call `mcp_epic-task-manager_provide_feedback` with my response
   - If revisions needed, fix code and call `mcp_epic-task-manager_address_feedback`

8. Move to self-review phase:
   - Call `mcp_epic-task-manager_approve_and_advance`
   - Review the code based on the self_review prompt
   - Test the implementation locally
   - Document findings in the context file
   - Request validation naturally: "I've completed my self-review and local testing. Everything looks solid - [brief summary of test results]. What do you think? Does this look ready for the team to review?"
   - Call `mcp_epic-task-manager_request_phase_review` internally
   - When I give feedback, call `mcp_epic-task-manager_provide_feedback` with my response
   - If revisions needed, fix issues and call `mcp_epic-task-manager_address_feedback`

9. Mark ready for PR:
   - Request final approval naturally: "We're almost there! I think {issue-key} is ready for PR. The implementation meets all the acceptance criteria and testing looks good. Are you happy for me to create the PR and move this to code review?"
   - Call `mcp_epic-task-manager_request_phase_review` internally
   - When I give final approval, call `mcp_epic-task-manager_provide_feedback` with my response
   - If final changes needed, make adjustments and call `mcp_epic-task-manager_address_feedback`
   - Once I approve, proceed:
   - Call `mcp_epic-task-manager_mark_task_ready_for_pr` with the task_id
   - Create a pull request for the changes
   - **IMPORTANT: Update Jira status to "Code Review"**
   - Call `mcp_atlassian_getTransitionsForJiraIssue` to find "Code Review" transition
   - Call `mcp_atlassian_transitionJiraIssue` to move it to Code Review
   - Call `mcp_atlassian_addCommentToJiraIssue` with PR link and completion message
   - Celebrate! "Awesome! {issue-key} is now ready for team review. PR created and Jira updated to Code Review status."

**Note:** MCP workflow ends here. Team review, final testing, and deployment happen outside MCP.

Throughout this process:
- Use `mcp_epic-task-manager_get_current_status` to check where we are
- Use `mcp_epic-task-manager_get_review_status` to check review cycle status
- Each phase has a specific prompt in `.epictaskmanager/prompts/[phase].md`
- The context file `.epictaskmanager/contexts/[ISSUE-KEY].md` tracks our entire journey
- **CRITICAL**: developer review and approval required at EVERY phase transition
- **CRITICAL**: Cannot advance phases without developer verification (needs_revision=false)
- Review cycles can repeat multiple times until quality standards are met
- We must go through phases in order: retrieved → planning → coding → self_review → ready_for_pr
- Jira status transitions: TO DO → TO DO → In Progress → In Progress → Code Review

## Review-Feedback Cycle Tools:
- `mcp_epic-task-manager_request_phase_review(task_id, work_summary)` - AI requests review
- `mcp_epic-task-manager_provide_feedback(task_id, feedback, needs_revision, reviewer_notes?)` - developer provides feedback
- `mcp_epic-task-manager_address_feedback(task_id, resolution_notes)` - AI addresses feedback
- `mcp_epic-task-manager_get_review_status(task_id)` - Check review status

Let's start with step 1!
