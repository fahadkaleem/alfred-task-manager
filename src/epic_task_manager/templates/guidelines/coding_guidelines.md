# Coding Guidelines

## 1. General Principles
- **Clarity is Paramount:** Write code that is easy to read and understand.
- **DRY (Don't Repeat Yourself):** Avoid duplicating code. Use functions and classes to promote reusability.
- **YAGNI (You Aren't Gonna Need It):** Do not add functionality that has not been explicitly requested.

## 2. Python-Specific Standards
- **Docstrings:** All modules, classes, and functions must have Google-style docstrings.
  ```python
  def my_function(param1: int) -> str:
      """This is a summary line.
      
      This is the extended description.
      
      Args:
          param1: The first parameter.
          
      Returns:
          A string describing the result.
      """
  ```
- **Type Hinting:** All function signatures and variable declarations must include type hints.
- **Error Handling:** Use specific exception types. Do not use broad `except Exception:`.
- **Imports:** Imports should be ordered: 1. Standard library, 2. Third-party, 3. Local application.