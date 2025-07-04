<!--
Template: plan_task.discovery
Purpose: Deep context discovery and codebase exploration
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - restart_context: Re-planning context (if any)
  - autonomous_mode: Whether running in autonomous mode
  - autonomous_note: Note about autonomous mode behavior
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Perform comprehensive context discovery by exploring the codebase in parallel using all available tools to build deep understanding before planning begins.

# BACKGROUND
You are beginning the discovery phase of planning. This is the foundation phase where you must:
- Use multiple tools simultaneously (Glob, Grep, Read, Task) for parallel exploration
- Understand existing patterns, architectures, and conventions
- Identify all files and components that will be affected
- Discover integration points and dependencies
- Collect ambiguities for later clarification (don't ask questions yet)
- Extract code snippets and context that will be needed for self-contained subtasks

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

${autonomous_note}

# INSTRUCTIONS
1. **Parallel Exploration**: Use Glob, Grep, Read, and Task tools simultaneously to explore the codebase
   - **If tool unavailable/fails**: Use available alternatives or provide best-effort analysis based on context
   - **Fallback strategy**: Document what exploration was attempted vs. what succeeded
2. **Pattern Recognition**: Identify existing coding patterns, architectural decisions, and conventions to follow
3. **Impact Analysis**: Map out all files, classes, and methods that will be affected by this task
4. **Dependency Mapping**: Understand how the new functionality will integrate with existing code
5. **Context Extraction**: Gather code snippets, method signatures, and examples that subtasks will need
6. **Ambiguity Collection**: Note questions and unclear requirements (don't ask yet - just collect)
7. **Complexity Assessment**: Determine if this is LOW/MEDIUM/HIGH complexity based on scope
8. **Tool Error Handling**: If exploration tools fail, document limitations and proceed with available information

# CONSTRAINTS
- Use multiple tools in parallel for maximum efficiency
- Focus on understanding, not designing solutions yet
- Collect ambiguities for later clarification phase
- Extract sufficient context for completely self-contained subtasks
- Follow existing codebase patterns and conventions

# OUTPUT
Create a ContextDiscoveryArtifact with the following structure:

## Schema Documentation

### CodePattern Object
```json
{
  "pattern_type": "string",        // e.g., "error_handling", "validation", "service_pattern"
  "example_code": "string",        // Actual code snippet showing the pattern
  "usage_context": "string",       // When/how this pattern is used
  "file_locations": ["string"]     // List of file paths where pattern is found
}
```

### IntegrationPoint Object
```json
{
  "component_name": "string",      // Name of component to integrate with
  "integration_type": "enum",      // MUST be one of the following values:
    // External integrations:
    // - "API_ENDPOINT"           // For REST API endpoints
    // - "DATABASE"               // For database operations
    // - "SERVICE_CALL"           // For service-to-service calls
    // - "FILE_SYSTEM"            // For file system operations
    // - "EXTERNAL_API"           // For third-party API calls
    
    // Code structure integrations:
    // - "DATA_MODEL_EXTENSION"   // Adding fields to existing models
    // - "PARSER_EXTENSION"       // Extending parser functionality
    // - "ALGORITHM_MODIFICATION" // Modifying existing algorithms
    // - "TEMPLATE_ADDITION"      // Adding new templates
    // - "CLASS_INHERITANCE"      // Inheriting from existing classes
    // - "INTERFACE_IMPLEMENTATION" // Implementing interfaces
    // - "METHOD_OVERRIDE"        // Overriding existing methods
    // - "CONFIGURATION_UPDATE"   // Updating configuration
    // - "WORKFLOW_EXTENSION"     // Extending workflow states
    // - "STATE_MACHINE_UPDATE"   // Updating state machines
    
  "interface_signature": "string", // Method signature or API endpoint
  "dependencies": ["string"],      // List of required dependencies
  "examples": ["string"]          // List of usage examples (MUST be array!)
}
```

### AmbiguityItem Object
```json
{
  "question": "string",           // MUST end with "?" and be specific
  "context": "string",            // Code/context related to ambiguity
  "impact_if_wrong": "string",    // Consequences of wrong assumption
  "discovery_source": "string"    // Where this was discovered
}
```

### Complete ContextDiscoveryArtifact Structure
```json
{
  "codebase_understanding": {     // Free-form dict with your findings
    "any_key": "any_value"        // Document what you discovered
  },
  "code_patterns": [              // List of CodePattern objects
    // See CodePattern schema above
  ],
  "integration_points": [         // List of IntegrationPoint objects
    // See IntegrationPoint schema above - USE VALID ENUM VALUES!
  ],
  "relevant_files": [             // Simple list of file paths
    "src/file1.py",
    "src/file2.py"
  ],
  "existing_components": {        // Dict mapping names to purposes
    "ComponentName": "What it does"
  },
  "ambiguities_discovered": [     // List of AmbiguityItem objects
    // See AmbiguityItem schema above
  ],
  "extracted_context": {          // Free-form dict with code snippets
    "any_key": "any_value"        // Include reusable code/patterns
  },
  "complexity_assessment": "enum", // MUST be: "LOW", "MEDIUM", or "HIGH"
  "discovery_notes": [            // List of strings
    "Note about what was discovered",
    "Note about tool limitations"
  ]
}
```

**Required Action:** Call `alfred.submit_work` with a `ContextDiscoveryArtifact`

# EXAMPLES

## Complete Example: Adding Priority Field to Task Model

### Good IntegrationPoint Example (CORRECT)
```json
{
  "component_name": "Task Model",
  "integration_type": "DATA_MODEL_EXTENSION",  // Valid enum value!
  "interface_signature": "Task(**task_data)",
  "dependencies": ["pydantic.BaseModel", "TaskPriority enum"],
  "examples": [                                // Array format required!
    "Add priority field with TaskPriority type",
    "Set default value to TaskPriority.MEDIUM"
  ]
}
```

### Bad IntegrationPoint Example (WRONG)
```json
{
  "component_name": "Task Model",
  "integration_type": "data_model",            // WRONG: Not a valid enum
  "interface_signature": "Task(**task_data)",
  "dependencies": ["pydantic.BaseModel"],
  "examples": "Add priority field"             // WRONG: Must be array!
}
```

### Good CodePattern Example
```json
{
  "pattern_type": "enum_definition",
  "example_code": "class TaskStatus(str, Enum):\n    NEW = \"new\"\n    PLANNING = \"planning\"\n    DONE = \"done\"",
  "usage_context": "String-based enums for JSON serialization compatibility",
  "file_locations": ["src/alfred/models/schemas.py:20-39"]
}
```

### Good AmbiguityItem Example
```json
{
  "question": "Should priority be required or optional with a default value?",
  "context": "Task model could enforce priority as required, but this breaks existing tasks. Optional with default=MEDIUM maintains compatibility.",
  "impact_if_wrong": "If required: All existing tasks fail to load. If optional: Smooth migration.",
  "discovery_source": "Analysis of Task model and existing task files"
}
```

### Common Integration Types by Use Case
- Extending a parser? Use `"PARSER_EXTENSION"`
- Adding model fields? Use `"DATA_MODEL_EXTENSION"`
- Modifying algorithms? Use `"ALGORITHM_MODIFICATION"`
- Overriding methods? Use `"METHOD_OVERRIDE"`
- Adding templates? Use `"TEMPLATE_ADDITION"`
- Updating configs? Use `"CONFIGURATION_UPDATE"`