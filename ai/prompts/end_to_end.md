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
1.  **Action:** Create a new task file at `.alfred/tasks/AL-DRY-RUN-01.md`.
2.  **Content:**
    ```markdown
    # TASK: AL-DRY-RUN-01
    
    ## Title
    Dry Run Validation Task
    
    ## Context
    This is a test task to validate the end-to-end workflow of the Alfred system in a simulated, dry-run mode.
    
    ## Implementation Details
    The AI agent executing this task must simulate all actions without performing any actual file I/O or git operations.
    
    ## Acceptance Criteria
    - The task successfully transitions through all workflow states from NEW to READY_FOR_FINALIZATION.
    - All tools (`start_task`, `plan_task`, `implement_task`, `review_task`, `test_task`) execute without error.
    - All required artifacts are generated and archived correctly.
    
    ## AC Verification
    - Inspect the `task_state.json` file after each `approve_and_advance` call to confirm the `task_status` has advanced correctly.
    - Inspect the `archive` directory to confirm artifacts are being saved.
    ```
3.  **Verification:** Confirm the file exists with the correct content.

### **Phase 3: The Workflow Loop**

#### **Step 3.1: Start Task**
1.  **Action:** Call `alfred.work_on_task(task_id="AL-DRY-RUN-01")`.
2.  **Verify:** The `next_prompt` must instruct you to call `start_task`.
3.  **Action:** Call `alfred.start_task(task_id="AL-DRY-RUN-01")`.
4.  **Verify:** The `next_prompt` should be for the `awaiting_acquisition` state. A new directory `.alfred/workspace/AL-DRY-RUN-01/` should exist.
5.  **Action:** `submit_work` with the `TaskAcquisitionArtifact`.
6.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
7.  **Verify:** `scratchpad.md` should contain a formatted "Task Acquisition" artifact. The tool's state should be `awaiting_git_setup`.
8.  **Action:** `submit_work` with the `GitStatusArtifact`.
9.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
10. **Verify:** `scratchpad.md` should now also contain a formatted "Git Status" artifact. The tool is now `verified`. The `next_prompt` must instruct you to call `approve_and_advance`.
11. **Action:** Call `alfred.approve_and_advance(task_id="AL-DRY-RUN-01")`.
12. **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"planning"`. `active_tool_state` must be `null`.
    - `.alfred/workspace/AL-DRY-RUN-01/archive/` must contain `01-start-task.md`.
    - `scratchpad.md` must be empty.

#### **Step 3.2: Plan Task**
1.  **Action:** Call `work_on_task` -> `plan_task`.
2.  **Action (Loop):** For each planning state (`contextualize`, `strategize`, `design`, `generate_subtasks`):
    - `submit_work` with a simple, valid artifact. Use the `ExecutionPlan` from our `TEST-006` example for the final step.
    - `approve_review` (AI) -> `approve_review` (Human).
3.  **Verify (Intermediate):** After each step, check that `scratchpad.md` has the new section appended.
4.  **Verify (Final):** The final `next_prompt` must instruct you to call `approve_and_advance`.
5.  **Action:** Call `alfred.approve_and_advance(task_id="AL-DRY-RUN-01")`.
6.  **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_development"`.
    - `archive/` must now contain `02-plan-task.md` and `planning_execution_plan.json`.
    - `scratchpad.md` must be empty.

#### **Step 3.3: Implement Task**
1.  **Action:** Call `work_on_task` -> `implement_task`.
2.  **Action:** For each `Subtask` in the `ExecutionPlan`, call `mark_subtask_complete`.
3.  **Verify (Intermediate):** After each call, the `ToolResponse` should show incrementing progress. `task_state.json`'s `context_store.completed_subtasks` should update.
4.  **Action:** After all subtasks are marked, `submit_work` with the `ImplementationManifestArtifact`.
5.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
6.  **Action:** `approve_and_advance`.
7.  **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_review"`.
    - `archive/` must now contain `03-implement-task.md` and `implement_task_final_artifact.json`.
    - `scratchpad.md` must be empty.

#### **Step 3.4: Review Task**
1.  **Action:** Call `work_on_task` -> `review_task`.
2.  **Action:** `submit_work` with the `ReviewArtifact` (`"approved": true`).
3.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
4.  **Action:** `approve_and_advance`.
5.  **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_testing"`.
    - `archive/` must now contain `04-review-task.md`.

#### **Step 3.5: Test Task**
1.  **Action:** Call `work_on_task` -> `test_task`.
2.  **Action:** `submit_work` with the `TestResultArtifact` (`"exit_code": 0`).
3.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
4.  **Action:** `approve_and_advance`.
5.  **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_finalization"`.
    - `archive/` must now contain `05-test-task.md`.

### **Phase 4: Final Validation**
- At this point, the task `AL-DRY-RUN-01` has successfully traversed the entire workflow.
- Report success and the final state of the `task_state.json`.
```

## Acceptance Criteria
- A new file `TESTING_PROTOCOL.md` exists in the project root.
- The file contains the complete, detailed, step-by-step instructions as specified above.

## AC Verification
1.  **Code Review:** Manually review the generated `TESTING_PROTOCOL.md` file against this task's specification to ensure all details, verification steps, and failure handling instructions are present.