# Discovery Planning Implementation Design
## Alfred Task Manager Enhanced Planning System

> **Author**: Claude Code (Sonnet 4)  
> **Date**: July 3, 2025  
> **Status**: Implementation Ready  
> **Follows**: All Alfred architectural principles in `docs/principles/`

---

## Executive Summary

This document provides the complete implementation specification for replacing Alfred's current planning system with the Discovery Planning approach. The new system will be called `plan_task` (replacing the existing one) and follows ALL existing architectural principles while delivering conversational, context-rich planning.

## Architecture Compliance

### State Machine Principles ✅
- **Uses Pattern 1**: Multi-step workflow with reviews
- **Uses the builder**: `workflow_builder.build_workflow_with_reviews()`
- **No custom transitions**: Builder handles all state transitions
- **Sacred review pattern**: work_state → ai_review → human_review

### Handler Principles ✅  
- **Uses GenericWorkflowHandler**: No custom handler classes
- **Configuration-driven**: All behavior via `WorkflowToolConfig`
- **Pure context loaders**: Stateless functions only
- **Immutable configuration**: Data, not code

### Template System Principles ✅
- **Strict section format**: CONTEXT → OBJECTIVE → BACKGROUND → INSTRUCTIONS → CONSTRAINTS → OUTPUT → EXAMPLES
- **Frozen variables**: Only standard template variables used
- **Template location**: `prompts/plan_task/{state}.md`
- **No logic**: Pure template substitution only

### Tool Registration Principles ✅
- **Uses @tool decorator**: Standard registration pattern
- **GenericWorkflowHandler**: No custom handlers
- **Pure context loaders**: Stateless dependency injection
- **Configuration-driven**: Behavior via `WorkflowToolConfig`

---

## New State Machine Design

### State Enum
```python
class PlanTaskState(str, Enum):
    DISCOVERY = "discovery"
    CLARIFICATION = "clarification" 
    CONTRACTS = "contracts"
    IMPLEMENTATION_PLAN = "implementation_plan"
    VALIDATION = "validation"
    VERIFIED = "verified"
```

### State Machine Pattern
**Pattern 1**: Multi-step workflow with reviews
```python
machine_config = workflow_builder.build_workflow_with_reviews(
    work_states=[
        PlanTaskState.DISCOVERY,
        PlanTaskState.CLARIFICATION,
        PlanTaskState.CONTRACTS, 
        PlanTaskState.IMPLEMENTATION_PLAN,
        PlanTaskState.VALIDATION
    ],
    terminal_state=PlanTaskState.VERIFIED,
    initial_state=PlanTaskState.DISCOVERY,
)
```

### Auto-Generated Review States
The builder will automatically create:
- `discovery_awaiting_ai_review`
- `discovery_awaiting_human_review`
- `clarification_awaiting_ai_review`
- `clarification_awaiting_human_review`
- `contracts_awaiting_ai_review`
- `contracts_awaiting_human_review`
- `implementation_plan_awaiting_ai_review`
- `implementation_plan_awaiting_human_review`
- `validation_awaiting_ai_review`
- `validation_awaiting_human_review`

---

## Tool Configuration

### WorkflowToolConfig Entry
```python
"plan_task": WorkflowToolConfig(
    tool_name="plan_task",
    tool_class=PlanTaskTool,
    required_status=[TaskStatus.NEW, TaskStatus.PLANNING],
    entry_status_map={
        TaskStatus.NEW: TaskStatus.PLANNING,
        TaskStatus.PLANNING: TaskStatus.PLANNING  # Stay in planning
    },
    dispatch_on_init=True,
    dispatch_state_attr="state",
    target_state_method="dispatch",
    context_loader=load_plan_task_context,
    requires_artifact_from=None  # No dependencies
)
```

### Pure Function Context Loader
```python
def load_plan_task_context(task: Task, task_state: TaskState) -> dict:
    """Pure function context loader for plan_task."""
    # Check for re-planning context
    restart_context = task_state.context_store.get("restart_context")
    
    return {
        "task_title": task.title,
        "task_context": task.context,
        "implementation_details": task.implementation_details,
        "acceptance_criteria": task.acceptance_criteria,
        "restart_context": restart_context,
        "preserved_artifacts": task_state.context_store.get("preserved_artifacts", [])
    }
```

---

## Artifact Specifications

### 1. ContextDiscoveryArtifact
```python
class ContextDiscoveryArtifact(BaseModel):
    """Comprehensive context discovery results."""
    
    codebase_understanding: Dict[str, Any] = Field(
        description="Deep understanding of relevant codebase components"
    )
    ambiguities_discovered: List[Dict[str, str]] = Field(
        description="Questions that need human clarification"
    )
    extracted_context: Dict[str, Any] = Field(
        description="Code snippets and context for subtask inclusion"
    )
    complexity_assessment: str = Field(
        description="LOW/MEDIUM/HIGH complexity based on discovery"
    )
```

### 2. ClarificationArtifact  
```python
class ClarificationArtifact(BaseModel):
    """Results of human-AI clarification dialogue."""
    
    resolved_ambiguities: List[Dict[str, str]] = Field(
        description="Questions and their resolutions"
    )
    updated_requirements: Dict[str, Any] = Field(
        description="Requirements refined based on clarifications"
    )
    domain_knowledge_gained: List[str] = Field(
        description="Domain expertise provided by human"
    )
```

### 3. ContractDesignArtifact
```python
class ContractDesignArtifact(BaseModel):
    """Interface-first design specifications."""
    
    method_contracts: List[Dict[str, Any]] = Field(
        description="Method signatures and specifications"
    )
    data_models: List[Dict[str, Any]] = Field(
        description="Data structure definitions"
    )
    api_contracts: List[Dict[str, Any]] = Field(
        description="External interface specifications"
    )
    integration_contracts: List[Dict[str, Any]] = Field(
        description="Component interaction specifications"
    )
```

### 4. ImplementationPlanArtifact
```python
class ImplementationPlanArtifact(BaseModel):
    """Detailed implementation plan with self-contained subtasks."""
    
    file_operations: List[Dict[str, Any]] = Field(
        description="Exact file changes required"
    )
    subtasks: List[Dict[str, Any]] = Field(
        description="Self-contained LOST subtasks"
    )
    test_plan: Dict[str, Any] = Field(
        description="Comprehensive testing strategy"
    )
    implementation_notes: List[str] = Field(
        description="Additional implementation guidance"
    )
```

### 5. ValidationArtifact
```python
class ValidationArtifact(BaseModel):
    """Final plan validation and coherence check."""
    
    plan_summary: Dict[str, Any] = Field(
        description="High-level plan summary statistics"
    )
    requirement_coverage: List[Dict[str, Any]] = Field(
        description="How each requirement is addressed"
    )
    risk_assessment: List[Dict[str, Any]] = Field(
        description="Identified risks and mitigations"
    )
    subtask_independence_check: List[Dict[str, Any]] = Field(
        description="Verification of subtask independence"
    )
```

---

## Template Specifications

### Template Structure (All States)
Every template follows the sacred format:
```markdown
<!--
Template: plan_task.{state}
Purpose: [One line description]
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
[State context]

# OBJECTIVE  
[What this state accomplishes]

# BACKGROUND
[Background information]

# INSTRUCTIONS
[Detailed step-by-step instructions]

# CONSTRAINTS
[Limitations and constraints]

# OUTPUT
[Required artifact specification]

# EXAMPLES
[Good/bad examples]
```

### Template Locations
- `src/alfred/templates/prompts/plan_task/discovery.md`
- `src/alfred/templates/prompts/plan_task/clarification.md`
- `src/alfred/templates/prompts/plan_task/contracts.md`
- `src/alfred/templates/prompts/plan_task/implementation_plan.md`
- `src/alfred/templates/prompts/plan_task/validation.md`

---

## Re-Planning Support

### Re-Planning Context Structure
```python
restart_context = {
    "trigger": "requirements_changed",  # or "implementation_failed", "review_failed"
    "restart_from": "CONTRACTS",        # State to restart from
    "changes": "Now need SAML support", # What changed
    "preserve_artifacts": ["discovery", "clarification"],  # What to keep
    "invalidated_decisions": ["oauth_only_approach"]       # What to discard
}
```

### Re-Planning Flow
1. **Store restart context** in task_state.context_store
2. **Restart tool** with preserved artifacts
3. **Skip preserved phases** or reload preserved artifacts
4. **Continue from restart point**

---

## Human Interaction Design

### Conversational States
**CLARIFICATION state only**: Real-time Q&A dialogue
- Present discovered ambiguities with full context
- Allow follow-up questions and explanations
- Update requirements based on human input

### Approval States  
**CONTRACTS and VALIDATION**: High-level approval gates
- CONTRACTS: Approve architectural approach and interfaces
- VALIDATION: Approve final comprehensive plan

### Autonomous Mode
Configuration flag skips human interaction:
```python
autonomous_config = {
    "skip_human_reviews": True,
    "auto_approve_contracts": True,
    "question_handling": "best_guess"
}
```

---

## Complexity Adaptation

### Simple Task Detection
Skip CONTRACTS state when:
- < 3 files affected
- No new APIs or data models  
- Well-understood domain
- Clear requirements

### Flow Adaptation
```python
def determine_workflow_states(discovery_artifact):
    base_states = [
        PlanTaskState.DISCOVERY,
        PlanTaskState.CLARIFICATION
    ]
    
    if requires_contracts_phase(discovery_artifact):
        base_states.append(PlanTaskState.CONTRACTS)
    
    base_states.extend([
        PlanTaskState.IMPLEMENTATION_PLAN,
        PlanTaskState.VALIDATION
    ])
    
    return base_states
```

---

## File Creation Plan

### New Files to Create
```
src/alfred/tools/plan_task.py                    # Replace existing
src/alfred/core/discovery_workflow.py            # New state machine
src/alfred/models/discovery_artifacts.py         # New artifacts  
src/alfred/templates/prompts/plan_task/          # Replace existing templates
├── discovery.md
├── clarification.md
├── contracts.md
├── implementation_plan.md
└── validation.md
```

### Files to Modify
```
src/alfred/tools/tool_definitions.py             # Update plan_task config
src/alfred/core/workflow.py                      # Add new PlanTaskTool class
src/alfred/models/planning_artifacts.py          # Add new artifact imports
```

### Files to Deprecate (Later)
```
src/alfred/templates/prompts/plan_task/contextualize.md    # Old templates
src/alfred/templates/prompts/plan_task/strategize.md
src/alfred/templates/prompts/plan_task/design.md
src/alfred/templates/prompts/plan_task/generate_subtasks.md
```

---

## Testing Strategy

### State Machine Testing
```python
def test_discovery_plan_state_machine():
    tool = PlanTaskTool("test-task-1")
    
    # Test initial state
    assert tool.state == PlanTaskState.DISCOVERY.value
    
    # Test state transitions via builder
    tool.submit_work()  # Should advance to review states
    assert tool.state == "discovery_awaiting_ai_review"
```

### Artifact Testing
```python
def test_discovery_artifact_validation():
    artifact = ContextDiscoveryArtifact(
        codebase_understanding={"files": ["test.py"]},
        ambiguities_discovered=[],
        extracted_context={},
        complexity_assessment="LOW"
    )
    assert artifact.complexity_assessment in ["LOW", "MEDIUM", "HIGH"]
```

### Template Testing
```python
def test_template_compliance():
    for state in PlanTaskState:
        if state != PlanTaskState.VERIFIED:
            template_path = f"prompts/plan_task/{state.value}.md"
            verify_template_structure(template_path)
            verify_template_variables(template_path)
```

---

## Migration Strategy

### Phase 1: Core Infrastructure (Week 1)
1. Create new artifact models
2. Create new state machine
3. Update tool configuration
4. Basic template structure

### Phase 2: Discovery Implementation (Week 1)  
1. Implement DISCOVERY state logic
2. Create discovery prompt template
3. Test context gathering functionality
4. Validate artifact generation

### Phase 3: Clarification System (Week 2)
1. Implement CLARIFICATION state
2. Create conversational interface
3. Test Q&A dialogue system
4. Validate ambiguity resolution

### Phase 4: Contract Design (Week 2)
1. Implement CONTRACTS state
2. Create interface design prompts
3. Test contract generation
4. Validate architectural approval

### Phase 5: Implementation Planning (Week 3)
1. Implement IMPLEMENTATION_PLAN state
2. Create self-contained subtask generation
3. Test context bundling
4. Validate subtask independence

### Phase 6: Validation & Re-Planning (Week 3)
1. Implement VALIDATION state
2. Add re-planning capability
3. Test complexity adaptation
4. End-to-end validation

### Phase 7: Production Deployment (Week 4)
1. Performance optimization
2. Comprehensive testing
3. Documentation updates
4. Gradual rollout

---

## Success Metrics

### Planning Quality
- **Context Completeness**: 95% of subtasks execute without additional context discovery
- **Requirement Coverage**: 100% of acceptance criteria addressed in plan
- **Subtask Independence**: 90% of subtasks complete without external dependencies

### Efficiency  
- **Planning Time**: < 10 minutes for simple tasks, < 30 minutes for complex
- **Re-Planning Frequency**: < 10% of plans require major revisions
- **Human Time**: < 5 minutes for clarification, < 3 minutes for approvals

### Implementation Success
- **First-Pass Success**: 85% of subtasks complete without plan modifications
- **Test Coverage**: Planned vs actual test coverage within 10%
- **Integration Success**: 95% of planned components integrate without issues

---

## Conclusion

This implementation design provides a complete roadmap for replacing Alfred's planning system while maintaining full compliance with all architectural principles. The new system delivers:

1. **Conversational Planning**: Real human-AI collaboration
2. **Context Saturation**: Deep codebase understanding before planning
3. **Contract-First Design**: Interfaces before implementation
4. **Self-Contained Subtasks**: No rediscovery needed
5. **Re-Planning Support**: Handle changing requirements gracefully

**Most importantly**: This system is designed to maximize Claude Code's effectiveness by mirroring natural problem-solving processes while maintaining Alfred's quality and structure guarantees.