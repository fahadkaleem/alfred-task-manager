# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}

# OBJECTIVE
Present the artifact to the human developer for final review and approval.

# BACKGROUND
The artifact has passed AI self-review and is now ready for human validation. The human will provide a simple approval decision or request specific changes.

**Artifact Summary:** ${artifact_summary}

# INSTRUCTIONS
1. Present the complete artifact below to the human developer
2. Wait for their review decision
3. If they approve, proceed with approval
4. If they request changes, capture their exact feedback
5. Submit the review decision

**Artifact for Review:**
```json
${artifact_json}
```

# CONSTRAINTS
- Present the artifact clearly and completely
- Capture human feedback verbatim if changes are requested
- Do not modify or interpret the human's feedback

# OUTPUT
Process the human's review decision:
- If approved, advance the workflow
- If changes requested, return to the previous step with feedback

**Required Action:** Call `alfred.provide_review` with the human's decision
- For approval: `is_approved=true`
- For revision: `is_approved=false` with their exact feedback in `feedback_notes`