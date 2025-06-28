# Testing Guidelines

## 1. Unit Tests
- **Coverage:** Aim for high unit test coverage for any new code.
- **Isolation:** Unit tests must be isolated and not depend on external services like databases or APIs. Use mocks where appropriate.
- **Assertion Clarity:** Assertions should be specific. `assert foo == True` is better than `assert foo`.

## 2. Integration Tests
- When running the full test suite (`pytest`), the primary success indicator is the `exit_code`. An `exit_code` of `0` means success. Any other value indicates failure.
- The `full_output` should be reviewed for warnings or deprecation notices even if the tests pass.