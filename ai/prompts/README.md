# Epic Task Manager + Jira Workflow Prompts

I've created several prompts for you to test the Epic Task Manager + Jira integration with EP-35. Choose the one that works best for your testing style:

## 1. Quick Start (Recommended for First Test)
**File**: `ai/prompts/implement_next_task.md`
- Most concise version
- Step-by-step numbered list
- Easy to copy/paste into Cursor
- Perfect for quick testing

## 2. Detailed Assistant
**File**: `ai/prompts/epic_task_manager_assistant.md`
- Most comprehensive version
- Includes example outputs
- Explicit about every parameter
- Self-starting (begins initialization automatically)

## 3. Workflow Instructions
**File**: `ai/prompts/cursor_workflow_instructions.md`
- Medium detail level
- Good error recovery guidance
- Clear rules and status commands

## 4. Complete Documentation
**File**: `ai/prompts/epic_task_manager_jira_workflow.md`
- Full workflow documentation
- Educational - explains why each step
- Good for understanding the system

## Testing with EP-35

1. Copy one of the prompts above into a new Cursor chat
2. When asked for the Jira issue, respond with: `EP-35`
3. Follow along as Cursor guides you through the entire workflow

## What to Expect

The workflow will:
1. Initialize the Epic Task Manager system
2. Fetch EP-35 details from Jira
3. Create a task in Epic Task Manager
4. Guide you through: Planning → Coding → Review → Complete
5. Update the Jira ticket to Done
6. Add a completion comment to Jira

## Current System Status

- Total Tasks: 3 (all completed)
- Active Tasks: 0
- System is ready for EP-35

Good luck with the test! 🚀
