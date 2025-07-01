# Prompts and Artifacts

## Overview

The prompt and artifact system is the heart of Alfred's human-AI collaboration. This document details how prompts guide AI behavior and how artifacts capture structured outputs.

## Prompt System Architecture

### Template Organization
```
templates/prompts/plan_task/
├── contextualize.md      # Initial analysis
├── review_context.md     # Clarification dialogue
├── strategize.md        # Strategy formulation
├── review_strategy.md   # Strategy review
├── design.md           # Detailed design
├── review_design.md    # Design review
├── generate_slots.md   # SLOT generation
├── review_plan.md      # Final review
└── verified.md         # Completion message
```

### Prompt Structure

Each prompt follows a consistent structure:

```markdown
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: {{ current_state }}

[Contextual greeting or status update]

---
### **Persona Guidelines**
[Instructions for embodying the persona]

---
### **Task Context**
[Relevant task information]

---
### **Directive**
[Specific instructions for this state]

---
### **Required Action**
[Tool call specification with artifact structure]
```

## Persona Integration

### Persona Configuration
```yaml
# personas/planning.yml
name: "Alex"
title: "Senior Planning Architect"
greeting: "Hey there! Alex here, your planning architect"
communication_style: "Collaborative, detail-oriented, asks clarifying questions"
thinking_methodology: "Break down complex problems into manageable pieces"
```

### Dynamic Persona Injection
```jinja2
# In prompts
**Your Persona:** {{ persona.name }}, {{ persona.title }}.
**Communication Style:** {{ persona.communication_style }}

# Example rendering
**Your Persona:** Alex, Senior Planning Architect.
**Communication Style:** Collaborative, detail-oriented, asks clarifying questions
```

## State-Specific Prompts

### 1. CONTEXTUALIZE Prompt
**Purpose**: Guide initial codebase analysis

```markdown
### **Directive: Codebase Analysis & Ambiguity Detection**

Your mission is to become the expert on this task. You must:
1. **Analyze the existing codebase.**
2. **Identify Ambiguities.**

### **Required Action**
Call `alfred.submit_work` with a `ContextAnalysisArtifact`:
```json
{
  "context_summary": "string",
  "affected_files": ["string"],
  "questions_for_developer": ["string"]
}
```

### 2. REVIEW_CONTEXT Prompt
**Purpose**: Manage clarification dialogue

```markdown
### **Directive: Manage Clarification Dialogue**

1. **Maintain a checklist** of the questions below
2. **Present the unanswered questions**
3. **Receive their response**
4. **Check your list**
5. **Repeat until all questions are answered**

**My Questions Checklist:**
{% for question in artifact.questions_for_developer %}
- [ ] {{ question }}
{% endfor %}
```

### 3. STRATEGIZE Prompt
**Purpose**: Create technical strategy

```markdown
### **Available Context**
{% set context_artifact = context_store.context_artifact %}
{% if additional_context.feedback_notes %}
**Developer's Clarifications:**
{{ additional_context.feedback_notes }}
{% endif %}

### **Directive: Technical Strategy**
Based on the clarifications, create a comprehensive strategy
```

## Artifact Models

### 1. ContextAnalysisArtifact
```python
class ContextAnalysisArtifact(BaseModel):
    """Captures understanding of task context"""
    context_summary: str = Field(
        description="Summary of codebase understanding"
    )
    affected_files: List[str] = Field(
        description="Files relevant to the task"
    )
    questions_for_developer: List[str] = Field(
        description="Ambiguities requiring clarification"
    )
```

### 2. StrategyArtifact
```python
class StrategyArtifact(BaseModel):
    """High-level technical approach"""
    approach: str = Field(
        description="Overall technical strategy"
    )
    key_technical_decisions: List[str] = Field(
        description="Important design choices"
    )
    risk_factors: List[str] = Field(
        description="Potential challenges"
    )
```

### 3. DesignArtifact
```python
class FileChange(BaseModel):
    """Single file modification"""
    file_path: str
    operation: OperationType  # CREATE, MODIFY, DELETE, REVIEW
    summary: str

class DesignArtifact(BaseModel):
    """Detailed implementation design"""
    design_overview: str
    file_breakdown: List[FileChange]
    assumptions: List[str] = Field(default_factory=list)
```

### 4. ExecutionPlanArtifact
```python
class Taskflow(BaseModel):
    """Step-by-step procedures"""
    description: str
    steps: List[str]
    verification_steps: List[str]

class DelegationSpec(BaseModel):
    """Complex task delegation"""
    delegated_to: str
    sub_slots: List['SLOT']
    handoff_context: str

class SLOT(BaseModel):
    """Atomic work unit"""
    slot_id: str
    title: str
    spec: str
    location: str
    operation: OperationType
    taskflow: Taskflow
    delegation: Optional[DelegationSpec] = None

class ExecutionPlanArtifact(BaseModel):
    """Complete execution plan"""
    slots: List[SLOT]
    estimated_complexity: str = Field(
        description="Overall complexity assessment"
    )
```

## Artifact Rendering

### Template Organization
```
templates/artifacts/
├── context_analysis.md   # Context artifact display
├── strategy.md          # Strategy artifact display
├── design.md           # Design artifact display
└── execution_plan.md   # Execution plan display
```

### Example Artifact Template
```jinja2
{# execution_plan.md #}
## 🎯 Execution Plan Generated

**Generated by:** {{ persona.name }} ({{ persona.title }})
**Timestamp:** {{ timestamp }}

### Overview
- **Total SLOTs:** {{ artifact.slots | length }}
- **Estimated Complexity:** {{ artifact.estimated_complexity }}

### Execution Units

{% for slot in artifact.slots %}
#### SLOT {{ slot.slot_id }}: {{ slot.title }}
- **Location:** `{{ slot.location }}`
- **Operation:** {{ slot.operation }}
- **Specification:** {{ slot.spec }}

**Taskflow:**
{{ slot.taskflow.description }}

**Steps:**
{% for step in slot.taskflow.steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

{% if slot.delegation %}
**⚡ Delegated to:** {{ slot.delegation.delegated_to }}
**Handoff Context:** {{ slot.delegation.handoff_context }}
{% endif %}

---
{% endfor %}
```

## Context Flow Between States

### Context Accumulation Pattern
```python
# After CONTEXTUALIZE
context_store = {
    "context_artifact": ContextAnalysisArtifact(...)
}

# After STRATEGIZE  
context_store = {
    "context_artifact": ContextAnalysisArtifact(...),
    "feedback_notes": "Developer clarifications",
    "strategy_artifact": StrategyArtifact(...)
}

# After DESIGN
context_store = {
    "context_artifact": ContextAnalysisArtifact(...),
    "feedback_notes": "Developer clarifications", 
    "strategy_artifact": StrategyArtifact(...),
    "design_artifact": DesignArtifact(...)
}
```

### Template Context Access
```jinja2
{# Access previous artifacts in templates #}
{% set strategy = context_store.strategy_artifact %}
{% set design = context_store.design_artifact %}

{# Use data from previous phases #}
Following the strategy of {{ strategy.approach }},
implementing the design with {{ design.file_breakdown | length }} files...
```

## Prompt Engineering Best Practices

### 1. Clear Structure
- Consistent headers and sections
- Explicit required actions
- JSON examples for artifacts

### 2. Persona Embodiment
- Dynamic greetings
- Role-appropriate language
- Avoid repetitive phrases

### 3. Context Awareness
- Reference previous artifacts
- Incorporate feedback
- Maintain conversation flow

### 4. Progressive Disclosure
- Only show relevant context
- Build on previous states
- Avoid information overload

## Artifact Validation

### Validation Flow
```python
# 1. Pydantic validation
try:
    validated = ArtifactModel.model_validate(submitted_data)
except ValidationError as e:
    return detailed_error_message(e)

# 2. Business logic validation
if not validated.slots:
    return "Execution plan must contain at least one SLOT"

# 3. Persistence
context_store[artifact_key] = validated
append_to_scratchpad(validated)
```

### Error Messages
Validation errors are formatted for AI comprehension:
```
Artifact validation failed for state 'generate_slots'.
The submitted artifact does not match the required structure.

Validation Errors:
- slots.0.taskflow.steps: Field required
- slots.1.operation: Invalid enum value 'modify', expected one of: CREATE, MODIFY, DELETE, REVIEW
```

## Advanced Prompt Features

### 1. Conditional Sections
```jinja2
{% if task.acceptance_criteria %}
### Acceptance Criteria
{% for criterion in task.acceptance_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}
```

### 2. Dynamic Lists
```jinja2
### Files to Consider
{% for file in context_store.context_artifact.affected_files %}
- `{{ file }}`
{% endfor %}
```

### 3. Nested Templates
```jinja2
{% include 'partials/persona_guidelines.md' %}
```

## Future Enhancements

1. **Multi-language Prompts**: Support for different languages
2. **Adaptive Prompts**: Adjust based on AI performance
3. **Template Inheritance**: Base templates for consistency
4. **A/B Testing**: Compare prompt effectiveness
5. **Version Control**: Track prompt evolution