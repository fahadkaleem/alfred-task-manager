# Precision Prompting Guide

## Quick Reference for AI Code Generation

### Core Principles

1. **Explicit Location** - Always specify WHERE code should live
   - `Target: src/interfaces/mcp/server.py`
   - `Target: tests/unit/test_health.py`

2. **Precise Technical Verbs** - Use verbs that carry architectural meaning
   - **Fundamental**: CREATE, UPDATE, ADD, MOVE, REPLACE, MIRROR
   - **Precise Operations**: IMPLEMENT, EXTEND, REFACTOR, OPTIMIZE, INTEGRATE, MIGRATE
   - **Modifiers**: ENSURE, ENFORCE, PRESERVE, EXPOSE, ENCAPSULATE, VALIDATE
   - **Patterns**: ORCHESTRATE, STREAM, BATCH, CACHE, THROTTLE, PIPELINE

3. **WHERE-WHAT-HOW Structure**
   - **WHERE**: Specific file/class/function location
   - **WHAT**: Precise technical verb/operation
   - **HOW**: Requirements, constraints, behavior details

4. **Define the Contract** - Focus on WHAT (interface) over HOW (implementation)
   - Complete type signatures: `def authenticate_user(self, email: str, password: str) -> User | None:`
   - Clear input/output expectations
   - Integration points and dependencies

5. **Explicit Error Handling**
   - VALIDATE input parameters
   - HANDLE edge cases
   - LOG failures appropriately
   - ENSURE graceful degradation

6. **Integration Points**
   - Name specific services/functions to integrate with
   - Specify libraries and their usage patterns
   - Define data flow between components

### Example Pattern

```
WHERE: services/auth_service.py
WHAT: IMPLEMENT AuthenticationService class
HOW:
  - IMPLEMENT authenticate_user(email: str, password: str) -> User | None:
    - VALIDATE email format
    - FETCH user from database
    - VERIFY password using bcrypt
    - LOG failed attempts
    - RETURN User or None
  - ENSURE thread-safe database access
  - INTEGRATE with existing User model
```

### Precision Prompt Template

```
TARGET: [file_path]
ACTION: [PRECISE_VERB]
REQUIREMENTS:
  - [Specific requirement with technical details]
  - [Integration points and dependencies]
  - [Error handling expectations]
  - [Performance constraints if any]
VALIDATION:
  - [How to verify implementation is correct]
  - [Test scenarios to consider]
```
