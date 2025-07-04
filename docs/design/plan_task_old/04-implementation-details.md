# Implementation Details

## Code Organization

### Package Structure
```
src/alfred/
├── tools/              # Tool entry points
│   ├── plan_task.py   # Plan task implementation
│   ├── submit_work.py # Generic work submission
│   └── provide_review.py # Review processing
├── core/              # Core workflow components
│   ├── workflow.py    # Base classes and state machines
│   └── prompter.py    # Prompt generation engine
├── models/            # Data models
│   ├── schemas.py     # Core data types
│   ├── planning_artifacts.py # Plan task artifacts
│   └── state.py       # State persistence models
├── orchestration/     # Lifecycle management
│   ├── orchestrator.py # Tool instance manager
│   └── persona_loader.py # Persona configuration
├── lib/               # Utilities
│   ├── artifact_manager.py # Artifact rendering
│   ├── task_utils.py  # Task I/O operations
│   └── logger.py      # Logging utilities
└── state/             # State management
    ├── manager.py     # State persistence
    └── recovery.py    # Tool recovery logic
```

## Key Implementation Components

### 1. Plan Task Entry Point

```python
# src/alfred/tools/plan_task.py
async def plan_task_impl(task_id: str) -> ToolResponse:
    # Setup task-specific logging
    setup_task_logging(task_id)
    
    # Tool instance resolution hierarchy:
    # 1. Check memory (orchestrator.active_tools)
    # 2. Try disk recovery (ToolRecovery.recover_tool)
    # 3. Create new instance
    
    # Load persona configuration
    persona_config = load_persona(tool_instance.persona_name or "planning")
    
    # Generate state-appropriate prompt
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        persona_config=persona_config,
        additional_context=tool_instance.context_store
    )
```

### 2. Artifact Validation System

```python
# In PlanTaskTool.__init__
self.artifact_map = {
    PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
    PlanTaskState.STRATEGIZE: StrategyArtifact,
    PlanTaskState.DESIGN: DesignArtifact,
    PlanTaskState.GENERATE_SLOTS: ExecutionPlanArtifact,
}

# In submit_work_impl
artifact_model = active_tool.artifact_map.get(current_state)
if artifact_model:
    validated_artifact = artifact_model.model_validate(artifact)
```

### 3. Prompt Generation Engine

```python
# src/alfred/core/prompter.py
class Prompter:
    def generate_prompt(self, task, tool_name, state, persona_config, additional_context):
        # Template path resolution
        template_path = f"templates/prompts/{tool_name}/{state}.md"
        
        # Context assembly
        context = {
            "task": task,
            "persona": persona_config,
            **additional_context
        }
        
        # Jinja2 rendering
        return template.render(**context)
```

### 4. State Persistence

```python
# src/alfred/state/manager.py
class StateManager:
    def save_tool_state(self, task_id: str, tool: BaseWorkflowTool):
        state_data = {
            "tool_class": tool.__class__.__name__,
            "state": tool.state,
            "context_store": self._serialize_context(tool.context_store),
            "persona_name": tool.persona_name
        }
        
        state_file = self.get_state_file(task_id)
        state_file.write_text(json.dumps(state_data, indent=2))
```

## Critical Implementation Patterns

### 1. Atomic State Transitions

Both `submit_work` and `provide_review` follow this pattern:

```python
# Save original state
original_state = active_tool.state
original_context = active_tool.context_store.copy()

try:
    # Phase 1: Prepare (can fail safely)
    validated_artifact = validate(...)
    next_prompt = generate_prompt(...)
    
    # Phase 2: Commit (must be atomic)
    update_context_store()
    trigger_state_transition()
    persist_to_disk()
    
except Exception as e:
    # Rollback everything
    active_tool.state = original_state
    active_tool.context_store = original_context
    state_manager.save_tool_state(task_id, active_tool)
    raise
```

### 2. Context Store Evolution

The context store accumulates data through the workflow:

```python
# Helper for review states
def _get_previous_state(current_state: str) -> Optional[str]:
    state_map = {
        "review_context": "contextualize",
        "review_strategy": "strategize",
        "review_design": "design",
        "review_plan": "generate_slots"
    }
    return state_map.get(current_state)

# Reconstruct artifact_content for review states
if "review" in tool_instance.state:
    prev_state = _get_previous_state(tool_instance.state)
    artifact_key = f"{artifact_name}_artifact"
    if artifact_key in prompt_context:
        artifact_data = prompt_context[artifact_key]
        prompt_context["artifact_content"] = json.dumps(
            artifact_data.model_dump() if hasattr(artifact_data, 'model_dump') 
            else artifact_data, 
            indent=2
        )
```

### 3. Artifact Rendering

```python
# src/alfred/lib/artifact_manager.py
class ArtifactManager:
    def append_to_scratchpad(self, task_id, state_name, artifact, persona_config):
        # Find artifact-specific template
        template_name = self._get_template_name(state_name)
        template = self._load_template(f"artifacts/{template_name}.md")
        
        # Render with full context
        content = template.render(
            artifact=artifact,
            persona=persona_config,
            timestamp=datetime.now()
        )
        
        # Append to scratchpad
        scratchpad_path = self._get_scratchpad_path(task_id)
        with open(scratchpad_path, 'a') as f:
            f.write(content)
```

### 4. Operation Normalization

To handle case-insensitive operation values:

```python
# In submit_work_impl
if artifact_model.__name__ == 'ExecutionPlanArtifact' and 'slots' in artifact:
    for slot in artifact['slots']:
        if 'operation' in slot and isinstance(slot['operation'], str):
            slot['operation'] = slot['operation'].upper()
elif artifact_model.__name__ == 'DesignArtifact' and 'file_breakdown' in artifact:
    for file_change in artifact['file_breakdown']:
        if 'operation' in file_change and isinstance(file_change['operation'], str):
            file_change['operation'] = file_change['operation'].upper()
```

## Logging Architecture

### Task-Specific Logging

```python
# src/alfred/lib/logger.py
def setup_task_logging(task_id: str):
    log_dir = Path(".alfred/debug") / task_id
    log_dir.mkdir(parents=True, exist_ok=True)
    
    handler = FileHandler(log_dir / "alfred.log")
    handler.setFormatter(Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    logger = getLogger(f"alfred.{task_id}")
    logger.addHandler(handler)

def cleanup_task_logging(task_id: str):
    logger = getLogger(f"alfred.{task_id}")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
```

## Error Handling Strategies

### 1. Validation Errors
```python
except ValidationError as e:
    error_msg = (
        f"Artifact validation failed for state '{current_state}'. "
        f"The submitted artifact does not match the required structure.\n\n"
        f"Validation Errors:\n{e}"
    )
    return ToolResponse(status="error", message=error_msg)
```

### 2. State Transition Errors
```python
if not hasattr(active_tool, trigger):
    return ToolResponse(
        status="error",
        message=f"Invalid action: cannot trigger '{trigger}' from state '{active_tool.state}'"
    )
```

### 3. Recovery Errors
```python
try:
    tool_instance = ToolRecovery.recover_tool(task_id)
except Exception as e:
    logger.warning(f"Failed to recover tool for {task_id}: {e}")
    # Fall back to creating new instance
```

## Performance Considerations

### 1. Lazy Loading
- Personas loaded only when needed
- Templates loaded on demand
- Task data reloaded before use

### 2. Memory Management
- Context store cleared on completion
- Active tools removed from orchestrator
- Loggers cleaned up properly

### 3. File I/O Optimization
- State saved only after successful transitions
- Scratchpad opened in append mode
- JSON serialization with streaming

## Testing Approach

### 1. "Simulated Reality" Philosophy
- No mocking of file systems
- Test against real directory structures
- Use temporary isolated environments

### 2. Integration Testing
```python
# Example test pattern
def test_plan_task_full_workflow(alfred_test_project):
    # Create real task file
    task_file = alfred_test_project.tasks_dir / "TK-01.md"
    task_file.write_text(task_content)
    
    # Execute real workflow
    response = plan_task_impl("TK-01")
    
    # Verify real artifacts
    scratchpad = alfred_test_project.workspace_dir / "TK-01/scratchpad.md"
    assert scratchpad.exists()
```

## Security Considerations

1. **Path Validation**: All file paths validated
2. **Input Sanitization**: User inputs escaped in templates
3. **State Integrity**: Atomic transitions prevent corruption
4. **Audit Trail**: All actions logged with timestamps

## Future Optimization Opportunities

1. **Async I/O**: Convert file operations to async
2. **Caching**: Cache loaded personas and templates
3. **Streaming**: Stream large artifacts instead of loading
4. **Compression**: Compress state files for large contexts
5. **Indexing**: Index scratchpad for faster searches