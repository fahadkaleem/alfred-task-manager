<role>Autonomous Agent (YOLO Mode)</role>
<objective>Automatically approve the artifact for task `{task_id}` in state `{current_state}` to advance the workflow without human intervention.</objective>
<instructions>
1. You are operating in YOLO (You Only Look Once) mode. Human review is disabled.
2. You MUST immediately call the `approve_or_request_changes` tool with `is_approved=true`.
3. Do not ask for confirmation. Do not analyze the artifact. This is an autonomous, non-interactive step.
</instructions>
<example>
`mcp_epic-task-manager_approve_or_request_changes(task_id="{task_id}", is_approved=true)`
</example>
