# Discovery Planning Prompt Template Specifications
## Advanced Prompting Techniques for Maximum AI Effectiveness

> **Author**: Claude Code (Sonnet 4)  
> **Date**: July 3, 2025  
> **Status**: Complete Specification  
> **Purpose**: Detailed prompting strategies for each discovery planning state

---

## Overview

This document provides comprehensive specifications for creating highly effective prompt templates for each state in the Discovery Planning workflow. These specifications follow advanced prompting techniques designed to maximize AI performance and align with Claude Code's natural problem-solving patterns.

---

## 1. General Prompting Principles

### Core Philosophy
**"Prompts should mirror how expert developers naturally think and work, providing clear context, specific instructions, and actionable outputs."**

### Universal Techniques

#### 1.1 Context Layering
```markdown
# CONTEXT
[Immediate context - what is happening right now]
[Task context - what we're trying to accomplish]
[System context - relevant system information]
```

#### 1.2 Cognitive Priming
- **Prime for parallel thinking**: "Use multiple tools simultaneously"
- **Prime for thoroughness**: "Explore comprehensively before planning"
- **Prime for specificity**: "Be specific and actionable"

#### 1.3 Constraint-Driven Design
- **Explicit constraints** prevent AI from going off-rails
- **Positive constraints** (what to do) over negative (what not to do)
- **Prioritized constraints** with clear hierarchy

#### 1.4 Output Specification
- **Structured artifacts** with clear field requirements
- **Required actions** that must be taken
- **Success criteria** for the output

---

## 2. State-Specific Prompting Strategies

### 2.1 DISCOVERY State Prompting

#### Purpose
Guide AI through comprehensive context exploration using multiple tools in parallel.

#### Key Techniques

**1. Parallel Tool Priming**
```markdown
# INSTRUCTIONS
1. **Parallel Exploration**: Use Glob, Grep, Read, and Task tools simultaneously to explore the codebase
```

**2. Pattern Recognition Guidance**
```markdown
2. **Pattern Recognition**: Identify existing coding patterns, architectural decisions, and conventions to follow
```

**3. Context Extraction Focus**
```markdown
5. **Context Extraction**: Gather code snippets, method signatures, and examples that subtasks will need
```

#### Advanced Techniques

**Exploration Breadth Priming**
```markdown
You are beginning the discovery phase of planning. This is the foundation phase where you must:
- Use multiple tools simultaneously (Glob, Grep, Read, Task) for parallel exploration
- Understand existing patterns, architectures, and conventions
- Identify all files and components that will be affected
- Discover integration points and dependencies
- Collect ambiguities for later clarification (don't ask questions yet)
- Extract code snippets and context that will be needed for self-contained subtasks
```

**Ambiguity Collection Priming**
```markdown
6. **Ambiguity Collection**: Note questions and unclear requirements (don't ask yet - just collect)
```

**Quality Gates**
```markdown
# CONSTRAINTS
- Use multiple tools in parallel for maximum efficiency
- Focus on understanding, not designing solutions yet
- Collect ambiguities for later clarification phase
- Extract sufficient context for completely self-contained subtasks
- Follow existing codebase patterns and conventions
```

#### Template Structure
```markdown
<!--
Template: plan_task.discovery
Purpose: Deep context discovery and codebase exploration
Variables: [Standard variables only]
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Perform comprehensive context discovery by exploring the codebase in parallel using all available tools to build deep understanding before planning begins.

# BACKGROUND
[Cognitive priming for discovery mindset]
[Context about the discovery phase importance]
[Specific guidance on parallel exploration]

# INSTRUCTIONS
[Step-by-step parallel exploration guidance]
[Pattern recognition instructions]
[Context extraction requirements]

# CONSTRAINTS
[Boundary setting for discovery scope]
[Quality requirements for context extraction]

# OUTPUT
[Structured artifact specification]
[Required action guidance]

# EXAMPLES
[Good vs bad examples of discovery outputs]
```

### 2.2 CLARIFICATION State Prompting

#### Purpose
Enable natural conversational clarification of discovered ambiguities.

#### Key Techniques

**1. Conversational Priming**
```markdown
This is a CONVERSATIONAL phase - engage in natural dialogue, ask follow-up questions, and seek clarification until all ambiguities are resolved.
```

**2. Context-Rich Question Framework**
```markdown
Good conversation starter: "I found two authentication systems in your codebase. The OAuth2Service handles JWT tokens for API endpoints, while LegacyAuthService manages sessions for web interface. Your task mentions 'authentication updates' - which system should I focus on, or do you want both updated?"
```

**3. Domain Knowledge Transfer Priming**
```markdown
3. **Domain Knowledge Transfer**: Learn from human expertise about business logic, edge cases, and decisions
```

#### Advanced Techniques

**Dialogue Flow Guidance**
```markdown
1. **Present Ambiguities**: Show each discovered ambiguity with full context from your exploration
2. **Conversational Dialogue**: Engage in natural conversation - ask follow-ups, seek examples, clarify nuances
3. **Domain Knowledge Transfer**: Learn from human expertise about business logic, edge cases, and decisions
4. **Requirement Refinement**: Update and clarify requirements based on conversation
5. **Question Everything Unclear**: Don't make assumptions - if something is unclear, ask
6. **Document Conversation**: Keep track of what you learn for future reference
```

**Question Quality Framework**
```markdown
# EXAMPLES
Good conversation starter: "I found two authentication systems in your codebase..."
Good follow-up: "You mentioned OAuth2Service should be the focus. I see it currently supports Google and GitHub providers. Are you looking to add new providers, modify existing flows, or enhance security features?"
Bad question: "How should I implement authentication?" (too vague, no context)
```

### 2.3 CONTRACTS State Prompting

#### Purpose
Guide interface-first design of all APIs and contracts.

#### Key Techniques

**1. Interface-First Priming**
```markdown
This is ARCHITECTURAL design - focus on WHAT interfaces exist and HOW they interact, not implementation details.
```

**2. Contract Completeness Framework**
```markdown
1. **Method Contract Design**: Define all new methods with exact signatures, parameters, return types, and error conditions
2. **Data Model Specification**: Create or update data structures, validation rules, and relationships
3. **API Contract Definition**: Specify external interfaces, request/response schemas, and error responses
4. **Integration Contracts**: Define how components will interact, dependencies, and communication patterns
5. **Error Handling Strategy**: Design exception types, error codes, and recovery patterns
6. **Testing Interface Design**: Consider how each contract will be tested and validated
```

**3. Design Pattern Enforcement**
```markdown
# CONSTRAINTS
- Focus on interfaces and contracts, not implementation
- Follow existing patterns discovered in codebase exploration
- Ensure all contracts are testable and verifiable
- Consider error cases and edge conditions
- Design for the requirements clarified in previous phase
```

#### Advanced Techniques

**Contract Specification Examples**
```markdown
# EXAMPLES
Good method contract:
```
class_name: "UserAuthService"
method_name: "authenticate"
signature: "authenticate(email: str, password: str) -> AuthResult"
purpose: "Authenticate user credentials and return auth result"
error_handling: ["ValidationError for invalid input", "AuthenticationError for failed auth"]
test_approach: "Unit tests with mock credentials, integration tests with test users"
```

Good data model:
```
name: "AuthResult"
fields: [{"name": "user", "type": "User", "required": true}, {"name": "token", "type": "str", "required": true}]
validation_rules: [{"field": "token", "rule": "JWT format validation"}]
relationships: [{"field": "user", "references": "User model"}]
```
```

### 2.4 IMPLEMENTATION_PLAN State Prompting

#### Purpose
Create completely self-contained subtasks with all necessary context.

#### Key Techniques

**1. Self-Containment Priming**
```markdown
Each subtask must be COMPLETELY SELF-CONTAINED - include all code snippets, patterns, examples, and context needed so no additional discovery is required.
```

**2. Context Bundle Framework**
```markdown
2. **Self-Contained Subtask Creation**: Each subtask must include complete context bundle with:
   - Existing code snippets from affected files
   - Related code patterns from other files
   - Data models and utility functions needed
   - Testing patterns and examples
   - Error handling patterns from codebase
```

**3. LOST Framework Integration**
```markdown
5. **Context Bundling**: Ensure each subtask has everything needed without external lookups

# CONSTRAINTS
- Subtasks must be truly independent and self-contained
- Include sufficient context for any developer to execute
- Follow LOST framework (Location, Operation, Specification, Test)
- Base implementation on approved contracts from previous phase
- Ensure subtasks can be assigned to different developers/agents
```

#### Advanced Techniques

**Context Bundle Examples**
```markdown
# EXAMPLES
Good self-contained subtask:
```
subtask_id: "ST-001"
title: "Create UserAuthService.authenticate method"
location: "src/services/UserAuthService.py"
operation: "CREATE"
context_bundle: {
  existing_code: "// Current file content",
  related_code_snippets: {
    "password_hashing": "// bcrypt pattern from existing code",
    "error_handling": "// ValidationError pattern from other services"
  },
  data_models: [AuthResult, User definitions],
  testing_patterns: "// Test structure from existing service tests"
}
specification: {
  exact_changes: ["Add authenticate method to UserAuthService class"],
  method_implementations: [{
    method_name: "authenticate",
    signature: "authenticate(email: str, password: str) -> AuthResult",
    implementation_approach: "Validate input, hash password, check against database, return AuthResult"
  }]
}
```

Bad subtask: Missing context bundle, requires external discovery, not truly independent.
```

**Independence Validation**
```markdown
3. **Test Strategy Integration**: Plan unit tests, integration tests, and validation approaches
4. **Implementation Sequencing**: Consider order dependencies (though subtasks should be independent)
5. **Context Bundling**: Ensure each subtask has everything needed without external lookups
```

### 2.5 VALIDATION State Prompting

#### Purpose
Comprehensive final validation of plan coherence and completeness.

#### Key Techniques

**1. Holistic Validation Priming**
```markdown
All planning phases are complete. Now you must validate the entire plan end-to-end:
- Does the plan achieve all acceptance criteria?
- Are all components consistent and coherent?
- Are subtasks truly independent and complete?
- What are the risks and how can they be mitigated?
- Is the human ready to approve this plan?
```

**2. Quality Gates Framework**
```markdown
1. **End-to-End Validation**: Review the complete plan from discovery through implementation
2. **Requirement Coverage**: Verify every acceptance criterion is addressed in the plan
3. **Contract Consistency**: Ensure all pieces fit together and interfaces align
4. **Subtask Independence**: Validate that subtasks are truly self-contained
5. **Risk Assessment**: Identify potential issues and mitigation strategies
6. **Completeness Check**: Ensure nothing critical is missing
7. **Plan Summary**: Create human-readable summary for approval
```

**3. Risk Assessment Framework**
```markdown
# EXAMPLES
Good requirement coverage:
```
requirement: "Users can login with email/password"
implementation_approach: "UserAuthService.authenticate method validates credentials and returns AuthResult with user and JWT token"
coverage_confidence: 0.95
```

Good risk assessment:
```
risk: "Password validation logic may not handle edge cases"
probability: "MEDIUM"
impact: "HIGH"
mitigation: "Comprehensive unit tests with edge cases and integration tests with real scenarios"
```
```

---

## 3. Advanced Prompting Techniques

### 3.1 Cognitive Load Management

#### Information Layering
```markdown
**Previous Phase Results:**
- Discovery: ${discovery_artifact}
- Clarifications: ${clarification_artifact}
- Contracts: ${contracts_artifact}
```

#### Progressive Disclosure
- **Phase 1**: Core context and immediate objectives
- **Phase 2**: Detailed instructions and constraints
- **Phase 3**: Output specifications and examples

### 3.2 Quality Enforcement

#### Constraint Hierarchies
```markdown
# CONSTRAINTS
- [CRITICAL] Subtasks must be truly independent and self-contained
- [IMPORTANT] Include sufficient context for any developer to execute
- [PREFERRED] Follow LOST framework (Location, Operation, Specification, Test)
```

#### Success Criteria Integration
```markdown
# OUTPUT
Create an ImplementationPlanArtifact with:
- `file_operations`: Exact file changes with current content and modifications
- `subtasks`: List of SelfContainedSubtask objects with complete context bundles
- `test_plan`: Comprehensive testing strategy for all components

**Required Action:** Call `alfred.submit_work` with an `ImplementationPlanArtifact`
```

### 3.3 Error Prevention

#### Common Pitfall Prevention
```markdown
# CONSTRAINTS
- Focus on understanding, not designing solutions yet
- Collect ambiguities for later clarification phase
- Extract sufficient context for completely self-contained subtasks
```

#### Quality Gate Enforcement
```markdown
# INSTRUCTIONS
5. **Context Extraction**: Gather code snippets, method signatures, and examples that subtasks will need
6. **Ambiguity Collection**: Note questions and unclear requirements (don't ask yet - just collect)
```

### 3.4 Human-AI Collaboration

#### Conversational Flow Design
```markdown
This is a CONVERSATIONAL phase - engage in natural dialogue, ask follow-up questions, and seek clarification until all ambiguities are resolved.
```

#### Approval Gate Optimization
```markdown
This is the final quality gate before implementation begins.
```

---

## 4. Template Validation Framework

### 4.1 Structural Validation
- [ ] Header comment with template metadata
- [ ] All required sections present (CONTEXT → OBJECTIVE → BACKGROUND → INSTRUCTIONS → CONSTRAINTS → OUTPUT → EXAMPLES)
- [ ] Only standard variables used
- [ ] No logic in templates (no `{% %}` tags)

### 4.2 Content Validation
- [ ] Clear cognitive priming in BACKGROUND
- [ ] Step-by-step instructions
- [ ] Specific constraints and boundaries
- [ ] Structured output requirements
- [ ] Quality examples provided

### 4.3 Effectiveness Validation
- [ ] Aligns with natural problem-solving patterns
- [ ] Provides sufficient context for decision-making
- [ ] Includes error prevention guidance
- [ ] Supports iterative refinement
- [ ] Enables quality validation

---

## 5. Prompt Evolution Strategy

### 5.1 A/B Testing Framework
- **Version A**: Current prompt template
- **Version B**: Modified prompt with specific improvements
- **Metrics**: Artifact quality, human approval rate, implementation success

### 5.2 Feedback Integration
- **Human feedback**: Incorporate learnings from clarification dialogues
- **Implementation feedback**: Learn from subtask execution success rates
- **Quality metrics**: Track requirement coverage and subtask independence

### 5.3 Continuous Improvement
- **Weekly reviews**: Analyze prompt effectiveness
- **Monthly updates**: Integrate learnings into template improvements
- **Quarterly overhauls**: Major prompt strategy updates

---

## 6. Success Metrics for Prompts

### 6.1 Discovery Phase Metrics
- **Context Completeness**: % of subtasks that execute without additional context discovery
- **Ambiguity Detection**: % of actual ambiguities identified during discovery
- **Pattern Recognition**: Quality score for identified code patterns

### 6.2 Clarification Phase Metrics
- **Resolution Rate**: % of ambiguities successfully resolved
- **Conversation Quality**: Human satisfaction with dialogue
- **Domain Knowledge Transfer**: Quality of insights gained

### 6.3 Contracts Phase Metrics
- **Interface Completeness**: % of planned functionality covered by contracts
- **Contract Coherence**: Consistency score across all contracts
- **Testability**: % of contracts with clear testing approaches

### 6.4 Implementation Planning Metrics
- **Subtask Independence**: % of subtasks with no external dependencies
- **Context Completeness**: % of subtasks with complete context bundles
- **Implementation Success**: % of subtasks that execute successfully

### 6.5 Validation Phase Metrics
- **Plan Coherence**: Overall consistency score
- **Risk Coverage**: % of potential risks identified and mitigated
- **Human Approval Rate**: % of plans approved without revision

---

This comprehensive prompting specification ensures that each state in the Discovery Planning workflow has maximally effective prompts that guide AI toward producing high-quality, actionable outputs that align with expert developer practices.