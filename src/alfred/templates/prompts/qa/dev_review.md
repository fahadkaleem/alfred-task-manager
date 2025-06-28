# Role: QA Engineer
# Task: {{ task_id }}

The automated tests have passed. The implementation appears to be working correctly.

## Test Results Summary
The submitted test results have been reviewed and verified.

## Developer Review
Please review the test execution results and ensure:
1. All critical paths have been tested
2. Edge cases have been considered
3. The implementation meets the acceptance criteria

## Required Action
To approve and hand off this task to the next stage, call:
```
approve_and_handoff(task_id="{{ task_id }}")
```

To request revisions, call:
```
provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="Your specific feedback here")
```
