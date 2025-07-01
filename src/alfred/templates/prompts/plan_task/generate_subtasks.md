# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Transform the approved design into precision-engineered subtasks that can be executed independently by different agents without ambiguity.

# BACKGROUND
You are creating an execution plan where each subtask must be so precise, complete, and independent that any developer or AI agent could execute it in complete isolation without questions or ambiguity.

**Critical Mindset - The Isolation Principle:**
Imagine each subtask will be executed by a different agent who:
- Has NEVER seen the other subtasks
- Has NO access to project context beyond what you provide
- Cannot ask questions or seek clarification
- Must produce code that integrates perfectly with others' work

## The Deep LOST Philosophy

LOST is a methodology for eliminating ambiguity through systematic precision:

### L - Location (The Context Anchor)
- **Activates Language Context**: `src/models/user.py` tells the agent "Python, likely SQLAlchemy/Django"
- **Implies Conventions**: `src/components/UserAvatar.tsx` signals "React, TypeScript, component patterns"
- **Defines Boundaries**: Precise paths prevent accidental modifications to wrong files
- **Creates Namespace**: Helps avoid naming conflicts between parallel implementations

### O - Operation (The Precision Verb)
**Foundation Operations** (Create structure):
- `CREATE` - Generate new file/class/module from scratch
- `DEFINE` - Establish interfaces, types, schemas
- `ESTABLISH` - Set up configuration, constants

**Implementation Operations** (Add logic):
- `IMPLEMENT` - Fill in method/function body
- `INTEGRATE` - Connect components
- `EXTEND` - Add capabilities to existing code

**Modification Operations** (Change existing):
- `MODIFY` - Alter existing code behavior
- `REFACTOR` - Restructure without changing behavior
- `ENHANCE` - Add features to existing functionality

### S - Specification (The Contract)
Must include:
1. **Exact Signatures**: "Define method authenticate(email: str, password: str) -> Union[User, None]"
2. **Precise Types**: "Accept config: Dict[str, Union[str, int, bool]] with keys: 'timeout' (int), 'retry' (bool)"
3. **Explicit Contracts**: "Returns User object with populated 'id', 'email', 'role' fields on success, None on failure"
4. **Clear Dependencies**: "Imports: from src.models.user import User; from src.utils.crypto import hash_password"
5. **Exact Integration Points**: "Registers route POST /api/auth/login with AuthRouter instance from src/routes/auth.py"

### T - Test (The Proof)
Must be executable commands or verifiable conditions:
1. **Concrete Execution**: "Run: python -m pytest tests/test_auth.py::test_authenticate_valid -xvs"
2. **Specific Validation**: "Verify: curl -X POST http://localhost:8000/api/auth/login -d '{"email":"test@example.com","password":"123"}' returns 401"
3. **Integration Verification**: "Confirm: from src.auth.handler import authenticate; result = authenticate('test@example.com', 'password'); assert result is None"

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Review the approved design and break it down into atomic units of work
2. Order subtasks by dependency (interfaces before implementations)
3. For each subtask, create a LOST-formatted specification with:
   - Precise location (exact file path)
   - Specific operation verb
   - Detailed specification with all imports, signatures, types
   - Executable test commands
4. Ensure each subtask ends with: "Call alfred.mark_subtask_complete with task_id='${task_id}' and subtask_id='ST-X'"
5. Use subtask IDs in format: ST-1, ST-2, etc.

# CONSTRAINTS
- Each subtask must be executable in complete isolation
- No assumptions about context beyond what's explicitly stated
- All types, imports, and dependencies must be specified
- Tests must be runnable commands, not descriptions
- Avoid circular dependencies between subtasks

# OUTPUT
Create an ExecutionPlan artifact with an array of subtasks, each containing:
- `subtask_id`: Format "ST-X" 
- `title`: Precise description of atomic work
- `summary`: Optional extended description
- `location`: Exact file path
- `operation`: Specific verb from LOST framework
- `specification`: Array of precise implementation steps
- `test`: Array of executable verification commands

**Required Action:** Call `alfred.submit_work` with an `ExecutionPlan` artifact

# EXAMPLES

## ✅ GOOD Example - Define Interface First:
```json
{
  "subtask_id": "ST-1",
  "title": "Define IAuthService interface with method signatures",
  "location": "src/interfaces/auth.interface.ts",
  "operation": "CREATE",
  "specification": [
    "Create new file src/interfaces/auth.interface.ts",
    "Define TypeScript interface IAuthService with methods:",
    "- authenticate(email: string, password: string): Promise<AuthResult>",
    "- validateToken(token: string): Promise<TokenValidation>",
    "Define type AuthResult = { success: boolean; user?: User; tokens?: AuthTokens; error?: string }",
    "Export all interfaces and types",
    "Call alfred.mark_subtask_complete with task_id='${task_id}' and subtask_id='ST-1'"
  ],
  "test": [
    "File src/interfaces/auth.interface.ts exists",
    "Run: npx tsc src/interfaces/auth.interface.ts --noEmit",
    "Verify interface has all methods with correct signatures"
  ]
}
```

## ❌ BAD Example - Vague and Interdependent:
```json
{
  "subtask_id": "subtask-1",
  "title": "Create user authentication",
  "location": "src/auth/",
  "operation": "CREATE",
  "specification": [
    "Create authentication system",
    "Add login and registration",
    "Handle tokens and sessions"
  ],
  "test": [
    "Test that users can log in"
  ]
}
```
Problems: Wrong ID format, vague location, multiple operations, no precise contracts