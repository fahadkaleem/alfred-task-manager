# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Execute tests and report the results in a structured format.

# BACKGROUND
Run the test suite to validate the implementation and capture the complete results. This includes unit tests, integration tests, and any manual validation required.

# INSTRUCTIONS
1. Execute the appropriate test command for this codebase
2. Capture the complete output including any error messages
3. Record the exact command used and exit code
4. Report all results in the required format

# CONSTRAINTS
- Use the standard test command for this project
- Capture the complete output, not just a summary
- Report actual exit codes (0 = success, non-zero = failure)

# OUTPUT
Create a TestResultArtifact with these exact fields:
- **command**: The exact test command that was executed
- **exit_code**: Integer exit code from test execution (0 = success)
- **output**: Complete text output from the test execution

**Required Action:** Call `alfred.submit_work` with a `TestResultArtifact`

# EXAMPLES
```json
{
  "command": "python -m pytest tests/",
  "exit_code": 0,
  "output": "===== test session starts =====\ncollected 15 items\n\ntests/test_auth.py ........\ntests/test_api.py .......\n\n===== 15 passed in 2.34s ====="
}
```

```json
{
  "command": "npm test",
  "exit_code": 1,
  "output": "FAIL src/components/Button.test.js\n  ✓ renders correctly (5ms)\n  ✗ handles click events (12ms)\n\n1 test failed, 1 test passed"
}
```