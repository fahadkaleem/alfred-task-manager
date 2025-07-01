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
    - All tools (`plan_task`, `implement_task`, `review_task`, `test_task`) execute without error.
    - All required artifacts are generated and archived correctly.
    
    ## AC Verification
    - Inspect the `task_state.json` file after each `approve_and_advance` call to confirm the `task_status` has advanced correctly.
    - Inspect the `archive` directory to confirm artifacts are being saved.
    ```
3.  **Verification:** Confirm the file exists with the correct content.

### **Phase 3: The Workflow Loop**

#### **Step 3.1: Plan Task (Complete Workflow)**
1.  **Action:** Call `alfred.work_on_task(task_id="AL-DRY-RUN-01")`.
2.  **Verify:** The `next_prompt` must instruct you to call `plan_task`.
3.  **Action:** Call `alfred.plan_task(task_id="AL-DRY-RUN-01")`.
4.  **Action (Loop):** For each planning state (`contextualize`, `strategize`, `design`, `generate_subtasks`):
    - `submit_work` with a simple, valid artifact.
    - `approve_review` (AI) -> `approve_review` (Human).
    - Verify `scratchpad.md` updates correctly after each step.
5.  **Action:** Call `alfred.approve_and_advance(task_id="AL-DRY-RUN-01")`.
6.  **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_development"`.
    - `archive/` must contain `03-plan-task.md` and `planning_execution_plan.json`.
    - `scratchpad.md` must be empty.

#### **Step 3.2: Implement Task (Critical Bug Test)**
1.  **Action:** Call `work_on_task` -> `implement_task`.
2.  **CRITICAL TEST:** Verify that `implement_task` succeeds without template variable errors.
3.  **Expected:** Tool should return success with implementing state prompt showing execution plan.
4.  **Bug Test:** If tool fails with "Missing required variables for implementing.md: artifact_json", the fix in implement_task.py failed.
5.  **Action:** For each `Subtask` in the `ExecutionPlan`, call `mark_subtask_complete`.
6.  **Verify (Intermediate):** Progress tracking should work correctly.
7.  **Action:** `submit_work` with the `ImplementationManifestArtifact`.
8.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
9.  **Action:** `approve_and_advance`.
10. **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_review"`.
    - `archive/` must contain implementation artifacts.

#### **Step 3.3: Review Task**
1.  **Action:** Call `work_on_task` -> `review_task`.
2.  **Action:** `submit_work` with the `ReviewArtifact` (`"approved": true`).
3.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
4.  **Action:** `approve_and_advance`.
5.  **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_testing"`.

#### **Step 3.4: Test Task**
1.  **Action:** Call `work_on_task` -> `test_task`.
2.  **Action:** `submit_work` with the `TestResultArtifact` (`"exit_code": 0`).
3.  **Action:** `approve_review` (AI) -> `approve_review` (Human).
4.  **Action:** `approve_and_advance`.
5.  **Verify Final State:**
    - `task_state.json` -> `task_status` must be `"ready_for_finalization"`.

### **Phase 4: Final Validation**
- At this point, the task `AL-DRY-RUN-01` has successfully traversed the entire workflow.
- Report success and the final state of the `task_state.json`.

## 4. Key Bug Tests

### **Bug Test 1: Template Variable Error**
- **Location:** Step 3.2 (Implement Task)
- **Test:** Verify `implement_task` doesn't fail with "Missing required variables for implementing.md: artifact_json"
- **Fix Applied:** Changed `execution_plan` to `artifact_content` in implement_task.py

### **Bug Test 2: Progress Tracking**
- **Location:** Step 3.2 (Mark Subtask Complete)
- **Test:** Verify `mark_subtask_complete` can find subtasks in execution plan
- **Fix Applied:** Changed `execution_plan_artifact` to `artifact_content` in progress.py

## 5. Success Criteria

The test passes if:
1. All phases complete without errors
2. Task status progresses correctly through all states
3. Artifacts are properly archived at each phase
4. The specific template variable bug is resolved
5. Progress tracking works correctly

## 6. Known Issues Resolved

- **Issue AL-14-001**: Missing `artifact_json` template variable in `implementing.md`
- **Issue AL-14-002**: Inconsistent execution plan storage keys between tools 