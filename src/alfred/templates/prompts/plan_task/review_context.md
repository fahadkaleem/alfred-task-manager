# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Manage a clarification dialogue with the human developer to get answers to all questions identified during context analysis.

# BACKGROUND
The initial context analysis has generated a list of questions that must be answered before planning can proceed. You need to:
- Present these questions clearly to the human developer
- Track which questions have been answered
- Continue prompting for missing information until all questions are resolved

**Questions to be answered:**
${artifact_summary}

# INSTRUCTIONS
1. Maintain a checklist of the questions in your context
2. Present the unanswered questions to the human developer in a clear, conversational manner
3. Receive their response (they may not answer all questions at once)
4. Check your list - if any questions remain unanswered, re-prompt the user for only the missing information
5. Repeat until all questions are answered
6. Once all questions are answered, compile a complete summary of questions and answers

# CONSTRAINTS
- Be patient and persistent in getting all questions answered
- Keep track of which questions have been answered
- Only ask for missing information, don't repeat answered questions
- Be clear and conversational in your communication

# OUTPUT
Once all questions have been answered, approve the context review with a complete summary.

**Required Action:** When all questions are answered, call `alfred.provide_review` with:
- `is_approved=true`
- `feedback_notes` containing a complete summary of all questions and their final, confirmed answers