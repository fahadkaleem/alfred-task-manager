# Parallel Subtask Generation Using Sub-Agents

## Overview

This document describes a revolutionary approach to generating self-contained subtasks using parallel sub-agents in the Alfred planning workflow. Instead of a single AI agent trying to detail multiple subtasks (which leads to quality degradation), we leverage multiple specialized sub-agents working in parallel, each focused on creating one perfect subtask specification.

**IMPORTANT**: This enhancement requires **NO infrastructure changes** to Alfred. It's achieved entirely through prompt engineering in the `implementation_plan` phase, leveraging the AI model's ability to orchestrate multiple parallel Task tool calls.

## The Complete Planning Flow

### Phase 1: DISCOVERY
**Purpose**: Deep, parallel exploration of the codebase to understand what exists

**What Happens**:
- Use Glob, Grep, Read, Task tools simultaneously
- Extract code patterns, integration points, dependencies
- Identify ambiguities that need clarification
- Build comprehensive context about the codebase

**Key Outputs**:
```json
{
  "findings": "Markdown summary of discoveries",
  "questions": ["What auth method to use?", "Should we migrate existing data?"],
  "files_to_modify": ["src/models/user.py", "src/services/auth.py"],
  "complexity": "MEDIUM",
  "implementation_context": {
    "patterns": {"error_handling": "try/except with logger"},
    "integrations": ["Database", "EmailService"]
  }
}
```

### Phase 2: CLARIFICATION
**Purpose**: Resolve ambiguities through human-AI conversation

**What Happens**:
- Present discovered ambiguities with full context
- Have natural conversation to resolve questions
- Capture domain knowledge and business decisions

**Key Outputs**:
```json
{
  "clarification_dialogue": "Full Q&A conversation",
  "decisions": [
    "Use JWT for authentication",
    "30-day token expiry",
    "No migration needed"
  ],
  "additional_constraints": [
    "Must support refresh tokens",
    "Rate limit: 5 attempts per minute"
  ]
}
```

### Phase 3: CONTRACTS
**Purpose**: Define exact interfaces before any implementation

**What Happens**:
- Design all method signatures with types
- Define data models with validation
- Specify error handling patterns
- Create the "blueprint" that all code must follow

**Example Contract Output**:
```python
# Authentication Contract
class AuthService:
    def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate user and return auth result with tokens"""
        
    def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh access token using refresh token"""
        
    def revoke_token(self, token: str) -> None:
        """Revoke a token (logout)"""

# Data Models Contract        
@dataclass
class User:
    id: int
    email: str
    hashed_password: str
    created_at: datetime
    
@dataclass
class AuthResult:
    user: User
    access_token: str
    refresh_token: str
    expires_at: datetime

# Repository Contract
class UserRepository:
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address"""
        
    def save(self, user: User) -> User:
        """Persist user to database"""

# Error Contracts
class AuthenticationError(Exception):
    """Raised when authentication fails"""
    
class TokenExpiredError(Exception):
    """Raised when token has expired"""
```

### Phase 4: IMPLEMENTATION_PLAN (With Parallel Sub-Agents)

**Purpose**: Create detailed, self-contained subtask specifications using parallel processing

**Implementation**: This is achieved by modifying the `implementation_plan.md` template to instruct the AI to use the Task tool for parallel subtask generation. No code or state machine changes needed!

#### Step 1: Main Agent Creates High-Level Outline

**Prompt**:
```markdown
# CONTEXT
Task: ${task_id} - ${task_title}

Based on our discoveries, clarifications, and contracts, break down the implementation into logical subtasks.

# DISCOVERED CONTEXT
${discovery_findings}

# KEY DECISIONS
${clarification_decisions}

# CONTRACTS TO IMPLEMENT
${contracts}

# INSTRUCTIONS
Create a high-level subtask outline. Each subtask should:
- Implement a specific part of the contracts
- Be independent enough for parallel execution
- Have clear boundaries and responsibilities

Output a simple list of subtasks with their primary contract focus.
```

**Example Output**:
```json
{
  "subtask_outline": [
    {
      "subtask_id": "ST-001",
      "title": "Create User model and database schema",
      "primary_contract": "User model",
      "estimated_complexity": "LOW"
    },
    {
      "subtask_id": "ST-002", 
      "title": "Implement UserRepository with database operations",
      "primary_contract": "UserRepository",
      "estimated_complexity": "MEDIUM"
    },
    {
      "subtask_id": "ST-003",
      "title": "Create AuthService with JWT implementation",
      "primary_contract": "AuthService",
      "estimated_complexity": "HIGH"
    }
  ]
}
```

#### Step 2: Launch Parallel Sub-Agents

The main agent now launches multiple sub-agents IN PARALLEL, one for each subtask:

**Sub-Agent Prompt Template**:
```markdown
# YOUR FOCUSED TASK
You are a specialized agent responsible for creating a complete, self-contained specification for ONE subtask.

## SUBTASK ASSIGNMENT
ID: ${subtask.id}
Title: ${subtask.title}
Primary Contract: ${subtask.primary_contract}

## COMPLETE CONTEXT

### Discovery Findings
${relevant_discovery_findings}

### Clarification Decisions
${relevant_decisions}

### All Contracts
${all_contracts}

### Integration Points
${integration_dependencies}

## YOUR MISSION
Create an EXHAUSTIVE specification for implementing this subtask. Since you're focused on just ONE subtask, be incredibly thorough.

Your specification must include:

1. **Exact Implementation Location**
   - File path: src/...
   - Class name (if applicable)
   - Method names to implement
   - Line numbers or relative positions

2. **Step-by-Step Implementation Guide**
   - Detailed steps in order
   - Exact code patterns to follow
   - Specific imports needed
   - Error handling approach

3. **Methods and Interfaces**
   - List each method/function you're implementing
   - Show exact type signatures
   - Describe expected behavior
   - Note error cases to handle

4. **Code Context**
   - Dependencies this relies on
   - What other subtasks produce that you need
   - Integration points with existing code

5. **Testing Requirements**
   - Unit tests to write
   - Test file location
   - Specific test cases
   - Mock requirements

6. **Verification Criteria**
   - How to know implementation is complete
   - How to verify it works with other subtasks

Output your specification in clean markdown format.
```

**Example Sub-Agent Output** (for AuthService subtask):
```markdown
## Subtask: ST-003 - Create AuthService with JWT implementation

**Goal**: Implement JWT-based authentication with refresh tokens

**Location**: `src/services/auth_service.py` → `AuthService` class

**Methods to Implement**:
- [ ] `authenticate(email: str, password: str) -> AuthResult`
- [ ] `refresh_token(refresh_token: str) -> AuthResult`  
- [ ] `revoke_token(token: str) -> None`

**Dependencies**:
- ST-001: User model must be complete
- ST-002: UserRepository.find_by_email() must exist
- External: pyjwt>=2.8.0, bcrypt>=4.0.0

**Implementation Steps**:
1. Create AuthService class with dependency injection
   - Accept UserRepository and secret_key in __init__
   - Set token TTLs (access: 30min, refresh: 30days)

2. Implement authenticate method
   - Find user by email (raise AuthenticationError if not found)
   - Verify password with bcrypt
   - Generate JWT tokens with proper claims
   - Return AuthResult with user and tokens

3. Implement refresh_token method
   - Decode and validate refresh token
   - Check token type and expiry
   - Generate new access token
   - Return updated AuthResult

4. Implement revoke_token method
   - Add token to blacklist/revocation store
   - Log revocation event

**Testing Requirements**:
- File: `tests/services/test_auth_service.py`
- Test valid authentication flow
- Test invalid credentials handling
- Test token refresh logic
- Test token revocation
- Mock: UserRepository, fixed datetime

**Verification**:
- [ ] All methods have correct type hints
- [ ] Authentication errors handled properly
- [ ] Tokens are valid JWT format
- [ ] Integration with UserRepository works
- [ ] All tests pass
```

#### Step 3: Main Agent Collects and Validates

After all sub-agents complete (in parallel), the main agent collects all specifications.

### Phase 5: VALIDATION

**Purpose**: Ensure all subtasks together form a complete, coherent implementation

**Validation Prompt**:
```markdown
# VALIDATION PHASE
You have received detailed subtask specifications from parallel sub-agents. Now validate the complete plan.

## ALL SUBTASK SPECIFICATIONS
${all_subtask_specs}

## ORIGINAL CONTRACTS
${contracts}

## VALIDATION CHECKLIST

### 1. Implementation Coverage
For each required feature, verify:
- [ ] Is it implemented by at least one subtask?
- [ ] Are all method signatures exactly matching requirements?
- [ ] Are all error cases handled?

### 2. Dependency Analysis
- [ ] Do subtask dependencies form a valid DAG (no cycles)?
- [ ] Are all referenced dependencies available when needed?
- [ ] Can subtasks truly execute in parallel where claimed?

### 3. Integration Verification
- [ ] Will all pieces fit together when complete?
- [ ] Are interfaces between subtasks consistent?
- [ ] Is data flow logical and complete?

### 4. Completeness Check
- [ ] Does the union of all subtasks implement the entire task?
- [ ] Are there any gaps in functionality?
- [ ] Is every acceptance criteria addressed?

### 5. Implementation Feasibility
- [ ] Is each subtask specification realistic?
- [ ] Are file paths and imports correct?
- [ ] Will the proposed code structure work?

## OUTPUT
Provide validation results with any issues found and whether the plan is ready for implementation.
```

**Validation Output Example**:
```json
{
  "validation_summary": "All subtasks form a complete implementation of the authentication system",
  
  "implementation_coverage": {
    "complete": true,
    "coverage_map": {
      "AuthService.authenticate": "ST-003",
      "AuthService.refresh_token": "ST-003",
      "User model": "ST-001",
      "UserRepository": "ST-002"
    }
  },
  
  "dependency_validation": {
    "valid_dag": true,
    "execution_order": ["ST-001", "ST-002", "ST-003"],
    "parallel_groups": [["ST-001"], ["ST-002"], ["ST-003"]]
  },
  
  "issues_found": [],
  
  "ready_for_implementation": true
}
```

## Benefits of This Approach

1. **Quality at Scale**: Each sub-agent focuses on ONE subtask, allowing deep, thorough specifications
2. **True Parallelism**: 10 subtasks = 10 parallel context windows = 10x faster
3. **Contract Enforcement**: Main agent ensures all specifications follow the contracts
4. **Self-Contained Results**: Each subtask specification has EVERYTHING needed
5. **Validation**: The validation phase ensures the pieces fit together perfectly

## Implementation Without Infrastructure Changes

### How It Works - Pure Prompt Engineering

The key insight is that modern AI models can orchestrate parallel Task tool calls directly from the prompt. Here's how to implement this in Alfred:

#### 1. Update the `implementation_plan.md` template:

```markdown
# INSTRUCTIONS FOR COMPLEX TASKS (5+ subtasks or HIGH complexity)

Instead of detailing each subtask inline, use parallel sub-agents:

1. Create a high-level outline with subtask IDs and titles
2. For EACH subtask, call the Task tool in parallel:
   ```
   Task(
     description="Create detailed spec for ST-001",
     prompt="You are a specialist focused on ONE subtask. [Include full context...]"
   )
   ```
3. Modern AI will execute these Task calls IN PARALLEL
4. Collect all Task results
5. Validate coherence across specifications
6. Submit the combined result as your artifact

This ensures each subtask gets focused, deep attention while maintaining speed through parallelism.
```

#### 2. The AI Model Handles Everything:
- No new states in the state machine
- No changes to handlers or workflow classes  
- No modifications to Alfred's core architecture
- Just a smarter prompt that leverages AI capabilities

### Benefits of This Approach
- **Zero code changes**: Update only the template
- **Maintains simplicity**: Alfred's architecture stays clean
- **Leverages AI strengths**: Uses model's native parallelism
- **Follows all principles**: Templates remain static data
- **Backward compatible**: Works with existing Alfred installations

### Error Handling Through Prompts
- Instruct AI to retry failed sub-agents with refined prompts
- Use validation phase to catch inconsistencies
- AI can iteratively improve based on validation feedback

## Summary

This approach transforms the implementation planning phase from a single agent trying to detail many things (with declining quality) to multiple specialized agents each perfecting one thing. The validation phase ensures these independent pieces form a coherent whole that perfectly implements the contracts defined earlier.

**The key innovation**: This is achieved entirely through prompt engineering - no infrastructure changes needed. By leveraging modern AI models' ability to orchestrate parallel tool calls, we get all the benefits of parallel sub-agents while keeping Alfred's architecture simple and maintainable.

The result: incredibly detailed, self-contained subtask specifications that can be independently implemented while guaranteeing they'll work together seamlessly.