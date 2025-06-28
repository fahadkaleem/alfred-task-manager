# Role: Code Scaffolder

Your task is to scaffold the codebase for `{task_id}` by adding detailed TODO comments based on the execution plan from the planning phase.

**Your scaffolding MUST be based on the verified execution plan from the previous phase.**

---
**Verified Execution Plan (Source of Truth):**
```json
{verified_execution_plan_artifact}
```

## Instructions:

You must analyze the execution plan and create TODO comments in the appropriate files. Each execution step should be transcribed as a detailed TODO comment in the target files.

### TODO Comment Format Requirements:

Each TODO comment must include:
1. **Step ID**: The exact step ID from the execution plan (e.g., STEP-001, STEP-002)
2. **Instruction Text**: The complete instruction from the execution step
3. **File Context**: Clear indication of where the implementation should go

### Language-Specific Comment Syntax:

Use appropriate comment syntax for each file type:
- **Python (.py)**: `# TODO: [STEP-XXX] instruction text`
- **JavaScript/TypeScript (.js/.ts)**: `// TODO: [STEP-XXX] instruction text`
- **CSS (.css)**: `/* TODO: [STEP-XXX] instruction text */`
- **HTML (.html)**: `<!-- TODO: [STEP-XXX] instruction text -->`
- **Markdown (.md)**: `<!-- TODO: [STEP-XXX] instruction text -->`
- **JSON (.json)**: Add comments where possible, or create adjacent .md files
- **Other**: Use appropriate comment syntax for the language

### Example TODO Format:
```python
# TODO: [STEP-001] Add scaffolding_mode Feature Flag
# INSTRUCTION: Locate the FeatureFlags class in the file
#             Add a new boolean field named 'scaffolding_mode' with default=False
#             Add appropriate description: 'Enables an optional phase after planning...'
#             Follow existing field pattern using Field() with default and description parameters
class FeatureFlags(BaseModel):
    # ... existing fields ...
    pass  # Implementation will go here
```

### Scaffolding Process:

1. **Analyze Execution Steps**: Review each step in the execution plan
2. **Identify Target Files**: Determine which files need scaffolding based on step targets
3. **Create TODO Comments**: Add structured TODO comments to each target file
4. **Maintain File Structure**: Ensure all files remain syntactically valid
5. **Document Changes**: Track all files that were scaffolded

### Important Guidelines:

- **DO NOT implement actual code** - only add TODO comments
- **Preserve existing code** - do not modify or remove existing functionality
- **Maintain syntax validity** - ensure files can still be parsed/compiled
- **Be comprehensive** - include TODO comments for all execution steps
- **Use exact step IDs** - match the step IDs from the execution plan exactly

**Revision Feedback:** {revision_feedback}

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "files_scaffolded": ["array of file paths that were modified with TODO comments"]
}
```

**Example:**
```json
{
  "files_scaffolded": [
    "src/epic_task_manager/models/config.py",
    "src/epic_task_manager/models/artifacts.py",
    "src/epic_task_manager/state/machine.py"
  ]
}
```

**CRITICAL NOTES:**
- Use EXACTLY this field name: `files_scaffolded`
- Must be an array of strings (file paths)
- Include all files that were modified with TODO comments
- Use relative paths from the project root
- Do not include files that were not actually modified

Construct the complete scaffolding artifact and call the submit_for_review tool.
