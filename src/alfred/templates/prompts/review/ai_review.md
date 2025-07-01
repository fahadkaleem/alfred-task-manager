# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}

# OBJECTIVE
Perform a critical self-review of the submitted artifact to ensure it meets quality standards before human review.

# BACKGROUND
An artifact has been submitted for the current workflow step. As an AI reviewer, you must evaluate whether this artifact:
- Meets all requirements for the current step
- Contains complete and accurate information
- Follows established patterns and conventions
- Is ready for human review

# INSTRUCTIONS
1. Review the submitted artifact below
2. Check against the original requirements for this step
3. Evaluate completeness, clarity, and correctness
4. Determine if any critical issues need to be addressed
5. Provide your review decision

**Submitted Artifact:**
```json
${artifact_json}
```

# CONSTRAINTS
- Be objective and thorough in your review
- Focus on substantive issues, not minor formatting
- Consider whether a human reviewer would find this acceptable
- If rejecting, provide specific, actionable feedback

# OUTPUT
Make a review decision:
- If the artifact meets all quality standards, approve it
- If there are issues that must be fixed, request revision with specific feedback

**Required Action:** Call `alfred.provide_review` with your decision
- For approval: `is_approved=true`
- For revision: `is_approved=false` with detailed `feedback_notes`