# Discovery Planning Prompts and Artifacts

## Overview

The Discovery Planning system uses a simplified, turn-based approach with human-readable artifacts and a conversational style. This document details the prompt templates and artifact structures for each phase of the planning workflow.

## Core Design Principles

### 1. **Simplicity First**
- Simple JSON artifacts with clear fields
- Markdown for all human-readable content
- No nested complex structures
- Validation focuses on essentials only

### 2. **Turn-Based Storage**
- Each artifact is saved as an immutable turn
- No JSON-to-Markdown conversions needed
- Scratchpad is a generated view, not storage
- Full history preserved for debugging

### 3. **Conversational Style**
- Prompts encourage natural dialogue
- Multi-turn conversations supported
- Context preserved across interactions
- Human expertise captured naturally

## Prompt Templates

### Discovery Phase Prompt

**File**: `src/alfred/templates/prompts/plan_task/discovery.md`

**Purpose**: Guide AI to explore the codebase comprehensively

**Key Sections**:
```markdown
# INSTRUCTIONS
1. Use Glob/Grep/Read tools to explore relevant code
2. Document what you find in markdown
3. Note any questions you need answered
4. List files that need changes
5. Assess complexity (LOW/MEDIUM/HIGH)

# OUTPUT
Submit a simple artifact with:
- **findings**: Your discoveries in markdown format
- **questions**: List of questions (must end with ?)
- **files_to_modify**: List of file paths
- **complexity**: LOW, MEDIUM, or HIGH
- **implementation_context**: Any code/patterns for later use
```

**Design Rationale**:
- Encourages parallel tool usage for efficiency
- Markdown findings are human-readable without conversion
- Questions must end with "?" for validation
- Complexity assessment guides workflow adaptation
- Implementation context preserves discovered patterns

### Clarification Phase Prompt

**File**: `src/alfred/templates/prompts/plan_task/clarification.md`

**Purpose**: Enable natural conversation to resolve ambiguities

**Key Features**:
```markdown
# INSTRUCTIONS
1. Present each question with its full context from discovery
2. Have a natural, multi-turn conversation with the human
3. **IMPORTANT: Track your progress internally** - humans may answer only some questions at a time:
   - Keep a mental list of which questions have been answered
   - Which questions remain unanswered
   - If human skips questions or only partially answers, acknowledge what you learned and continue asking the remaining questions
   - Do NOT submit work until ALL questions are resolved
```

**Design Innovation**:
- Supports partial answers and follow-ups
- AI tracks conversation state internally
- Natural dialogue flow, not rigid Q&A
- Captures domain knowledge through conversation

### Contracts Phase Prompt

**File**: `src/alfred/templates/prompts/plan_task/contracts.md`

**Purpose**: Design interfaces before implementation

**Structure**:
```markdown
# OUTPUT
Submit artifact with:
- **interface_design**: Markdown-formatted specifications
- **contracts_defined**: List of main contracts/interfaces
- **design_notes**: Important decisions or notes
```

**Simplification**:
- Single markdown field for all interface designs
- List of contract names for quick reference
- Design notes capture key decisions
- No complex nested structures

### Implementation Plan Prompt

**File**: `src/alfred/templates/prompts/plan_task/implementation_plan.md`

**Purpose**: Create detailed implementation steps with subtasks

**Key Output**:
```markdown
# OUTPUT
- **implementation_plan**: Markdown-formatted steps
- **subtasks**: List of structured subtasks with IDs
- **risks**: Potential risks or concerns
```

**Subtask Structure**:
- Simple ID + description format
- Self-contained context in plan markdown
- No complex dependency tracking
- Future extensibility preserved

### Validation Phase Prompt

**File**: `src/alfred/templates/prompts/plan_task/validation.md`

**Purpose**: Final coherence check

**Validation Output**:
```markdown
# OUTPUT
- **validation_summary**: Markdown results
- **validations_performed**: Checklist of validations
- **issues_found**: List of concerns
- **ready_for_implementation**: Boolean flag
```

## Artifact Models

### ContextDiscoveryArtifact

**File**: `src/alfred/models/planning_artifacts.py`

```python
class ContextDiscoveryArtifact(BaseModel):
    """Simplified discovery artifact focusing on essentials."""
    
    # What we found (markdown formatted for readability)
    findings: str = Field(
        description="Markdown-formatted discovery findings"
    )
    
    # Questions that need answers
    questions: List[str] = Field(
        description="Simple list of questions for clarification",
        default_factory=list
    )
    
    # Files that will be touched
    files_to_modify: List[str] = Field(
        description="List of files that need changes",
        default_factory=list
    )
    
    # Complexity assessment
    complexity: ComplexityLevel = Field(
        description="Overall complexity: LOW, MEDIUM, or HIGH",
        default=ComplexityLevel.MEDIUM
    )
    
    # Context bundle for implementation (free-form)
    implementation_context: Dict[str, Any] = Field(
        description="Any context needed for implementation",
        default_factory=dict
    )
```

**Design Choices**:
- `findings` in markdown eliminates conversion needs
- Simple string list for questions (validated to end with "?")
- Free-form dict for implementation context
- Enum for complexity ensures consistency

### ClarificationArtifact

```python
class ClarificationArtifact(BaseModel):
    """Simplified clarification results."""
    
    # Q&A in markdown format
    clarification_dialogue: str = Field(
        description="Markdown-formatted Q&A dialogue"
    )
    
    # Key decisions made
    decisions: List[str] = Field(
        description="List of decisions made during clarification",
        default_factory=list
    )
    
    # Any new constraints discovered
    additional_constraints: List[str] = Field(
        description="New constraints or requirements discovered",
        default_factory=list
    )
```

**Conversation Capture**:
- Full dialogue preserved in markdown
- Key decisions extracted as a list
- New constraints documented separately
- No complex conversation tree structure

### ContractDesignArtifact

```python
class ContractDesignArtifact(BaseModel):
    """Simplified contracts/interface design."""
    
    # Interface design in markdown
    interface_design: str = Field(
        description="Markdown-formatted interface specifications"
    )
    
    # Key APIs/contracts defined
    contracts_defined: List[str] = Field(
        description="List of main contracts/interfaces defined",
        default_factory=list
    )
    
    # Any additional notes
    design_notes: List[str] = Field(
        description="Important design decisions or notes",
        default_factory=list
    )
```

**Flexibility**:
- Single markdown field for all designs
- List of contract names for indexing
- Design notes capture rationale
- No rigid schema for interfaces

### ImplementationPlanArtifact

```python
class ImplementationPlanArtifact(BaseModel):
    """Implementation plan with structured subtasks."""
    
    # Implementation plan in markdown
    implementation_plan: str = Field(
        description="Markdown-formatted implementation steps"
    )
    
    # List of structured subtasks
    subtasks: List[Subtask] = Field(
        description="List of structured subtasks with IDs",
        default_factory=list
    )
    
    # Any risks or concerns
    risks: List[str] = Field(
        description="Potential risks or concerns",
        default_factory=list
    )
```

### Subtask Model

```python
class Subtask(BaseModel):
    """Structured subtask with ID and description."""
    
    subtask_id: str = Field(
        ..., 
        description="Unique identifier for the subtask (e.g., 'subtask-1')"
    )
    description: str = Field(
        ..., 
        description="Clear, actionable description of what needs to be done"
    )
    # Future extensibility: status, dependencies, estimated_hours, etc.
```

**Extensibility**:
- Minimal required fields
- Room for future enhancements
- Compatible with existing implementation flow
- Self-contained context in plan markdown

### ValidationArtifact

```python
class ValidationArtifact(BaseModel):
    """Simplified validation results."""
    
    # Validation summary in markdown
    validation_summary: str = Field(
        description="Markdown-formatted validation results"
    )
    
    # Checklist of validations performed
    validations_performed: List[str] = Field(
        description="List of validations performed",
        default_factory=list
    )
    
    # Any issues found
    issues_found: List[str] = Field(
        description="List of issues or concerns found",
        default_factory=list
    )
    
    # Ready for implementation?
    ready_for_implementation: bool = Field(
        description="Whether the plan is ready for implementation",
        default=True
    )
```

## Turn-Based Storage System

### How Artifacts are Stored

```python
# When submitting work
artifact_manager.record_artifact(
    task_id=task.task_id,
    state_name=current_state_val,
    tool_name=tool_name,
    artifact_data=validated_artifact,
    revision_of=revision_of  # If this is a revision
)
```

### Turn Structure

```python
class Turn(BaseModel):
    """Represents a single turn in the task history."""
    turn_number: int
    state_name: str
    tool_name: str
    timestamp: datetime
    artifact_data: Dict[str, Any]
    revision_of: Optional[int]
    revision_feedback: Optional[str]
```

### Storage Benefits

1. **Immutable History**: Every artifact version preserved
2. **No Data Loss**: Original JSON saved exactly
3. **Efficient Queries**: Manifest provides quick lookups
4. **Revision Tracking**: Clear lineage of changes
5. **Tool Agnostic**: Works with any workflow

## Scratchpad Generation

### Current State View

The scratchpad is now a **view**, not storage:

```python
def generate_scratchpad(self, task_id: str):
    """Generates a human-readable scratchpad showing ONLY the current state."""
    
    # Get latest artifacts by state
    latest_artifacts = turn_manager.get_latest_artifacts_by_state(task_id)
    
    # Determine current phase
    current_phase = self._determine_current_phase(task, current_state)
    
    # Build clean, current view
    content_parts = [
        f"# Task: {task_id}",
        f"**Current Phase:** {current_phase}",
        # ... phase-specific content
    ]
```

### Phase-Specific Rendering

```python
if current_phase == "Planning":
    # Show planning artifacts in order
    planning_states = ["discovery", "clarification", "contracts", 
                      "implementation_plan", "validation"]
    for state in planning_states:
        if state in latest_artifacts:
            self._add_planning_artifact(content_parts, state, 
                                      latest_artifacts[state])
```

## Best Practices

### 1. **Artifact Design**
- Keep fields simple and flat
- Use markdown for all human-readable content
- Validate only essential constraints
- Allow flexibility for edge cases

### 2. **Prompt Design**
- Guide without constraining
- Support multi-turn interactions
- Provide clear examples
- Explain the "why" behind instructions

### 3. **Context Preservation**
- Save discovered patterns in implementation_context
- Capture full conversations in clarification
- Document all decisions and rationale
- Enable re-planning with preserved work

### 4. **Error Handling**
- Validate questions end with "?"
- Ensure findings are not empty
- Check complexity is valid enum value
- Handle partial conversation responses

## Migration Guide

### From Old System to New

1. **Artifact Storage**:
   - Old: JSON → Markdown conversion in scratchpad
   - New: Direct JSON storage as turns

2. **Scratchpad Role**:
   - Old: Primary storage mechanism
   - New: Generated view of current state

3. **Artifact Structure**:
   - Old: Complex nested models
   - New: Simple flat structures with markdown

4. **Conversation Handling**:
   - Old: Rigid Q&A format
   - New: Natural multi-turn dialogue

## Future Enhancements

### 1. **Rich Media Support**
- Embed diagrams in markdown fields
- Link to external documentation
- Include code snippets with syntax highlighting

### 2. **Collaborative Features**
- Multiple participants in clarification
- Async conversation support
- Vote on design decisions

### 3. **Intelligence Features**
- Auto-suggest questions from patterns
- Predict complexity from discovery
- Recommend design patterns

### 4. **Integration Points**
- Export to project management tools
- Generate documentation from artifacts
- Create test cases from contracts

The simplified artifact system makes Discovery Planning more approachable while maintaining the power and flexibility needed for complex software development tasks.