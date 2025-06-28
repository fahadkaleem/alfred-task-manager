Analyze a module's code to identify patterns, conventions, and important information that should be documented in its Claude.md file.

## Task

Examine the specified module (or current directory if not specified) and suggest what should be added to its Claude.md documentation.

## Analysis Steps

### 1. Code Pattern Detection

- Identify recurring patterns in the code
- Note naming conventions actually used
- Detect common import patterns
- Find frequently used decorators or utilities

### 2. Dependency Analysis

- List all imports to understand dependencies
- Identify which other modules this one uses
- Note external libraries utilized

### 3. Complexity Detection

- Find complex functions that might need explanation
- Identify non-obvious algorithms or logic
- Spot potential gotchas or edge cases

### 4. Testing Analysis

- Check test coverage and patterns
- Identify testing strategies used
- Note any special test fixtures or mocks

### 5. API Surface Analysis

- List public functions/classes
- Identify the main entry points
- Document expected usage patterns

## Output Format

```
Analysis for module: [module_name]

Detected Patterns:
- Pattern 1: [description with example]
- Pattern 2: [description with example]

Key Dependencies:
- Internal: [list of project modules]
- External: [list of third-party libraries]

Complex Areas Needing Documentation:
- [Function/class]: [why it's complex]

Testing Insights:
- Test pattern: [description]
- Special considerations: [any gotchas]

Suggested Claude.md Additions:
[Formatted content ready to add]
```

Arguments: $ARGUMENTS (module path, defaults to current directory)
