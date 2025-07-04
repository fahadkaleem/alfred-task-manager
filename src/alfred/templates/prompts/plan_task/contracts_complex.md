<!--
Template: plan_task.contracts
Purpose: Interface-first design of all APIs and contracts
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - context_discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Design all interfaces, method signatures, data models, and contracts before any implementation details. This is contract-first design.

# BACKGROUND
Context has been discovered and ambiguities resolved. Now you must design the complete interface layer:
- Method signatures with exact parameters and return types
- Data models with validation and relationships
- API contracts for external interfaces
- Integration contracts for component interactions
- Error handling strategies and exception types

This is ARCHITECTURAL design - focus on WHAT interfaces exist and HOW they interact, not implementation details.

**Previous Phase Results:**
- Discovery: ${context_discovery_artifact}
- Clarifications: ${clarification_artifact}

${feedback_section}

# INSTRUCTIONS
1. **Method Contract Design**: Define all new methods with exact signatures, parameters, return types, and error conditions
2. **Data Model Specification**: Create or update data structures, validation rules, and relationships
3. **API Contract Definition**: Specify external interfaces, request/response schemas, and error responses
4. **Integration Contracts**: Define how components will interact, dependencies, and communication patterns
5. **Error Handling Strategy**: Design exception types, error codes, and recovery patterns
6. **Testing Interface Design**: Consider how each contract will be tested and validated

# CONSTRAINTS
- Focus on interfaces and contracts, not implementation
- Follow existing patterns discovered in codebase exploration
- Ensure all contracts are testable and verifiable
- Consider error cases and edge conditions
- Design for the requirements clarified in previous phase

# OUTPUT
Create a ContractDesignArtifact with:
- `method_contracts`: All method signatures with specifications
- `data_models`: Data structure definitions and validation rules
- `api_contracts`: External interface specifications
- `integration_contracts`: Component interaction specifications
- `error_handling_strategy`: Exception types and error patterns

**Required Action:** Call `alfred.submit_work` with a `ContractDesignArtifact`

# EXAMPLES
Good method contract:
```
class_name: "UserAuthService"
method_name: "authenticate"
signature: "authenticate(email: str, password: str) -> AuthResult"
purpose: "Authenticate user credentials and return auth result"
error_handling: ["ValidationError for invalid input", "AuthenticationError for failed auth"]
test_approach: "Unit tests with mock credentials, integration tests with test users"
```

Good data model:
```
name: "AuthResult"
fields: [{"name": "user", "type": "User", "required": true}, {"name": "token", "type": "str", "required": true}]
validation_rules: [{"field": "token", "rule": "JWT format validation"}]
relationships: [{"field": "user", "references": "User model"}]
```