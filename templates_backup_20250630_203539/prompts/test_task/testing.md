# Testing Phase

You are now in the testing phase for task {{ task.task_id }}.

## Test Objectives

Run tests to validate the implementation. This includes:
- Unit tests
- Integration tests
- Any manual validation required

## Test Results

Create a `TestResultArtifact` with:
- **test_summary**: Overall test results summary
- **tests_run**: List of test names/identifiers that were executed
- **test_results**: List of test result objects with:
  - `name`: Test name
  - `status`: "passed" or "failed"
  - `message`: Optional failure message

Call `submit_work` with your test results.