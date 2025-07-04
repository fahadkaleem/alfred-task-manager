## COMMAND TEMPLATE STRUCTURE

```markdown
---
allowed-tools: [Specific tools based on requirements]
description: [Professional, concise description]
---

You are a [specific role] assistant for [specific context]. Your task is to [specific objective with clear boundaries].

IMPORTANT: [Primary constraint about what NOT to do]. Your only action should be to [what they SHOULD do].

## Task Information
[Dynamic information fetching using ! commands if needed]

## TASK OVERVIEW

1. First, [initial data gathering step]:
   - Use [tool] to [specific action]
   - [Additional sub-steps]

2. Next, [analysis or processing step]:
   - [Specific actions with tools]
   - [Decision criteria]

3. [Continue numbered steps as needed]

4. Generate [output type] following the format below

## OUTPUT FORMAT

[Structured format with clear sections]
```

[Remainder of format specification]

```

## IMPORTANT GUIDELINES

- [Critical constraint 1]
- [Critical constraint 2]
- [Safety measure]
- Your only output should be [expected output]

[Additional sections as needed based on requirements]

$ARGUMENTS
```

## BEST PRACTICES TO APPLY

1. **Role Clarity**: Start with "You are a [role]" - no ambiguity
2. **Front-load Constraints**: IMPORTANT sections early and repeated
3. **Sequential Workflow**: Numbered steps create deterministic path
4. **Tool Specificity**: Exact tools with usage warnings
5. **Output Structure**: Professional format with no emojis
6. **Safety First**: Multiple fail-safes and boundaries
7. **Zero Ambiguity**: Every instruction is explicit

## EXAMPLE PATTERNS TO FOLLOW

### For Analysis Commands
- Start with data gathering
- Follow with systematic analysis
- End with structured report

### For Action Commands
- Start with validation checks
- Follow with safety confirmations
- Execute with clear boundaries
- Report what was done

### For Review Commands
- Start with context loading
- Follow with criteria-based checking
- End with actionable recommendations

### For Research-Based Commands
- Leverage discovered patterns in tool selection
- Build constraints based on codebase limitations
- Design workflow around actual file structures
- Create outputs that match existing conventions