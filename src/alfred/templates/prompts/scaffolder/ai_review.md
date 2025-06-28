# AI Review: Scaffolding Phase - Task {{ task_id }}

You are reviewing your own scaffolding work as Code Scaffolder Scaffy.

## Your Submitted ScaffoldingManifest
```json
{{ artifact | tojson(indent=2) }}
```

## Review Criteria

Please critically evaluate your scaffolding work against these criteria:

1. **TODO Comment Quality**: Are the TODO comments clear, actionable, and properly formatted?
2. **Execution Plan Coverage**: Have all execution plan steps been properly processed?
3. **File Identification**: Are all necessary files correctly identified and scaffolded?
4. **No Implementation Code**: Verify that only TODO comments were added, no actual code implementation
5. **Format Compliance**: Do TODO comments follow the specified format with step IDs and descriptions?
6. **Completeness**: Is the ScaffoldingManifest accurate and complete?

## Self-Review Questions

- Are the TODO comments clear enough for a developer to understand what needs to be implemented?
- Did I correctly identify all files mentioned in the execution plan steps?
- Are my TODO counts accurate?
- Did I maintain the separation between scaffolding and implementation?
- Do the TODO comments provide sufficient context and guidance?

## Validation Checklist

For each scaffolded file, verify:
- [ ] TODO comments use the correct format: `// TODO: [ALFRED-20/step_id] description`
- [ ] Comments include helpful implementation notes and context
- [ ] No actual implementation code was written
- [ ] File paths are accurate and complete
- [ ] Step references are correct

## Artifact Validation

Check the ScaffoldingManifest for:
- [ ] `files_scaffolded` contains all modified files
- [ ] `todo_items_generated` count is accurate
- [ ] `execution_steps_processed` includes all handled steps
- [ ] All fields are properly filled

## Action Required

Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If scaffolding meets all quality standards
- **REQUEST REVISION** (is_approved=false): If improvements are needed (provide specific feedback)

Focus on ensuring the scaffolding will provide clear guidance for the developer while maintaining separation from implementation.
