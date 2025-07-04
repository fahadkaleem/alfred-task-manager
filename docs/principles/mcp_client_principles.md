# MCP Client Interface Principles

## Core Philosophy
MCP clients are **external users without source code access**. They rely entirely on tool descriptions and prompts to understand how to use our tools correctly.

## The Golden Rules

### 1. PROMPTS MUST BE SELF-DOCUMENTING
- Every data structure mentioned in a prompt MUST include its complete schema
- Never assume clients can "figure out" field names or types
- If you mention an object type, show its JSON structure immediately

### 2. EXAMPLES ARE MANDATORY
- Every complex data structure needs at least one complete, valid example
- Include both GOOD (correct) and BAD (wrong) examples
- Annotate examples with comments explaining key points

### 3. ENUM VALUES MUST BE LISTED
- Never just say "integration_type enum" - list ALL valid values
- Include descriptions of when to use each value
- Group related values with explanatory headers

### 4. ERROR MESSAGES MUST GUIDE
- Don't just say what's wrong - show what's right
- Include partial examples in error messages
- Suggest the closest valid option for invalid inputs

### 5. VALIDATION SHOULD TEACH
- Validation errors should educate, not just reject
- Show the expected format alongside what was provided
- Explain WHY something is invalid, not just that it is

## Required Sections for Tool Prompts

### Schema Documentation Section
```markdown
## Schema Documentation

### ObjectName
\```json
{
  "field_name": "type",        // Description of field
  "enum_field": "enum",        // MUST be one of: VALUE1, VALUE2, VALUE3
  "array_field": ["type"],     // Array of elements (note the brackets!)
  "nested_object": {           // Nested object structure
    "sub_field": "type"
  }
}
\```
```

### Examples Section
```markdown
## Examples

### Good Example (CORRECT)
\```json
{
  "field": "value",            // Why this is correct
  "enum": "VALID_VALUE"        // Using proper enum
}
\```

### Bad Example (WRONG)  
\```json
{
  "field": value,              // WRONG: Missing quotes
  "enum": "invalid"            // WRONG: Not a valid enum value
}
\```
```

## Common Patterns

### For Enum Fields
```markdown
"integration_type": "enum",      // MUST be one of the following values:
  // External integrations:
  // - "API_ENDPOINT"           // For REST API endpoints
  // - "DATABASE"               // For database operations
  
  // Code structure integrations:
  // - "DATA_MODEL_EXTENSION"   // Adding fields to existing models
  // - "PARSER_EXTENSION"       // Extending parser functionality
```

### For Array Fields
```markdown
"examples": ["string"]          // List of examples (MUST be array!)
// CORRECT: ["example1", "example2"]
// WRONG: "example1"            // Single string not allowed
```

### For Complex Objects
```markdown
### Complete Structure
\```json
{
  "simple_field": "string",
  "complex_field": {
    "nested": "value"
  },
  "array_field": [
    {"item": "value"}
  ]
}
\```
```

## Testing MCP Interfaces

Before releasing any MCP tool:

1. **Black Box Test**: Test without looking at source code
2. **Schema Completeness**: Verify all mentioned types are documented
3. **Example Validity**: Ensure all examples actually work
4. **Error Helpfulness**: Trigger errors and check if messages guide to solution

## Anti-Patterns to Avoid

### ❌ Vague Type References
```markdown
Create a ContextDiscoveryArtifact with:
- integration_points: List of IntegrationPoint objects
```

### ✅ Complete Type Documentation
```markdown
Create a ContextDiscoveryArtifact with:
- integration_points: List of IntegrationPoint objects, where each has:
  - component_name: string
  - integration_type: one of ["PARSER_EXTENSION", "DATA_MODEL_EXTENSION", ...]
  - examples: array of strings (e.g., ["example1", "example2"])
```

### ❌ Enum Without Values
```markdown
"complexity_assessment": enum based on scope
```

### ✅ Enum With All Values
```markdown
"complexity_assessment": "enum", // MUST be: "LOW", "MEDIUM", or "HIGH"
```

## The MCP Client Promise

*"As an MCP tool developer, I promise that my tools will be fully usable by someone who has never seen my source code. My prompts will teach, my errors will guide, and my examples will illuminate the path to success."*

---

Remember: Your MCP client might be an AI agent, a human developer, or an automated system. They all deserve clear, complete, and helpful interfaces.