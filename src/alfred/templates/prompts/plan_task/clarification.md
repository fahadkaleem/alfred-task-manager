<!--
Template: plan_task.clarification
Purpose: Get answers to discovery questions
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - discovery_findings: Flattened findings from discovery
  - discovery_questions: Flattened questions from discovery
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Get answers to the questions discovered during exploration.

# DISCOVERY SUMMARY
${discovery_findings}

# QUESTIONS TO CLARIFY
${discovery_questions}

# INSTRUCTIONS
1. Present each question with its full context from discovery
2. Have a natural, multi-turn conversation with the human
3. **IMPORTANT: Track your progress internally** - humans may answer only some questions at a time:
   - Keep a mental list of which questions have been answered
   - Which questions remain unanswered
   - If human skips questions or only partially answers, acknowledge what you learned and continue asking the remaining questions
   - Do NOT submit work until ALL questions are resolved
4. Be conversational - ask follow-ups, seek clarification, ensure you truly understand
5. Document the entire dialogue in markdown format
6. Extract key decisions and new constraints discovered

# OUTPUT
Submit a simple artifact with:
- **clarification_dialogue**: Markdown Q&A conversation
- **decisions**: List of key decisions
- **additional_constraints**: Any new requirements discovered

## Example
```json
{
  "clarification_dialogue": "## Clarification Discussion\n\n**AI**: I found 3 ambiguities during discovery. Let me ask about each:\n\n1. Should priority be required or optional with default?\n2. Where does priority rank in the task selection algorithm?\n3. Should we migrate existing tasks or handle missing priority?\n\n**Human**: Make it optional with MEDIUM default. We have existing tasks.\n\n**AI**: Thank you! That answers questions 1 and 3. For question 2, where should priority rank in the selection algorithm?\n\n**Human**: After in-progress status but before ready status.\n\n**AI**: Perfect! All questions are now answered. Let me summarize what I've learned...",
  
  "decisions": [
    "Priority will be optional with default=MEDIUM",
    "Priority ranks second in algorithm after in-progress"
  ],
  
  "additional_constraints": [
    "Must maintain backward compatibility",
    "No migration needed for existing tasks"
  ]
}
```

**CRITICAL**: Only call `alfred.submit_work` when ALL questions have been answered. If any questions remain, continue the conversation.
