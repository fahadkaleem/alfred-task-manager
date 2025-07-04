# Re-planning Support in Discovery Planning

## Overview

Re-planning is a critical feature that handles the reality of changing requirements, new discoveries during implementation, and failed approaches. The Discovery Planning system supports intelligent re-planning that preserves valuable work while adapting to new constraints.

## Design Philosophy

### 1. **Preserve Valuable Work**
- Discovery findings remain valid
- Clarifications still apply
- Reuse decisions where possible
- Only redo what's affected

### 2. **Clear Change Tracking**
- Document what changed
- Explain why re-planning is needed
- Show impact on existing plan
- Maintain audit trail

### 3. **Flexible Entry Points**
- Restart from any phase
- Skip completed phases
- Merge new requirements
- Handle partial failures

## Re-planning Triggers

### 1. Requirements Changed
```python
trigger = "requirements_changed"
changes = "Added SAML authentication requirement"
restart_from = "CONTRACTS"  # Need new interface design
preserve = ["discovery", "clarification"]  # Reuse exploration
```

### 2. Implementation Failed
```python
trigger = "implementation_failed"
changes = "Database schema conflicts discovered"
restart_from = "CONTRACTS"  # Redesign data model
preserve = ["discovery", "clarification"]
```

### 3. Review Feedback
```python
trigger = "review_failed"
changes = "Security team requires encryption at rest"
restart_from = "IMPLEMENTATION_PLAN"  # Update plan only
preserve = ["discovery", "clarification", "contracts"]
```

### 4. New Discoveries
```python
trigger = "new_discovery"
changes = "Found existing auth service we should use"
restart_from = "CLARIFICATION"  # Confirm approach change
preserve = ["discovery"]  # But update with new findings
```

## Implementation

### Initiating Re-planning

```python
def initiate_replanning(
    self,
    trigger: str,
    restart_from: str,
    changes: str,
    preserve_artifacts: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Initiate re-planning with preserved context."""
    
    restart_context = {
        "trigger": trigger,
        "restart_from": restart_from,
        "changes": changes,
        "preserve_artifacts": preserve_artifacts or [],
        "timestamp": datetime.now().isoformat(),
        "previous_state": self.state,
        "previous_turn": self.current_turn_number
    }
    
    # Save current artifacts for preservation
    for artifact_name in preserve_artifacts:
        artifact_key = f"{artifact_name}_artifact"
        if artifact_key in self.context_store:
            restart_context[artifact_name] = self.context_store[artifact_key]
    
    # Store for next planning session
    self.context_store["restart_context"] = restart_context
    
    # Create re-planning turn
    turn_manager.append_turn(
        task_id=self.task_id,
        state_name="replanning_initiated",
        tool_name="plan_task",
        artifact_data={
            "reason": trigger,
            "changes": changes,
            "restart_from": restart_from,
            "preserved_work": preserve_artifacts
        }
    )
    
    return restart_context
```

### Starting with Re-planning Context

```python
# Create new planning tool with restart context
tool = PlanTaskTool(
    task_id="TK-01",
    restart_context={
        "trigger": "requirements_changed",
        "restart_from": "CONTRACTS",
        "changes": "Need to add SAML support",
        "preserve_artifacts": ["discovery", "clarification"],
        "discovery": {...},  # Preserved discovery artifact
        "clarification": {...}  # Preserved clarification artifact
    }
)
```

### Context Loading

```python
def load_plan_task_context(task: Task, task_state: TaskState) -> Dict[str, Any]:
    """Load context including re-planning information."""
    
    # Check for re-planning context
    restart_context = None
    if task_state.active_tool_state:
        restart_context = task_state.active_tool_state.context_store.get("restart_context")
    
    context = {
        "task_title": task.title,
        "task_context": task.context,
        "implementation_details": task.implementation_details,
        "acceptance_criteria": task.acceptance_criteria,
        "restart_context": restart_context,
        "preserved_artifacts": [],
        "replanning_note": ""
    }
    
    # Add preserved artifacts
    if restart_context:
        context["replanning_note"] = f"Re-planning due to: {restart_context['trigger']}"
        context["changes_description"] = restart_context.get("changes", "")
        
        # Load preserved artifacts
        for artifact_name in restart_context.get("preserve_artifacts", []):
            if artifact_name in restart_context:
                context[f"preserved_{artifact_name}"] = restart_context[artifact_name]
                context["preserved_artifacts"].append(artifact_name)
    
    return context
```

## Phase-Specific Re-planning

### Discovery Phase Re-planning

When restarting from DISCOVERY with preserved work:

```markdown
# CONTEXT
Task: TK-01 - Add Authentication
State: discovery
**Re-planning Note**: Re-planning due to: new_discovery

# CHANGES
Found existing OAuth2Service that should be extended instead of creating new service.

# PRESERVED WORK
- Previous clarification decisions remain valid
- Interface contracts may need adjustment

# INSTRUCTIONS
1. Re-explore focusing on OAuth2Service integration
2. Identify what can be reused vs. what needs changing
3. Update questions based on new discovery
4. Note which previous decisions are affected
```

### Clarification Phase Re-planning

When restarting from CLARIFICATION:

```markdown
# PREVIOUS DECISIONS (Preserved)
- JWT tokens with 30min expiry
- Rate limiting at 5 attempts/15min
- Database storage for refresh tokens

# NEW QUESTIONS
Based on the changes: "Security team requires SAML support"

1. Should we support both JWT and SAML, or SAML only?
2. Which SAML provider/library should we use?
3. How do we handle existing JWT users during migration?
```

### Contracts Phase Re-planning

When restarting from CONTRACTS:

```markdown
# PRESERVED ARTIFACTS
- Discovery findings (still valid)
- Clarification decisions (incorporated)

# WHAT CHANGED
Database schema conflicts require new approach to user data storage.

# FOCUS AREAS
1. Redesign user data model to avoid conflicts
2. Update API contracts for new schema
3. Ensure backward compatibility
```

### Implementation Plan Re-planning

When restarting from IMPLEMENTATION_PLAN:

```markdown
# PRESERVED WORK
- All contracts remain unchanged
- Discovery and clarification still valid

# WHAT NEEDS UPDATE
Security requirement: All data must be encrypted at rest

# SUBTASK UPDATES NEEDED
1. Add encryption setup subtask
2. Update data access subtasks for encryption
3. Add migration subtask for existing data
```

## Smart Artifact Merging

### Discovery Merge Strategy

```python
def merge_discovery_artifacts(
    self,
    preserved: ContextDiscoveryArtifact,
    new: ContextDiscoveryArtifact
) -> ContextDiscoveryArtifact:
    """Intelligently merge preserved and new discovery."""
    
    merged = ContextDiscoveryArtifact(
        # Combine findings
        findings=f"{preserved.findings}\n\n## Re-planning Updates\n\n{new.findings}",
        
        # Merge questions, removing answered ones
        questions=self.merge_questions(preserved.questions, new.questions),
        
        # Union of files
        files_to_modify=list(set(preserved.files_to_modify + new.files_to_modify)),
        
        # Reassess complexity
        complexity=max(preserved.complexity, new.complexity),
        
        # Merge implementation context
        implementation_context={
            **preserved.implementation_context,
            **new.implementation_context,
            "replanning_context": {
                "previous_complexity": preserved.complexity,
                "complexity_increased": new.complexity > preserved.complexity
            }
        }
    )
    
    return merged
```

### Clarification Preservation

```python
def apply_preserved_clarifications(
    self,
    new_questions: List[str],
    preserved_clarification: ClarificationArtifact
) -> List[str]:
    """Filter out already answered questions."""
    
    answered_topics = set()
    
    # Extract topics from previous decisions
    for decision in preserved_clarification.decisions:
        # Simple topic extraction (can be enhanced)
        topics = extract_topics(decision)
        answered_topics.update(topics)
    
    # Filter new questions
    remaining_questions = []
    for question in new_questions:
        question_topics = extract_topics(question)
        if not question_topics.intersection(answered_topics):
            remaining_questions.append(question)
    
    return remaining_questions
```

## Re-planning Scenarios

### Scenario 1: Mid-Implementation Requirement Change

**Situation**: Halfway through implementation, product adds real-time notifications.

```python
# Current state: 3 of 5 subtasks complete
replanning_context = {
    "trigger": "requirements_changed",
    "restart_from": "CONTRACTS",  # Need new interfaces
    "changes": "Add real-time notifications via WebSocket",
    "preserve_artifacts": ["discovery", "clarification"],
    "completed_subtasks": ["subtask-1", "subtask-2", "subtask-3"],
    "implementation_progress": {
        "auth_service": "complete",
        "user_model": "complete",
        "api_endpoints": "partial"
    }
}
```

**Approach**:
1. Preserve completed implementation work
2. Re-design contracts to include WebSocket
3. Create new subtasks for notification system
4. Mark original subtasks 4-5 as obsolete

### Scenario 2: Failed Code Review

**Situation**: Code review reveals architectural issues.

```python
replanning_context = {
    "trigger": "review_failed",
    "restart_from": "CONTRACTS",
    "changes": "Must use repository pattern, not direct DB access",
    "preserve_artifacts": ["discovery"],
    "review_feedback": [
        "Direct DB queries in service layer",
        "No abstraction for data access",
        "Testing will be difficult"
    ]
}
```

**Approach**:
1. Keep discovery (still accurate)
2. Re-clarify architecture approach
3. Redesign contracts with repository pattern
4. New implementation plan with proper layers

### Scenario 3: Performance Issues Discovered

**Situation**: Testing reveals performance problems.

```python
replanning_context = {
    "trigger": "testing_failed",
    "restart_from": "IMPLEMENTATION_PLAN",
    "changes": "Query performance too slow, need caching",
    "preserve_artifacts": ["discovery", "clarification", "contracts"],
    "performance_data": {
        "current_latency": "2.5s",
        "required_latency": "200ms",
        "bottleneck": "database queries"
    }
}
```

**Approach**:
1. Keep all design decisions
2. Update implementation plan only
3. Add caching subtasks
4. Include performance testing

## Turn Storage for Re-planning

### Re-planning Turn Structure

```json
{
  "turn_number": 15,
  "state_name": "replanning_initiated",
  "tool_name": "plan_task",
  "timestamp": "2024-01-15T10:30:00Z",
  "artifact_data": {
    "reason": "requirements_changed",
    "changes": "Add SAML authentication support",
    "restart_from": "CONTRACTS",
    "preserved_work": ["discovery", "clarification"],
    "affected_subtasks": ["subtask-2", "subtask-4"],
    "risk_assessment": "MEDIUM"
  }
}
```

### Tracking Re-planning History

```python
def get_replanning_history(self, task_id: str) -> List[Dict]:
    """Get all re-planning events for a task."""
    
    turns = turn_manager.load_all_turns(task_id)
    replanning_events = []
    
    for turn in turns:
        if turn.state_name == "replanning_initiated":
            event = {
                "turn": turn.turn_number,
                "timestamp": turn.timestamp,
                "reason": turn.artifact_data["reason"],
                "changes": turn.artifact_data["changes"],
                "impact": self.assess_replanning_impact(turn)
            }
            replanning_events.append(event)
    
    return replanning_events
```

## Best Practices

### 1. **Minimize Re-work**
- Preserve as much as possible
- Only redo affected parts
- Reuse valid decisions
- Keep discovery findings

### 2. **Clear Communication**
- Document why re-planning
- Show what's preserved
- Highlight changes needed
- Explain impact

### 3. **Progressive Re-planning**
- Start from latest valid phase
- Don't always go back to start
- Build on existing work
- Validate preserved artifacts

### 4. **Audit Trail**
- Track all re-planning events
- Link changes to triggers
- Show decision evolution
- Enable learning

## Configuration

### Re-planning Policy

```yaml
# .alfred/replanning.yml
replanning_policy:
  max_replanning_attempts: 3
  
  preservation_rules:
    discovery: "always"  # Unless fundamentally wrong
    clarification: "when_valid"  # If decisions still apply
    contracts: "when_compatible"  # If interfaces work
    implementation: "never"  # Always redo
  
  triggers:
    requirements_changed:
      default_restart: "CONTRACTS"
      preserve: ["discovery", "clarification"]
      
    implementation_failed:
      default_restart: "IMPLEMENTATION_PLAN"
      preserve: ["discovery", "clarification", "contracts"]
      
    review_failed:
      default_restart: "CONTRACTS"
      preserve: ["discovery"]
```

### Validation Rules

```python
def validate_replanning_request(self, request: Dict) -> bool:
    """Validate re-planning request is sensible."""
    
    validations = {
        "valid_trigger": request["trigger"] in VALID_TRIGGERS,
        "valid_restart": request["restart_from"] in VALID_STATES,
        "preserve_before_restart": self.check_preserve_order(request),
        "not_circular": self.check_not_circular(request),
        "has_changes": bool(request.get("changes"))
    }
    
    return all(validations.values())
```

## Future Enhancements

### 1. **Smart Preservation**
- AI-powered artifact analysis
- Automatic validity checking
- Impact assessment
- Preservation recommendations

### 2. **Differential Planning**
- Show only what changed
- Highlight affected areas
- Side-by-side comparison
- Change impact visualization

### 3. **Re-planning Templates**
- Common scenarios
- Pre-built strategies
- Team preferences
- Historical patterns

### 4. **Continuous Planning**
- Real-time requirement updates
- Progressive refinement
- Living documentation
- Adaptive execution

Re-planning support makes Discovery Planning resilient to change while maximizing the value of completed work. It acknowledges that software development is iterative and requirements evolve, providing a structured way to adapt without starting over.