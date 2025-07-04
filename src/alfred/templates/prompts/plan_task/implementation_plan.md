<!--
Template: plan_task.implementation_plan
Purpose: Create implementation plan
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - contracts_artifact: Results from contracts phase (if available)
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Create a detailed implementation plan with clear subtasks.

# BACKGROUND
We've explored the codebase, clarified requirements, and designed interfaces. Now create the implementation roadmap.

# INSTRUCTIONS

## For Simple Tasks (1-2 subtasks):
1. Break down the work into clear, self-contained subtasks
2. Write implementation steps in markdown overview
3. For each subtask, use structured description format (see below)
4. Identify any risks or concerns

## For Complex Tasks (3+ subtasks or HIGH complexity):
Use parallel sub-agents for deeper, more thorough specifications:

1. Create a high-level outline with subtask IDs and titles
2. For EACH subtask, call the Task tool in parallel (CRITICAL: You MUST launch ALL Task tools in a SINGLE message to achieve true parallelism - do NOT call them sequentially):
   ```
   Task(
     description="Create detailed spec for ST-001: [subtask title]",
     prompt='''You are a specialist focused on creating a complete specification for ONE subtask.

CONTEXT: Working on ST-001 - [subtask title]

CONTEXT FROM DISCOVERY:
[Include relevant discovery findings for this subtask]

KEY DECISIONS:
[Include relevant decisions from clarification]

YOUR MISSION: Create an exhaustive specification in this format:

**Goal**: [One line describing what to achieve]

**Location**: `path/to/file.py` → `ClassName` or `function_name`

**Methods to Implement**:
- [ ] `method_name(params) -> ReturnType`
- [ ] [List all methods with exact signatures]

**Dependencies**:
- [Other subtask dependencies]
- [External package dependencies]

**Implementation Steps**:
1. [Detailed step-by-step guide]
2. [Include specific patterns to follow]
3. [Reference decisions and discoveries]

**Testing Requirements**:
- File: `tests/path/to/test_file.py`
- [Specific test cases needed]
- [Mocks required]

**Verification**:
- [ ] [Checklist of completion criteria]
- [ ] [How to verify integration with other subtasks]
'''
   )
   ```
3. Execute all Task calls IN PARALLEL for maximum speed
4. Collect and validate all specifications
5. Submit the combined result as your artifact

This ensures each subtask gets focused, deep attention while maintaining speed through parallelism.

# OUTPUT
Submit a simple artifact with:
- **implementation_plan**: Markdown overview of the implementation approach
- **subtasks**: List of subtask objects with `subtask_id` and structured `description`
- **risks**: Potential risks or concerns

## Subtask Description Format
Each subtask description should use this structured markdown format:

```
**Goal**: One line describing what to achieve

**Location**: `path/to/file.py` → `ClassName` or `function_name`

**Approach**:
- Key implementation steps
- Reference patterns: "Follow pattern in `file.py:ClassName`"
- Reference decisions: "Per decision: use X approach [CLARIFICATION]"
- Reference discoveries: "Integration point: `file.py:method` [DISCOVERY]"

**Verify**: How to know it's done (test approach or verification steps)
```

Keep each subtask description concise (under 10 lines).
For 5+ subtasks, be increasingly brief.
Reference discoveries, decisions, and patterns rather than copying code.

## Example for Simple Task (1-2 subtasks)
```json
{
  "implementation_plan": "## Implementation Plan\n\n### Overview\nAdd task priority support in three phases:\n1. Extend Task model with priority field\n2. Update parser to handle Priority sections\n3. Integrate priority into task ranking algorithm\n\n### Key Decisions from Planning\n- Priority is optional with MEDIUM default\n- No migration needed for existing tasks\n- Priority ranks after status but before age",
  
  "subtasks": [
    {
      "subtask_id": "ST-001",
      "description": "**Goal**: Add priority field to Task model\n\n**Location**: `src/alfred/models/schemas.py` → `Task` class\n\n**Approach**:\n- Create TaskPriority enum (pattern: see TaskStatus in same file)\n- Add field: `priority: Optional[TaskPriority] = Field(default=TaskPriority.MEDIUM)`\n- Per decision: \"Priority optional with MEDIUM default\" [CLARIFICATION]\n\n**Verify**: Existing tasks load without error, new tasks get MEDIUM by default"
    },
    {
      "subtask_id": "ST-002", 
      "description": "**Goal**: Add Priority section parser\n\n**Location**: `src/alfred/lib/md_parser.py` → `parse_task` function\n\n**Approach**:\n- Add Priority section parsing after Status section\n- Map string values to TaskPriority enum\n- Handle missing section gracefully (return None)\n- Pattern: follow Status section parsing approach\n\n**Verify**: Can parse '## Priority\\nHIGH' correctly"
    },
    {
      "subtask_id": "ST-003",
      "description": "**Goal**: Update task ranking algorithm\n\n**Location**: `src/alfred/tools/get_next_task.py` → `_calculate_rank` function\n\n**Approach**:\n- Add priority to ranking tuple after status\n- Per decision: \"Priority ranks after in-progress but before ready\" [CLARIFICATION]\n- Integration: Use task.priority.value for numeric comparison\n\n**Verify**: HIGH priority tasks rank above MEDIUM when status equal"
    }
  ],
  
  "risks": [
    "Existing tasks need graceful handling when priority is None",
    "Parser must handle case variations (High, HIGH, high)"
  ]
}
```

## Example for Complex Task (3+ subtasks) using Parallel Sub-Agents

First, create the outline:
```json
{
  "subtask_outline": [
    {"subtask_id": "ST-001", "title": "Create User model and database schema"},
    {"subtask_id": "ST-002", "title": "Implement UserRepository"},
    {"subtask_id": "ST-003", "title": "Create AuthService with JWT"},
    {"subtask_id": "ST-004", "title": "Add authentication middleware"},
    {"subtask_id": "ST-005", "title": "Create login/logout endpoints"}
  ]
}
```

Then launch ALL Task tools IN ONE MESSAGE (for true parallelism):
```
Task(description="Create detailed spec for ST-001: Create User model and database schema", prompt="...")
Task(description="Create detailed spec for ST-002: Implement UserRepository", prompt="...")
Task(description="Create detailed spec for ST-003: Create AuthService with JWT", prompt="...")
Task(description="Create detailed spec for ST-004: Add authentication middleware", prompt="...")
Task(description="Create detailed spec for ST-005: Create login/logout endpoints", prompt="...")
```

After collecting all parallel results:
```json
{
  "implementation_plan": "## Implementation Plan\n\n### Overview\nImplement complete authentication system...",
  
  "subtasks": [
    {
      "subtask_id": "ST-001",
      "description": "[Detailed specification from sub-agent 1]"
    },
    {
      "subtask_id": "ST-002", 
      "description": "[Detailed specification from sub-agent 2]"
    },
    // ... all subtasks with detailed specs from parallel agents
  ],
  
  "risks": [
    "Token security requires careful key management",
    "Database migrations needed for existing users"
  ]
}
```

**Action**: Call `alfred.submit_work` with implementation plan