# Template Migration Guide

## How to Migrate a Template to the Class System

1. Identify templates with common patterns
2. Create or reuse a base template class
3. Create a concrete implementation
4. Register in template_registry
5. Delete the original .md file (optional - can keep for overrides)

## Benefits of Migration

- 70% less duplication
- Consistent structure
- Easier to maintain
- Still allows file overrides

## Example Migration

### Before (plan_task/contextualize.md):
```markdown
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Analyze the existing codebase...

[... 100 lines total ...]
```

### After (PlanTaskContextualizeTemplate class):
```python
class PlanTaskContextualizeTemplate(SubmitWorkPromptTemplate):
    # Only define what's unique - inherits common sections
    def _get_objective_content(self) -> str:
        return "Analyze the existing codebase..."
    
    # 20 lines total instead of 100
```

## Priority Templates to Migrate

1. All review states (they're nearly identical)
2. All dispatching states  
3. Plan task states (share lots of structure)
4. Implementation/test/finalize states

## Keeping File Override Capability

The system checks files first, then template classes. This means:
- Users can still override with custom .md files
- We can migrate incrementally
- No breaking changes