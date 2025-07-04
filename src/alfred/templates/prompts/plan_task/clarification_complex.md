<!--
Template: plan_task.clarification
Purpose: Conversational clarification of discovered ambiguities
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - context_discovery_artifact: Results from discovery phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Engage in conversational clarification with the human to resolve all discovered ambiguities and gain domain knowledge not available in training data.

# BACKGROUND
Context discovery has been completed and ambiguities have been identified. Now you must engage in real conversation with the human to:
- Resolve all discovered ambiguities with their domain expertise
- Understand business context and decisions not captured in code
- Clarify requirements and expectations
- Gain domain knowledge that will inform the design

**Note**: After clarification, the workflow will automatically determine if this task is simple enough to skip the CONTRACTS phase and proceed directly to implementation planning. This is based on complexity assessment from discovery.

This is a CONVERSATIONAL phase - engage in natural dialogue, ask follow-up questions, and seek clarification until all ambiguities are resolved.

**Discovery Results:**
- Complexity: ${context_discovery_artifact.complexity_assessment}
- Files Affected: ${context_discovery_artifact.relevant_files}
- Ambiguities Found: ${context_discovery_artifact.ambiguities_discovered}

${feedback_section}

# INSTRUCTIONS
1. **Present Ambiguities**: Show each discovered ambiguity with full context from your exploration
2. **Conversational Dialogue**: Engage in natural conversation - ask follow-ups, seek examples, clarify nuances
3. **Domain Knowledge Transfer**: Learn from human expertise about business logic, edge cases, and decisions
4. **Requirement Refinement**: Update and clarify requirements based on conversation
5. **Question Everything Unclear**: Don't make assumptions - if something is unclear, ask
6. **Document Conversation**: Keep track of what you learn for future reference

# CONSTRAINTS
- This is conversational, not just Q&A - engage naturally
- Focus on resolving ambiguities that impact design decisions
- Don't ask implementation details - focus on requirements and approach
- Seek domain knowledge that's not available in the codebase
- Be specific with your questions and provide context

# OUTPUT
Create a ClarificationArtifact with the following structure:

## Schema Documentation

### ResolvedAmbiguity Object
```json
{
  "original_question": "string",      // The question from discovery phase
  "human_response": "string",         // What the human answered
  "clarification": "string",          // Your understanding of the resolution
  "follow_up_questions": ["string"],  // Any follow-up questions you asked
  "final_decision": "string"          // The actionable decision (min 10 chars)
}
```

### RequirementUpdate Object
```json
{
  "original_requirement": "string",   // What the requirement was before
  "updated_requirement": "string",    // What it is now after clarification
  "reason_for_change": "string"       // Why this change was needed
}
```

### ConversationEntry Object
```json
{
  "speaker": "enum",                  // MUST be "AI" or "Human"
  "message": "string",                // The message content
  "timestamp": "string"               // Optional timestamp
}
```

### Complete ClarificationArtifact Structure
```json
{
  "resolved_ambiguities": [           // List of ResolvedAmbiguity objects
    // See ResolvedAmbiguity schema above
  ],
  "updated_requirements": [           // List of RequirementUpdate objects
    // See RequirementUpdate schema above
  ],
  "domain_knowledge_gained": [        // List of key insights (strings)
    "Business rule: Orders over $1000 require manager approval",
    "Edge case: Cancelled orders must retain audit trail for 7 years"
  ],
  "conversation_log": [               // List of ConversationEntry objects
    // See ConversationEntry schema above
  ],
  "business_context": {               // Dict of business decisions
    "key": "Business context that impacts technical approach"
  },
  "additional_constraints": [         // List of new constraints discovered
    "Must integrate with legacy billing system",
    "Response time must be under 200ms"
  ]
}
```

**Required Action:** Call `alfred.submit_work` with a `ClarificationArtifact`

# EXAMPLES

## Complete Example: Resolving Priority Implementation Ambiguity

### Good ResolvedAmbiguity Example
```json
{
  "original_question": "Should priority be a required field or optional with a default value?",
  "human_response": "Make it optional with MEDIUM as default. We have hundreds of existing tasks.",
  "clarification": "Priority will be an optional field defaulting to MEDIUM to maintain backward compatibility with existing tasks",
  "follow_up_questions": [
    "Should existing tasks display as MEDIUM priority or show 'No priority set'?",
    "Do you want a migration script to set all existing tasks to MEDIUM explicitly?"
  ],
  "final_decision": "Priority field will be Optional[TaskPriority] with default=TaskPriority.MEDIUM. Existing tasks will transparently show as MEDIUM priority without migration."
}
```

### Good ConversationEntry Example
```json
{
  "speaker": "AI",
  "message": "I found that the ranking algorithm currently considers: 1) in-progress status, 2) ready status, 3) task age. Where should priority fit in this hierarchy?",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Good RequirementUpdate Example
```json
{
  "original_requirement": "Have the system consider priority when recommending next tasks",
  "updated_requirement": "Priority should be the second factor after in-progress status but before ready status in task recommendations",
  "reason_for_change": "Human clarified that we shouldn't interrupt in-progress work but should respect priority for new task selection"
}
```

### Example Conversation Flow
1. AI: "I discovered two auth systems. Which one needs updating?"
2. Human: "Focus on OAuth2Service, that's our main auth now."
3. AI: "Got it. Should we deprecate LegacyAuthService as part of this?"
4. Human: "No, keep it for now. Some internal tools still use it."
5. AI: "Understood. I'll only modify OAuth2Service and ensure no breaking changes to legacy system."