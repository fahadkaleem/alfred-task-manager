# Role: QA Engineer
# Task: {{ task_id }}

It is time to perform quality assurance testing.

## Instructions:
1.  Run the project's main test suite. For this simulation, you don't need to run a real command.
2.  Instead, you will **fabricate a test result**. You can choose to make it pass or fail.
3.  Submit a structured artifact with the test results.

## Required Artifact Structure:
You **MUST** submit an artifact with the following JSON structure:
```json
{
  "test_results": {
    "command_run": "string - The test command you would have run (e.g., 'pytest -v').",
    "exit_code": "integer - The result of the test. Use 0 for success/pass, and 1 for failure.",
    "full_output": "string - A fabricated log of the test output."
  }
}
```
**Example (Passing):**
```json
{
  "test_results": {
    "command_run": "pytest -v",
    "exit_code": 0,
    "full_output": "10/10 tests passed."
  }
}
```
**Example (Failing):**
```json
{
  "test_results": {
    "command_run": "pytest -v",
    "exit_code": 1,
    "full_output": "Test failed: test_user_login(). AssertionError: False is not true."
  }
}
```

## Required Action:
Call the `submit_work` tool with your fabricated artifact.
