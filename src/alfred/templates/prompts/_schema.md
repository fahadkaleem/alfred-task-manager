# Alfred Prompt Template Guidelines

## Structure
Every prompt should follow the standard sections:
1. CONTEXT - Current state and task information
2. OBJECTIVE - Clear, single-sentence goal
3. BACKGROUND - Necessary context and previous work
4. INSTRUCTIONS - Step-by-step guide
5. CONSTRAINTS - Limitations and requirements
6. OUTPUT - Expected format and action
7. EXAMPLES (optional) - Good/bad examples

## Variables
Standard variables available in all prompts:
- `${task_id}` - The task identifier
- `${tool_name}` - Current tool name
- `${current_state}` - Current workflow state
- `${task_title}` - Task title
- `${task_context}` - Task goal/context
- `${implementation_details}` - Implementation overview
- `${acceptance_criteria}` - Formatted AC list

## Writing Guidelines
1. **Be explicit** - State exactly what you want
2. **Use consistent tone** - Professional but conversational
3. **Number instructions** - Makes them easy to follow
4. **Include examples** - When behavior might be ambiguous
5. **Specify output format** - Be clear about expected structure
6. **End with action** - Always specify the required function call

## Testing Your Prompts
1. Check all variables are defined
2. Verify instructions are clear and ordered
3. Ensure output format is unambiguous
4. Test with edge cases
5. Review generated outputs for quality