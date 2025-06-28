# Jira Issue Creation Guidelines

## Overview

This document outlines the standard structure and best practices for creating Jira issues in our projects. Following these guidelines ensures consistency, clarity, and completeness in our issue tracking.

## Required Sections

Every Jira issue should contain the following sections:

### 1. Context

The Context section provides the background and rationale for the change. It should answer:
- What is the current functionality or situation?
- Why is this change needed?
- What problem are we solving?
- What is the desired outcome?

**Guidelines:**
- Keep it concise but comprehensive
- Focus on the "why" behind the change
- Include relevant background information
- Avoid technical implementation details here

**Example:**
```
Currently, our API returns all user data including sensitive fields when queried. This poses a security risk as it exposes unnecessary information to clients. We need to implement field filtering to allow clients to specify which fields they want to receive, reducing data exposure and improving API performance.
```

### 2. Implementation Details

This section provides high-level implementation guidance without diving into code specifics.

**Guidelines:**
- Use bullet points for clarity
- Describe the approach in plain language
- Include important technical considerations
- Mention any dependencies or prerequisites
- Note any potential challenges or risks

**Example:**
```
" Add query parameter support for field selection (e.g., ?fields=name,email)
" Implement a field filtering mechanism in the response serializer
" Create a whitelist of allowed fields for each endpoint
" Consider performance implications of dynamic field selection
" Ensure backward compatibility - all fields returned if no filter specified
" Add appropriate validation for invalid field names
```

### 3. Acceptance Criteria

Define clear, testable criteria that must be met for the issue to be considered complete.

**Guidelines:**
- Use "As a [role], I [want/can/should]..." format when appropriate
- Make each criterion specific and measurable
- Focus on behavior and outcomes, not implementation
- Cover both positive and negative scenarios

**Example:**
```
" As an API consumer, I can specify which fields to include in the response using a query parameter
" As an API consumer, I receive only the requested fields in the response body
" As a service, we validate field names and return an error for invalid fields
" As a service, we return all fields when no field filter is specified (backward compatibility)
" As a service, we maintain the same response time performance (±10%) with field filtering
```

### 4. AC Verification

Provide detailed steps to manually verify that all acceptance criteria are met.

**Guidelines:**
- Include setup steps if needed
- Provide exact commands, URLs, or actions
- Specify expected results for each step
- Include both happy path and error scenarios
- Make steps reproducible by any team member

**Example:**
```
1. **Setup**
   - Ensure test database is populated with sample users
   - Start the API server on localhost:8080

2. **Verify field filtering works**
   - Run: `curl -X GET "http://localhost:8080/api/users/123?fields=name,email"`
   - Verify: Response contains only 'name' and 'email' fields
   - Verify: Response does NOT contain 'password', 'address', or other fields

3. **Verify backward compatibility**
   - Run: `curl -X GET "http://localhost:8080/api/users/123"`
   - Verify: Response contains all user fields (same as before implementation)

4. **Verify invalid field handling**
   - Run: `curl -X GET "http://localhost:8080/api/users/123?fields=invalid_field"`
   - Verify: Response returns 400 Bad Request
   - Verify: Error message indicates "invalid_field" is not a valid field name

5. **Verify performance**
   - Run performance test: `ab -n 1000 -c 10 "http://localhost:8080/api/users/123?fields=name"`
   - Verify: Average response time is within 10% of baseline (without field filtering)
```

## Best Practices

1. **Be Specific**: Avoid vague statements. Instead of "improve performance", specify "reduce response time to under 200ms"

2. **Think Like a Tester**: When writing AC Verification, imagine you know nothing about the implementation

3. **Consider Edge Cases**: Include criteria and verification for error scenarios, empty states, and boundary conditions

4. **Keep It Maintainable**: Write in a way that the issue can be understood months later by someone unfamiliar with the current context

5. **Link Related Issues**: Reference related tickets, documentation, or design documents where appropriate

6. **Use Consistent Formatting**: Follow the structure and formatting shown in this guide for all issues

## Templates

Consider creating issue templates in Jira for common types of work:
- Feature Development
- Bug Fix
- Technical Debt
- Infrastructure Change
- API Endpoint

Each template should pre-populate the four required sections with appropriate prompts.
