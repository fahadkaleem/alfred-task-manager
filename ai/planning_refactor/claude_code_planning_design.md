# Claude Code Planning Design
## A Practical, Conversational Planning System for Alfred

> **Author**: Claude Code (Sonnet 4)  
> **Date**: July 3, 2025  
> **Status**: Complete Design, Ready for Implementation  
> **Core Principle**: Mirror how expert developers actually solve complex problems  

---

## Executive Summary

Alfred's current planning system is fundamentally broken because it follows a rigid waterfall model that doesn't match how real software development works. This document presents a complete redesign based on how I (Claude Code) actually approach complex tasks in practice.

**The solution is not more automation or complex frameworks - it's making planning conversational, context-rich, and iterative while keeping it simple.**

## The Real Problem

Current Alfred planning forces a linear flow that assumes:
1. All context can be gathered upfront
2. Strategy can be finalized before detailed design
3. Implementation details can be specified without experimentation
4. Human approval gates add value at abstract levels

**Reality**: Expert developers work iteratively, gathering context progressively, designing contracts first, and planning implementation only when understanding is deep enough.

## Design Philosophy

### Core Principles

1. **Context Saturation**: Use all available tools in parallel to deeply understand the codebase before planning
2. **Conversational Discovery**: Real-time human-AI dialogue when ambiguities emerge, not async queues
3. **Contract-First Design**: Define all interfaces, method signatures, and data models before implementation details
4. **Self-Contained Subtasks**: Each subtask includes all necessary context - no rediscovery needed
5. **Iterative Refinement**: Can restart from any phase when discoveries invalidate previous work

### What We're NOT Building

- ❌ Complex "autonomous modes" and workflow frameworks
- ❌ DecisionPoint async queue systems  
- ❌ Progressive autonomy tracking with ML
- ❌ Multiple database tables for mode management
- ❌ Triage algorithms and complexity scoring

### What We ARE Building

- ✅ Deep context discovery using existing tools
- ✅ Natural conversational clarification  
- ✅ Thorough contract design phase
- ✅ Comprehensive implementation planning
- ✅ Simple restart mechanism for changing requirements

---

## New State Machine Design

### State Flow
```
DISCOVERY → CLARIFICATION → CONTRACTS → IMPLEMENTATION_PLAN → VALIDATION → VERIFIED
```

### State Transitions

**Normal Flow**: Linear progression through phases  
**Replanning Flow**: Restart from any phase with preserved context  
**Complexity Adaptation**: Skip CONTRACTS for simple tasks  

---

## Detailed State Specifications

### 1. DISCOVERY (Context Saturation)

**Purpose**: Comprehensive autonomous context gathering using all available tools

**Activities**:
- **Parallel Tool Usage**: Glob, Grep, Read, Task tools used simultaneously
- **Deep Code Analysis**: Understand existing patterns, architectures, conventions
- **Dependency Mapping**: Identify what connects to what, integration points
- **Ambiguity Collection**: Note questions and unclear requirements (don't ask yet)
- **File Context Extraction**: Gather code snippets that will be needed for subtasks

**No Human Interaction**: Pure AI exploration phase

**Artifact**: `ContextDiscoveryArtifact`
```typescript
interface ContextDiscoveryArtifact {
  codebase_understanding: {
    relevant_files: string[];
    existing_patterns: CodePattern[];
    integration_points: IntegrationPoint[];
    dependencies: Dependency[];
  };
  ambiguities_discovered: {
    question: string;
    context: string;
    impact_if_wrong: string;
  }[];
  extracted_context: {
    code_snippets: Record<string, string>;  // For subtask inclusion
    existing_methods: MethodSignature[];
    data_models: ModelDefinition[];
  };
}
```

### 2. CLARIFICATION (Conversational Q&A)

**Purpose**: Resolve all discovered ambiguities through focused human conversation

**Activities**:
- **Present Questions with Context**: Show discovered ambiguities with relevant code context
- **Natural Conversation**: Real-time Q&A, follow-up questions, explanations
- **Requirement Refinement**: Update task based on clarifications
- **Domain Knowledge Transfer**: Human shares context not available in training data

**Human Interaction**: **Full conversational mode** - not approval gates, actual dialogue

**Conversation Example**:
```
AI: "I found two authentication systems in the codebase:
1. OAuth2Service (newer, handles JWT tokens)
2. LegacyAuthService (older, session-based)

The task mentions 'update authentication' but doesn't specify which. 
Looking at usage patterns, OAuth2Service is used for API endpoints 
while LegacyAuthService handles web sessions.

Which system should I focus on? Or do you want me to update both?"
```

**Artifact**: `ClarificationArtifact`
```typescript
interface ClarificationArtifact {
  resolved_ambiguities: {
    original_question: string;
    human_response: string;
    clarification: string;
  }[];
  updated_requirements: TaskRequirements;
  domain_knowledge_gained: string[];
}
```

### 3. CONTRACTS (Interface-First Design)

**Purpose**: Define all interfaces, method signatures, and data contracts before implementation

**Activities**:
- **Method Signature Design**: Define all new methods with parameters, return types, error handling
- **Data Model Specification**: Create/update data structures, validation schemas
- **API Contract Definition**: External interfaces, event schemas, integration points
- **Error Handling Strategy**: Define exception types, error codes, recovery patterns
- **Testing Interface Design**: How each contract will be tested

**Human Interaction**: **Approval of high-level approach** - review contracts and architectural decisions

**Artifact**: `ContractDesignArtifact`
```typescript
interface ContractDesignArtifact {
  method_contracts: {
    class_name: string;
    method_name: string;
    signature: string;
    purpose: string;
    error_handling: string[];
    test_approach: string;
  }[];
  data_models: {
    name: string;
    fields: ModelField[];
    validation_rules: ValidationRule[];
    relationships: Relationship[];
  }[];
  api_contracts: {
    endpoint: string;
    method: HTTPMethod;
    request_schema: Schema;
    response_schema: Schema;
    error_responses: ErrorResponse[];
  }[];
  integration_contracts: {
    component: string;
    interface: string;
    dependencies: string[];
  }[];
}
```

### 4. IMPLEMENTATION_PLAN (Comprehensive Planning)

**Purpose**: Create detailed, self-contained implementation plan based on contracts

**Activities**:
- **File-Level Planning**: Exactly which files to create/modify/delete
- **Method-Level Specifications**: Implementation approach for each method
- **Test Strategy Integration**: Unit and integration test plans
- **Self-Contained Subtask Creation**: Each subtask includes all necessary context
- **Dependency Order Analysis**: Sequence considerations (though subtasks should be independent)

**No Human Interaction**: Pure AI planning based on approved contracts

**Artifact**: `ImplementationPlanArtifact`
```typescript
interface ImplementationPlanArtifact {
  file_operations: {
    file_path: string;
    operation: 'CREATE' | 'MODIFY' | 'DELETE';
    existing_code_context: string;  // Current file content
    changes_description: string;
    affected_methods: string[];
  }[];
  subtasks: SelfContainedSubtask[];
  test_plan: {
    unit_tests: TestSpecification[];
    integration_tests: TestSpecification[];
    test_data_requirements: TestDataSpec[];
  };
  implementation_notes: string[];
}

interface SelfContainedSubtask {
  subtask_id: string;
  title: string;
  location: string;
  operation: 'CREATE' | 'MODIFY' | 'DELETE';
  
  // Complete context bundle - no external dependencies
  context_bundle: {
    existing_code: string;           // Current file content
    related_code_snippets: Record<string, string>;  // From other files
    data_models: ModelDefinition[];  // All models used
    utility_functions: string[];     // Helper functions available
    testing_patterns: string;        // How to test in this codebase
    error_handling_patterns: string; // How errors are handled
  };
  
  // Detailed specifications
  specification: {
    exact_changes: string[];         // Step-by-step what to do
    method_implementations: {
      method_name: string;
      signature: string;
      implementation_approach: string;
      edge_cases: string[];
    }[];
    integration_points: string[];    // How this connects to other code
  };
  
  // Testing requirements
  testing: {
    unit_tests_to_create: string[];
    test_data: TestData[];
    verification_steps: string[];
    expected_outcomes: string[];
  };
  
  // Validation
  acceptance_criteria: string[];
  dependencies: string[];  // Should be empty for true independence
}
```

### 5. VALIDATION (Final Coherence Check)

**Purpose**: Final validation that complete plan works cohesively

**Activities**:
- **End-to-End Plan Review**: Does the entire plan achieve the requirements?
- **Contract Consistency Check**: Do all pieces fit together properly?
- **Completeness Validation**: Are we missing anything critical?
- **Risk Assessment**: What could go wrong during implementation?
- **Subtask Independence Verification**: Can each subtask truly execute independently?

**Human Interaction**: **Final plan approval** - comprehensive review before implementation

**Artifact**: `ValidationArtifact`
```typescript
interface ValidationArtifact {
  plan_summary: {
    files_affected: number;
    methods_created: number;
    methods_modified: number;
    tests_planned: number;
    estimated_complexity: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  requirement_coverage: {
    requirement: string;
    implementation_approach: string;
    coverage_confidence: number;  // 0-1
  }[];
  risk_assessment: {
    risk: string;
    probability: 'LOW' | 'MEDIUM' | 'HIGH';
    impact: 'LOW' | 'MEDIUM' | 'HIGH';
    mitigation: string;
  }[];
  subtask_independence_check: {
    subtask_id: string;
    is_independent: boolean;
    dependencies_found: string[];
  }[];
}
```

---

## Complexity Adaptation

### Simple Task Flow (Skip CONTRACTS)
```
DISCOVERY → CLARIFICATION → IMPLEMENTATION_PLAN → VALIDATION → VERIFIED
```

**When to use**: Bug fixes, documentation updates, small feature additions

**Criteria**:
- < 3 files affected
- No new APIs or data models
- Well-understood domain
- Clear requirements

### Complex Task Flow (Full Process)
```
DISCOVERY → CLARIFICATION → CONTRACTS → IMPLEMENTATION_PLAN → VALIDATION → VERIFIED
```

**When to use**: New features, architectural changes, integrations

**Criteria**:
- Multiple files/components affected
- New APIs or data models
- Cross-cutting concerns
- Integration requirements

---

## Re-Planning Capability

### Trigger Scenarios
- Requirements change during planning
- Implementation discovers plan won't work
- Review finds fundamental issues
- New constraints discovered

### Re-Planning API
```python
plan_task(
    task_id="AL-001", 
    restart_from="CLARIFICATION",  # or any state
    context={
        "trigger": "requirements_changed",
        "changes": "Now need to support SAML authentication",
        "preserve_artifacts": ["discovery", "partial_contracts"],
        "invalidated_decisions": ["oauth_only_approach"]
    }
)
```

### State Restart Rules
- **DISCOVERY**: Start fresh, previous context may be stale
- **CLARIFICATION**: Preserve discovery, re-ask questions with new context
- **CONTRACTS**: Preserve clarifications, redesign interfaces
- **IMPLEMENTATION_PLAN**: Preserve contracts, re-plan implementation
- **VALIDATION**: Preserve plan, re-validate with new criteria

---

## Implementation Strategy

### Existing FSM Integration

**Use Current Builder Pattern**:
```python
class PlanTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str, restart_context: Optional[Dict] = None):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK)
        
        # Handle re-planning
        if restart_context:
            initial_state = restart_context.get("restart_from", PlanTaskState.DISCOVERY)
            self.preserved_artifacts = restart_context.get("preserve_artifacts", [])
        else:
            initial_state = PlanTaskState.DISCOVERY
            
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=[
                PlanTaskState.DISCOVERY,
                PlanTaskState.CLARIFICATION, 
                PlanTaskState.CONTRACTS,
                PlanTaskState.IMPLEMENTATION_PLAN,
                PlanTaskState.VALIDATION
            ],
            terminal_state=PlanTaskState.VERIFIED,
            initial_state=initial_state,
        )
```

### New State Enum
```python
class PlanTaskState(str, Enum):
    DISCOVERY = "discovery"
    CLARIFICATION = "clarification"  
    CONTRACTS = "contracts"
    IMPLEMENTATION_PLAN = "implementation_plan"
    VALIDATION = "validation"
    VERIFIED = "verified"
```

### Review Process Integration

**AI Review States** (automatic):
- `discovery_awaiting_ai_review`
- `clarification_awaiting_ai_review`
- `contracts_awaiting_ai_review`
- `implementation_plan_awaiting_ai_review`
- `validation_awaiting_ai_review`

**Human Review States** (approval gates):
- `clarification_awaiting_human_review` - After Q&A completion
- `contracts_awaiting_human_review` - After interface design
- `validation_awaiting_human_review` - Final plan approval

**Revision Handling**:
- Technical issues → back to current work state
- Requirement issues → back to CLARIFICATION
- Contract issues → back to CONTRACTS

---

## Autonomous Mode Support

### Configuration-Based Autonomy
```python
autonomous_config = {
    "skip_human_reviews": True,
    "auto_approve_contracts": True,
    "question_handling": "best_guess",  # or "skip_task"
    "confidence_threshold": 0.8
}
```

### Autonomous Behavior
- **CLARIFICATION**: Skip if no critical ambiguities
- **CONTRACTS**: Auto-approve if following existing patterns
- **VALIDATION**: Auto-approve if low risk and high confidence

### Autonomous Safeguards
- Always create artifacts for audit trail
- Escalate on complexity threshold breach
- Require human review for high-risk changes

---

## Benefits Over Current System

### 1. Mirrors Real Development Process
- Context discovery matches how developers explore codebases
- Conversational clarification reflects real team communication
- Contract-first design follows best practices
- Iterative refinement handles changing requirements

### 2. Self-Contained Subtasks
- Each subtask includes all necessary context
- No rediscovery needed during implementation
- Can be assigned to sub-agents
- Truly independent execution

### 3. Practical Human Interaction
- Conversational Q&A instead of abstract approvals
- Focused on actual ambiguities and decisions
- Reduced ceremony, increased value

### 4. Simple but Effective
- Uses existing FSM infrastructure
- No complex new frameworks
- Clear state transitions
- Maintainable and debuggable

### 5. Re-Planning Support
- Handle changing requirements gracefully
- Preserve work when assumptions change
- Learn from failures

---

## Success Metrics

### Planning Quality
- **Requirement Coverage**: Percentage of acceptance criteria addressed in plan
- **Context Completeness**: Successful implementation without additional context discovery
- **Subtask Independence**: Percentage of subtasks completing without external dependencies

### Efficiency
- **Planning Time**: End-to-end planning duration
- **Re-Planning Frequency**: How often plans need major revisions
- **Human Time Investment**: Time spent in clarification and approval phases

### Implementation Success
- **First-Pass Success Rate**: Subtasks completing without plan modifications
- **Test Coverage Achievement**: Planned vs actual test coverage
- **Integration Success**: How well planned components integrate

---

## Migration Path

### Phase 1: Core Implementation (2-3 weeks)
- Implement new state machine with 5 states
- Build DISCOVERY phase with parallel tool usage
- Create conversational CLARIFICATION interface
- Basic artifact definitions

### Phase 2: Contract Design (1-2 weeks)
- Implement CONTRACTS phase
- Build contract design templates
- Add human approval interface
- Integration with existing review system

### Phase 3: Implementation Planning (2-3 weeks)
- Build IMPLEMENTATION_PLAN phase
- Create self-contained subtask generation
- Add context bundling logic
- Comprehensive test planning

### Phase 4: Validation & Re-Planning (1-2 weeks)
- Implement VALIDATION phase
- Add re-planning capability
- Build complexity adaptation logic
- End-to-end testing

### Phase 5: Production (1 week)
- Performance optimization
- Documentation
- Monitoring and metrics
- Gradual rollout

---

## Conclusion

This design solves Alfred's core planning problems by:

1. **Making planning conversational** - Real human-AI collaboration instead of approval theater
2. **Emphasizing context saturation** - Deep understanding before planning
3. **Designing contracts first** - Interfaces before implementation details  
4. **Creating truly independent subtasks** - No rediscovery needed
5. **Supporting iteration** - Handle changing requirements gracefully

The result is a planning system that mirrors how expert developers actually work while maintaining the quality and structure that Alfred provides.

**Most importantly: This system is designed for how Claude Code actually operates, making it maximally effective for AI-human collaboration in software development.**