# TASK: AL-14

## Title
End-to-End System Validation Protocol

## Context
A comprehensive, repeatable validation protocol is required to ensure the stability and correctness of the Alfred system after major architectural changes. This task defines a detailed, step-by-step script for an AI agent to perform a complete end-to-end "dry run" of the workflow. The script includes explicit checkpoints for verifying the file system state (`.alfred` directory), `task_state.json`, `scratchpad.md`, and archived artifacts at each phase transition. It also includes a strict failure-handling protocol.

## Implementation Details

This task does not involve writing code. It involves creating the definitive validation document that will be used for all future end-to-end tests.

**File to Create:** `TESTING_PROTOCOL.md` (in the project root)

**Content:**

```markdown
# Alfred End-to-End Workflow Validation Protocol (Dry Run)

## 1. Objective
To perform a complete, end-to-end "dry run" validation of the Alfred task workflow, from project initialization to the final phase, without writing any actual code or modifying the Git repository.

## 2. Failure Handling Protocol
If any step fails (the `ToolResponse.status` is 'error' or the outcome does not match the "Expected State"), **HALT** the test immediately. Do not proceed. Your new objective is to provide a detailed failure report including:
- The step number that failed.
- The full `ToolResponse` object received from the failing command.
- The contents of `.alfred/debug/{task_id}/alfred.log`.
- The contents of `.alfred/debug/{task_id}/transactions.jsonl`.
- The final state of `.alfred/workspace/{task_id}/task_state.json`.
- A summary of the discrepancy between the expected and actual outcomes.
Await further instructions after reporting the failure.

---
## 3. Test Execution Steps

### **Phase 0: Environment Cleanup**
1.  **Action:** Execute the command `rm -rf .alfred`.
2.  **Verification:** Confirm the command completed successfully and the `.alfred` directory does not exist.

### **Phase 1: Project Initialization**
1.  **Action:** Call `alfred.initialize_project(provider="local")`.
2.  **Verification:**
    - The tool call must succeed (`status: "success"`).
    - The `.alfred/` directory must now exist.
    - The directory must contain `config.json` and `tasks/`.

### **Phase 2: Task Creation**
1.  **Action:** Call `alfred.create_task(task_content="...")` with proper task template format:
    ```markdown
    # TASK: AL-DRY-RUN-01
    
    ## Title
    Dry Run Validation Task
    
    ## Context
    This is a test task to validate the end-to-end workflow of the Alfred system in a simulated, dry-run mode.
    
    ## Implementation Details
    The AI agent executing this task must simulate all actions without performing any actual file I/O or git operations.
    
    ## Acceptance Criteria
    - The task successfully transitions through all workflow states from NEW to COMPLETED
    - All tools (plan_task, implement_task, review_task, test_task, finalize_task) execute without error
    - All required artifacts are generated and archived correctly
    - Scratchpad formatting is clean and professional
    
    ## AC Verification
    - Inspect the `scratchpad.md` file after each phase to confirm proper formatting
    - Verify all subtasks are properly displayed with clean section headers
    - Confirm validation logic prevents incomplete implementations
    ```
2.  **Verification:** 
    - Tool must succeed and return task_id (e.g., "TS-01")
    - File `.alfred/tasks/{task_id}.md` must exist with correct content

### **Phase 3: The Workflow Loop**

#### **Step 3.1: Task Routing**
1.  **Action:** Call `alfred.work_on_task(task_id="{task_id}")`.
2.  **Verify:** The response should indicate the task is NEW and route to planning.
3.  **Expected:** Next action should be to call `plan_task`.

#### **Step 3.2: Plan Task (5-Phase Discovery Planning)**
1.  **Action:** Call `alfred.plan_task(task_id="{task_id}")`.
2.  **Verify:** Tool creates planning workflow and enters "discovery" state.

##### **Discovery Phase**
3.  **Action:** `submit_work` with discovery artifact:
    ```json
    {
      "findings": "## Discovery Results\n\n### Current State\n- Test task for validation\n- Simple implementation needed\n\n### Patterns Found\n- Standard validation patterns available",
      "questions": ["Should we create 2 or 3 subtasks?", "What validation scenarios to test?"],
      "files_to_modify": ["src/alfred/validation_utils.py", "tests/test_validation.py"],
      "complexity": "LOW",
      "implementation_context": {"pattern": "Simple utility validation"}
    }
    ```
4.  **Action:** `approve_review` (AI self-review) → `approve_review` (Human review).
5.  **Verify:** Scratchpad shows formatted discovery section.

##### **Clarification Phase**
6.  **Action:** `submit_work` with clarification artifact:
    ```json
    {
      "clarification_dialogue": "## Clarification Discussion\n\n**AI**: Need clarification on validation requirements:\n1. Should we create 2 or 3 subtasks?\n2. What validation scenarios to test?\n\n**Human**: Create 3 subtasks for thorough testing. Focus on edge case validation.\n\n**AI**: Perfect! Clear requirements established.",
      "decisions": ["Create 3 subtasks for testing", "Focus on edge case validation", "Keep implementation simple"],
      "additional_constraints": ["Maintain backward compatibility", "Follow existing patterns"]
    }
    ```
7.  **Action:** `approve_review` (AI) → `approve_review` (Human).
8.  **Verify:** Scratchpad shows clarification section.

##### **Contracts Phase**
9.  **Action:** `submit_work` with contracts artifact:
    ```json
    {
      "interface_design": "## Interface Design\n\n### ValidationUtils Class\n```python\nclass ValidationUtils:\n    def validate_input(data: Dict) -> bool\n    def check_constraints(item: Any) -> ValidationResult\n```",
      "contracts_defined": ["ValidationUtils class interface", "ValidationResult data model", "Input validation methods"],
      "design_notes": ["Keep interfaces simple", "Return clear validation results"]
    }
    ```
10. **Action:** `approve_review` (AI) → `approve_review` (Human).
11. **Verify:** Scratchpad shows contracts section.

##### **Implementation Plan Phase**  
12. **Action:** `submit_work` with implementation plan artifact containing **properly formatted subtasks**:
    ```json
    {
      "implementation_plan": "## Implementation Plan\n\n### Overview\nCreate validation utilities in three phases:\n1. Core validation class\n2. Input validation methods\n3. Constraint checking logic",
      "subtasks": [
        {
          "subtask_id": "ST-001",
          "description": "**Goal**: Create ValidationUtils core class\n\n**Location**: `src/alfred/validation_utils.py` → `ValidationUtils` class\n\n**Approach**:\n- Create class with validation methods\n- Follow existing utility patterns\n- Per decision: \"Keep implementation simple\" [CLARIFICATION]\n\n**Verify**: Class loads and methods are callable"
        },
        {
          "subtask_id": "ST-002", 
          "description": "**Goal**: Implement input validation methods\n\n**Location**: `src/alfred/validation_utils.py` → validation methods\n\n**Approach**:\n- Add validate_input method\n- Handle edge cases properly\n- Return clear validation results\n\n**Verify**: Input validation works with valid/invalid data"
        },
        {
          "subtask_id": "ST-003",
          "description": "**Goal**: Add constraint checking logic\n\n**Location**: `src/alfred/validation_utils.py` → constraint methods\n\n**Approach**:\n- Implement check_constraints method\n- Support multiple constraint types\n- Per decision: \"Focus on edge case validation\" [CLARIFICATION]\n\n**Verify**: Constraint checking handles all edge cases"
        }
      ],
      "risks": ["Edge case handling complexity", "Backward compatibility requirements"]
    }
    ```
13. **Action:** `approve_review` (AI) → `approve_review` (Human).
14. **Verify:** **CRITICAL FORMATTING CHECK** - Scratchpad must show:
    ```markdown
    ## Subtasks
    
    ### ST-001 - Create ValidationUtils core class
    
    **Goal**: Create ValidationUtils core class
    
    **Location**: `src/alfred/validation_utils.py` → `ValidationUtils` class
    ```
    - **NO** messy `- [ST-001] ## ST-001` format
    - **YES** clean `### ST-001 - Title` section headers

##### **Validation Phase**
15. **Action:** `submit_work` with validation artifact:
    ```json
    {
      "validation_summary": "## Validation Complete\n\nThe plan is comprehensive and ready:\n- All 3 subtasks are well-defined\n- Interfaces are consistent\n- Edge case handling addressed\n- Implementation follows project patterns",
      "validations_performed": ["Checked all subtasks cover requirements", "Verified interface consistency", "Validated edge case coverage"],
      "issues_found": [],
      "ready_for_implementation": true
    }
    ```
16. **Action:** `approve_review` (AI) → `approve_review` (Human).
17. **Action:** `approve_and_advance`.
18. **Verify Final State:**
    - Task status must be `"ready_for_development"`
    - Scratchpad should be cleared
    - Archive should contain planning artifacts

#### **Step 3.3: Implement Task**
1.  **Action:** Call `alfred.work_on_task(task_id="{task_id}")` → routes to `implement_task`.
2.  **Action:** Call `alfred.implement_task(task_id="{task_id}")`.
3.  **Verify:** Implementation workflow starts, shows subtasks and progress.

##### **Mark Subtasks Complete**
4.  **Action:** For each subtask: `alfred.mark_subtask_complete(task_id="{task_id}", subtask_id="ST-001")`.
5.  **Verify:** Progress updates correctly (e.g., "1/3 subtasks complete (33%)").
6.  **Verify:** Task status has been updated from `"ready_for_development"` to `"in_development"`.
7.  **Action:** Mark remaining subtasks complete: "ST-002", "ST-003".

##### **Submit Implementation**
8.  **Action:** Try submitting **incomplete** implementation to test validation:
    ```json
    {
      "summary": "Partial implementation completed",
      "completed_subtasks": ["ST-001", "ST-002"],
      "testing_notes": "Only completed first two subtasks"
    }
    ```
9.  **Verify:** **VALIDATION SHOULD FAIL** with clear error:
    ```
    "Implementation validation failed: Implementation incomplete. 
    Missing subtasks: ['ST-003']. Expected all subtasks to be completed."
    ```

10. **Action:** Submit **complete** implementation:
    ```json
    {
      "summary": "All validation utilities implemented successfully",
      "completed_subtasks": ["ST-001", "ST-002", "ST-003"],
      "testing_notes": "All subtasks completed. Validation logic working correctly.",
      "implementation_details": "Created ValidationUtils class with all required methods"
    }
    ```
11. **Action:** `approve_review` (AI) → `approve_review` (Human).
12. **Action:** Either call `approve_and_advance` or complete the workflow with `work_on_task`.
13. **Verify Final State:**
    - Task status must be `"ready_for_review"`
    - Scratchpad cleared
    - Archive contains implementation artifacts

#### **Step 3.4: Review Task**
1.  **Action:** Call `alfred.work_on_task(task_id="{task_id}")` → routes to `review_task`.
2.  **Action:** Call `alfred.review_task(task_id="{task_id}")`.
3.  **Action:** Submit review findings:
    ```json
    {
      "review_summary": "Code review completed successfully",
      "functionality_review": {"complete": true, "meets_requirements": true},
      "code_quality_review": {"follows_patterns": true, "proper_error_handling": true},
      "test_coverage_review": {"adequate_coverage": true, "edge_cases_tested": true},
      "security_review": {"no_vulnerabilities": true},
      "issues_found": [],
      "approval_status": "approved"
    }
    ```
4.  **Action:** `approve_review` (AI) → `approve_review` (Human).
5.  **Action:** `approve_and_advance`.
6.  **Verify Final State:**
    - Task status must be `"ready_for_testing"`

#### **Step 3.5: Test Task**
1.  **Action:** Call `alfred.work_on_task(task_id="{task_id}")` → routes to `test_task`.
2.  **Action:** Call `alfred.test_task(task_id="{task_id}")`.
3.  **Action:** Submit test results:
    ```json
    {
      "test_summary": "All tests passing successfully",
      "unit_tests": {"passed": 15, "failed": 0, "coverage": "95%"},
      "integration_tests": {"passed": 8, "failed": 0},
      "manual_tests": ["Validation logic works correctly", "Edge cases handled properly"],
      "issues_found": [],
      "overall_status": "passed"
    }
    ```
4.  **Action:** `approve_review` (AI) → `approve_review` (Human).
5.  **Action:** `approve_and_advance`.
6.  **Verify Final State:**
    - Task status must be `"ready_for_finalization"`

#### **Step 3.6: Finalize Task**
1.  **Action:** Call `alfred.work_on_task(task_id="{task_id}")` → routes to `finalize_task`.
2.  **Action:** Call `alfred.finalize_task(task_id="{task_id}")`.
3.  **Verify:** Task creates commit and pull request (simulated).
4.  **Verify Final State:**
    - Task status must be `"completed"`
    - All artifacts archived properly

### **Phase 4: Error Message Testing**
Test improved error messages by trying to mark subtasks complete after workflow completion:

1.  **Action:** Try `alfred.mark_subtask_complete(task_id="{task_id}", subtask_id="ST-001")`.
2.  **Verify:** Should receive **helpful error message**:
    ```
    No active implementation workflow found for task '{task_id}'. 

    **Current Status**: completed

    **Possible Reasons**:
    - Implementation phase has already completed
    - Task is in a different phase (planning, review, testing, etc.)

    **What to do**:
    - Task is already complete - no further action needed
    - To see current status: Use `alfred.work_on_task('{task_id}')`
    ```

### **Phase 5: Final Validation**
- **Scratchpad Formatting:** Verify clean formatting throughout:
  - ✅ Section headers use `### ST-001 - Title` format
  - ✅ No messy `- [ST-001] ## ST-001` mixing
  - ✅ Professional, readable layout
- **Validation Logic:** Confirmed prevents incomplete implementations
- **Error Messages:** Clear, actionable feedback provided
- **Workflow Integrity:** All phases transition correctly
- **Artifact Archival:** All artifacts properly saved

### **Phase 6: Success Criteria**
✅ **Task Creation:** Template validation working  
✅ **Planning Phases:** All 5 discovery phases complete correctly  
✅ **Subtask Formatting:** Clean section headers, no redundant prefixes  
✅ **Implementation Validation:** Blocks incomplete submissions  
✅ **Error Messages:** Helpful, actionable feedback  
✅ **Workflow Transitions:** All phases advance correctly  
✅ **Final Completion:** Task reaches completed status  

Report success with final task state and any observations about system behavior.
```

## Acceptance Criteria
- A new file `TESTING_PROTOCOL.md` exists in the project root.
- The file contains the complete, detailed, step-by-step instructions as specified above.
- The protocol reflects the current Alfred workflow structure including:
  - 5-phase discovery planning (discovery, clarification, contracts, implementation_plan, validation)
  - Proper artifact types for each phase  
  - AI and human review processes
  - Clean subtask formatting verification
  - Implementation validation logic testing
  - Improved error message verification

## AC Verification
1.  **Code Review:** Manually review the generated `TESTING_PROTOCOL.md` file against this task's specification to ensure all details, verification steps, and failure handling instructions are present.
2.  **Workflow Accuracy:** Verify the protocol matches the actual Alfred workflow behavior as demonstrated in recent testing.
3.  **Formatting Validation:** Confirm the protocol includes specific checks for the improved subtask formatting.