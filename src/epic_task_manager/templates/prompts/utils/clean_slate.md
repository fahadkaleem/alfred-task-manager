<system_command name="clean_slate">
  <objective>Suggest that the human user start a new chat session to optimize performance before proceeding with the main task.</objective>
  <instructions>
    1.  **PAUSE** all other actions.
    2.  **Output this exact text to the user:** "A new major phase of work has begun. To ensure the best performance and a clean context, I recommend we start a new chat session."
    3.  **Wait for the user's response.**
    4.  If the user agrees or starts a new session, your first command in the new session MUST be `mcp_epic-task-manager_begin_or_resume_task(task_id="{task_id}")`.
    5.  If the user wishes to continue in the current session, disregard this command and proceed with the rest of the prompt below.
  </instructions>
</system_command>
