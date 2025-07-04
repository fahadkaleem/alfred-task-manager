# Discovery Planning File Creation Plan
## Complete Blueprint for Implementation

> **Author**: Claude Code (Sonnet 4)  
> **Date**: July 3, 2025  
> **Status**: Implementation Blueprint  
> **Purpose**: Exact specification of all files to create/modify

---

## Overview

This document provides the complete file-by-file specification for implementing the Discovery Planning system. Every file is specified with exact content structure, following Alfred's architectural principles.

---

## 1. NEW FILES TO CREATE

### 1.1 Core State Machine
**File**: `src/alfred/core/discovery_workflow.py`

```python
"""Discovery planning workflow state machine implementation."""

from enum import Enum
from typing import Any, Dict, Optional
from transitions.core import Machine

from src.alfred.constants import ToolName
from src.alfred.core.state_machine_builder import workflow_builder
from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.models.discovery_artifacts import (
    ContextDiscoveryArtifact,
    ClarificationArtifact,
    ContractDesignArtifact,
    ImplementationPlanArtifact,
    ValidationArtifact,
)


class PlanTaskState(str, Enum):
    """State enumeration for the discovery planning workflow."""
    DISCOVERY = "discovery"
    CLARIFICATION = "clarification"
    CONTRACTS = "contracts"
    IMPLEMENTATION_PLAN = "implementation_plan"
    VALIDATION = "validation"
    VERIFIED = "verified"


class PlanTaskTool(BaseWorkflowTool):
    """Discovery planning tool with conversational, context-rich workflow."""
    
    def __init__(self, task_id: str, restart_context: Optional[Dict] = None):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK)
        
        # Define artifact mapping
        self.artifact_map = {
            PlanTaskState.DISCOVERY: ContextDiscoveryArtifact,
            PlanTaskState.CLARIFICATION: ClarificationArtifact,
            PlanTaskState.CONTRACTS: ContractDesignArtifact,
            PlanTaskState.IMPLEMENTATION_PLAN: ImplementationPlanArtifact,
            PlanTaskState.VALIDATION: ValidationArtifact,
        }
        
        # Handle re-planning context
        if restart_context:
            initial_state = self._determine_restart_state(restart_context)
            self._load_preserved_artifacts(restart_context)
        else:
            initial_state = PlanTaskState.DISCOVERY
            
        # Determine workflow states based on complexity
        workflow_states = self._determine_workflow_states()
        
        # Use the builder to create state machine configuration
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=workflow_states,
            terminal_state=PlanTaskState.VERIFIED,
            initial_state=initial_state,
        )
        
        # Create the state machine
        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )
        
    def get_final_work_state(self) -> str:
        """Return the final work state that produces the main artifact."""
        return PlanTaskState.VALIDATION.value
        
    def _determine_restart_state(self, restart_context: Dict) -> PlanTaskState:
        """Determine initial state for re-planning."""
        restart_from = restart_context.get("restart_from", "DISCOVERY")
        return PlanTaskState(restart_from.lower())
        
    def _load_preserved_artifacts(self, restart_context: Dict) -> None:
        """Load preserved artifacts from previous planning attempt."""
        preserved = restart_context.get("preserve_artifacts", [])
        for artifact_name in preserved:
            # Load preserved artifact into context_store
            self.context_store[f"preserved_{artifact_name}"] = restart_context.get(artifact_name)
            
    def _determine_workflow_states(self) -> list:
        """Determine which states to include based on complexity."""
        # For now, include all states. Later can add complexity detection
        return [
            PlanTaskState.DISCOVERY,
            PlanTaskState.CLARIFICATION,
            PlanTaskState.CONTRACTS,
            PlanTaskState.IMPLEMENTATION_PLAN,
            PlanTaskState.VALIDATION
        ]
        
    def should_skip_contracts(self, discovery_artifact: ContextDiscoveryArtifact) -> bool:
        """Determine if CONTRACTS state should be skipped for simple tasks."""
        if not discovery_artifact:
            return False
            
        # Simple task criteria
        complexity = getattr(discovery_artifact, 'complexity_assessment', 'MEDIUM')
        return complexity == 'LOW'
```

### 1.2 Discovery Artifacts Models
**File**: `src/alfred/models/discovery_artifacts.py`

```python
"""Pydantic models for discovery planning artifacts."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextDiscoveryArtifact(BaseModel):
    """Comprehensive context discovery results from DISCOVERY state."""
    
    codebase_understanding: Dict[str, Any] = Field(
        description="Deep understanding of relevant codebase components",
        default_factory=dict
    )
    
    ambiguities_discovered: List[Dict[str, str]] = Field(
        description="Questions that need human clarification",
        default_factory=list
    )
    
    extracted_context: Dict[str, Any] = Field(
        description="Code snippets and context for subtask inclusion",
        default_factory=dict
    )
    
    complexity_assessment: str = Field(
        description="LOW/MEDIUM/HIGH complexity based on discovery",
        default="MEDIUM"
    )
    
    relevant_files: List[str] = Field(
        description="Files that will be affected by this task",
        default_factory=list
    )
    
    integration_points: List[Dict[str, str]] = Field(
        description="Integration points and dependencies discovered",
        default_factory=list
    )


class ClarificationArtifact(BaseModel):
    """Results of human-AI clarification dialogue from CLARIFICATION state."""
    
    resolved_ambiguities: List[Dict[str, str]] = Field(
        description="Questions and their resolutions",
        default_factory=list
    )
    
    updated_requirements: Dict[str, Any] = Field(
        description="Requirements refined based on clarifications",
        default_factory=dict
    )
    
    domain_knowledge_gained: List[str] = Field(
        description="Domain expertise provided by human",
        default_factory=list
    )
    
    conversation_log: List[Dict[str, str]] = Field(
        description="Log of the clarification conversation",
        default_factory=list
    )


class ContractDesignArtifact(BaseModel):
    """Interface-first design specifications from CONTRACTS state."""
    
    method_contracts: List[Dict[str, Any]] = Field(
        description="Method signatures and specifications",
        default_factory=list
    )
    
    data_models: List[Dict[str, Any]] = Field(
        description="Data structure definitions",
        default_factory=list
    )
    
    api_contracts: List[Dict[str, Any]] = Field(
        description="External interface specifications",
        default_factory=list
    )
    
    integration_contracts: List[Dict[str, Any]] = Field(
        description="Component interaction specifications",
        default_factory=list
    )
    
    error_handling_strategy: Dict[str, Any] = Field(
        description="Error handling patterns and exception types",
        default_factory=dict
    )


class SelfContainedSubtask(BaseModel):
    """Self-contained subtask with all necessary context."""
    
    subtask_id: str = Field(description="Unique subtask identifier")
    title: str = Field(description="Human-readable subtask title")
    location: str = Field(description="File or directory location")
    operation: str = Field(description="CREATE, MODIFY, or DELETE")
    
    context_bundle: Dict[str, Any] = Field(
        description="Complete context bundle - no external dependencies",
        default_factory=dict
    )
    
    specification: Dict[str, Any] = Field(
        description="Detailed specifications for implementation",
        default_factory=dict
    )
    
    testing: Dict[str, Any] = Field(
        description="Testing requirements and verification steps",
        default_factory=dict
    )
    
    acceptance_criteria: List[str] = Field(
        description="Success criteria for this subtask",
        default_factory=list
    )
    
    dependencies: List[str] = Field(
        description="Should be empty for true independence",
        default_factory=list
    )


class ImplementationPlanArtifact(BaseModel):
    """Detailed implementation plan with self-contained subtasks from IMPLEMENTATION_PLAN state."""
    
    file_operations: List[Dict[str, Any]] = Field(
        description="Exact file changes required",
        default_factory=list
    )
    
    subtasks: List[SelfContainedSubtask] = Field(
        description="Self-contained LOST subtasks",
        default_factory=list
    )
    
    test_plan: Dict[str, Any] = Field(
        description="Comprehensive testing strategy",
        default_factory=dict
    )
    
    implementation_notes: List[str] = Field(
        description="Additional implementation guidance",
        default_factory=list
    )
    
    dependency_order: List[str] = Field(
        description="Suggested order for subtask execution (though they should be independent)",
        default_factory=list
    )


class ValidationArtifact(BaseModel):
    """Final plan validation and coherence check from VALIDATION state."""
    
    plan_summary: Dict[str, Any] = Field(
        description="High-level plan summary statistics",
        default_factory=dict
    )
    
    requirement_coverage: List[Dict[str, Any]] = Field(
        description="How each requirement is addressed",
        default_factory=list
    )
    
    risk_assessment: List[Dict[str, Any]] = Field(
        description="Identified risks and mitigations",
        default_factory=list
    )
    
    subtask_independence_check: List[Dict[str, Any]] = Field(
        description="Verification of subtask independence",
        default_factory=list
    )
    
    final_approval_status: str = Field(
        description="APPROVED, NEEDS_REVISION, or REJECTED",
        default="PENDING"
    )
```

### 1.3 Context Loader Function  
**File**: `src/alfred/core/discovery_context.py`

```python
"""Pure function context loaders for discovery planning."""

from typing import Any, Dict
from src.alfred.models.schemas import Task, TaskState


def load_plan_task_context(task: Task, task_state: TaskState) -> Dict[str, Any]:
    """Pure function context loader for plan_task tool.
    
    Args:
        task: The task being planned
        task_state: Current task state with artifacts and context
        
    Returns:
        Context dictionary for prompt template rendering
        
    Raises:
        ValueError: If required dependencies are missing
    """
    # Check for re-planning context
    restart_context = task_state.context_store.get("restart_context")
    
    # Base context for all planning states
    context = {
        "task_title": task.title or "Untitled Task",
        "task_context": task.context or "",
        "implementation_details": task.implementation_details or "",
        "acceptance_criteria": task.acceptance_criteria or [],
        "restart_context": restart_context,
        "preserved_artifacts": task_state.context_store.get("preserved_artifacts", [])
    }
    
    # Add state-specific context
    current_state = getattr(task_state, 'current_state', None)
    if current_state:
        context["current_state"] = current_state
        
        # Add artifacts from previous states
        if current_state != "discovery":
            discovery_artifact = task_state.get_artifact("discovery")
            if discovery_artifact:
                context["discovery_artifact"] = discovery_artifact
                
        if current_state in ["contracts", "implementation_plan", "validation"]:
            clarification_artifact = task_state.get_artifact("clarification")
            if clarification_artifact:
                context["clarification_artifact"] = clarification_artifact
                
        if current_state in ["implementation_plan", "validation"]:
            contracts_artifact = task_state.get_artifact("contracts")
            if contracts_artifact:
                context["contracts_artifact"] = contracts_artifact
                
        if current_state == "validation":
            implementation_artifact = task_state.get_artifact("implementation_plan")
            if implementation_artifact:
                context["implementation_artifact"] = implementation_artifact
    
    return context


def load_simple_task_context(task: Task, task_state: TaskState) -> Dict[str, Any]:
    """Context loader for simple tasks that skip CONTRACTS state."""
    context = load_plan_task_context(task, task_state)
    context["skip_contracts"] = True
    return context
```

---

## 2. FILES TO MODIFY

### 2.1 Update Tool Configuration
**File**: `src/alfred/tools/tool_definitions.py`

**Add/Replace**:
```python
# Replace existing plan_task configuration
PLAN_TASK_TOOL = ToolDefinition(
    name="plan_task",
    description="""
    Interactive planning with deep context discovery and conversational clarification.
    
    This tool implements a comprehensive planning workflow that mirrors how expert developers 
    actually approach complex tasks:
    
    1. DISCOVERY: Deep context gathering using all available tools in parallel
    2. CLARIFICATION: Conversational Q&A to resolve ambiguities  
    3. CONTRACTS: Interface-first design of all APIs and data models
    4. IMPLEMENTATION_PLAN: Self-contained subtask creation with full context
    5. VALIDATION: Final coherence check and human approval
    
    Features:
    - Context saturation before planning begins
    - Real human-AI conversation for ambiguity resolution
    - Contract-first design approach
    - Self-contained subtasks with no rediscovery needed
    - Re-planning support for changing requirements
    - Complexity adaptation (can skip contracts for simple tasks)
    """,
    parameters={
        "task_id": {
            "type": "string",
            "description": "The unique identifier for the task to plan"
        },
        "restart_context": {
            "type": "object", 
            "description": "Optional context for re-planning scenarios",
            "required": False
        }
    }
)
```

### 2.2 Update Workflow Configuration
**File**: `src/alfred/core/workflow_config.py`

**Add/Replace**:
```python
from src.alfred.core.discovery_context import load_plan_task_context
from src.alfred.core.discovery_workflow import PlanTaskTool

# Replace existing plan_task configuration
"plan_task": WorkflowToolConfig(
    tool_name="plan_task",
    tool_class=PlanTaskTool,
    required_status=[TaskStatus.NEW, TaskStatus.PLANNING],
    entry_status_map={
        TaskStatus.NEW: TaskStatus.PLANNING,
        TaskStatus.PLANNING: TaskStatus.PLANNING  # Allow re-planning
    },
    dispatch_on_init=True,
    dispatch_state_attr="state",
    target_state_method="dispatch",
    context_loader=load_plan_task_context,
    requires_artifact_from=None  # No dependencies
)
```

### 2.3 Update Main Workflow File
**File**: `src/alfred/core/workflow.py`

**Remove**:
```python
# Remove old PlanTaskTool class (lines ~106-127)
# Remove old PlanTaskState enum (lines ~27-33)
```

**Add**:
```python
# Import new discovery workflow
from src.alfred.core.discovery_workflow import PlanTaskTool, PlanTaskState
```

### 2.4 Update Artifact Imports
**File**: `src/alfred/models/planning_artifacts.py`

**Add**:
```python
# Add imports for new discovery artifacts
from src.alfred.models.discovery_artifacts import (
    ContextDiscoveryArtifact,
    ClarificationArtifact,
    ContractDesignArtifact,
    ImplementationPlanArtifact,
    ValidationArtifact,
    SelfContainedSubtask,
)
```

### 2.5 Update Tool Implementation
**File**: `src/alfred/tools/plan_task.py`

**Replace entire content**:
```python
"""Discovery planning tool implementation."""

from typing import Optional, Dict, Any
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.tool_factory import get_tool_handler
from src.alfred.constants import ToolName


async def plan_task_impl(task_id: str, restart_context: Optional[Dict[str, Any]] = None) -> ToolResponse:
    """Implementation logic for the discovery planning tool.
    
    Args:
        task_id: The unique identifier for the task to plan
        restart_context: Optional context for re-planning scenarios
        
    Returns:
        ToolResponse with next action guidance
    """
    # Get the handler from factory (uses GenericWorkflowHandler)
    handler = get_tool_handler(ToolName.PLAN_TASK)
    
    # Execute with restart context if provided
    if restart_context:
        return await handler.execute(task_id=task_id, restart_context=restart_context)
    else:
        return await handler.execute(task_id=task_id)
```

---

## 3. TEMPLATE FILES TO CREATE

### Template Directory Structure
```
src/alfred/templates/prompts/plan_task/
├── discovery.md
├── clarification.md  
├── contracts.md
├── implementation_plan.md
└── validation.md
```

### 3.1 Discovery Template
**File**: `src/alfred/templates/prompts/plan_task/discovery.md`

```markdown
<!--
Template: plan_task.discovery
Purpose: Deep context discovery and codebase exploration
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - restart_context: Re-planning context (if any)
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Perform comprehensive context discovery by exploring the codebase in parallel using all available tools to build deep understanding before planning begins.

# BACKGROUND
You are beginning the discovery phase of planning. This is the foundation phase where you must:
- Use multiple tools simultaneously (Glob, Grep, Read, Task) for parallel exploration
- Understand existing patterns, architectures, and conventions
- Identify all files and components that will be affected
- Discover integration points and dependencies
- Collect ambiguities for later clarification (don't ask questions yet)
- Extract code snippets and context that will be needed for self-contained subtasks

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. **Parallel Exploration**: Use Glob, Grep, Read, and Task tools simultaneously to explore the codebase
2. **Pattern Recognition**: Identify existing coding patterns, architectural decisions, and conventions to follow
3. **Impact Analysis**: Map out all files, classes, and methods that will be affected by this task
4. **Dependency Mapping**: Understand how the new functionality will integrate with existing code
5. **Context Extraction**: Gather code snippets, method signatures, and examples that subtasks will need
6. **Ambiguity Collection**: Note questions and unclear requirements (don't ask yet - just collect)
7. **Complexity Assessment**: Determine if this is LOW/MEDIUM/HIGH complexity based on scope

# CONSTRAINTS
- Use multiple tools in parallel for maximum efficiency
- Focus on understanding, not designing solutions yet
- Collect ambiguities for later clarification phase
- Extract sufficient context for completely self-contained subtasks
- Follow existing codebase patterns and conventions

# OUTPUT
Create a ContextDiscoveryArtifact with:
- `codebase_understanding`: Your deep understanding of relevant code and integration points
- `ambiguities_discovered`: Specific questions that need human clarification (with context)
- `extracted_context`: Code snippets, patterns, and context for subtask inclusion
- `complexity_assessment`: LOW/MEDIUM/HIGH based on scope and impact
- `relevant_files`: List of files that will be affected
- `integration_points`: How this will connect to existing systems

**Required Action:** Call `alfred.submit_work` with a `ContextDiscoveryArtifact`

# EXAMPLES
Good context extraction: Include method signatures, error handling patterns, test examples, and integration code that subtasks will need to follow existing patterns.

Good ambiguity: "The task mentions 'authentication updates' but there are two auth systems (OAuth2Service for APIs, LegacyAuthService for web). Which should be the focus?"

Bad ambiguity: "How should I implement this?" (too vague, no context provided)
```

### 3.2 Clarification Template  
**File**: `src/alfred/templates/prompts/plan_task/clarification.md`

```markdown
<!--
Template: plan_task.clarification
Purpose: Conversational clarification of discovered ambiguities
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - discovery_artifact: Results from discovery phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Engage in conversational clarification with the human to resolve all discovered ambiguities and gain domain knowledge not available in training data.

# BACKGROUND
Context discovery has been completed and ambiguities have been identified. Now you must engage in real conversation with the human to:
- Resolve all discovered ambiguities with their domain expertise
- Understand business context and decisions not captured in code
- Clarify requirements and expectations
- Gain domain knowledge that will inform the design

This is a CONVERSATIONAL phase - engage in natural dialogue, ask follow-up questions, and seek clarification until all ambiguities are resolved.

**Discovery Results:**
- Complexity: ${discovery_artifact.complexity_assessment}
- Files Affected: ${discovery_artifact.relevant_files}
- Ambiguities Found: ${discovery_artifact.ambiguities_discovered}

${feedback_section}

# INSTRUCTIONS
1. **Present Ambiguities**: Show each discovered ambiguity with full context from your exploration
2. **Conversational Dialogue**: Engage in natural conversation - ask follow-ups, seek examples, clarify nuances
3. **Domain Knowledge Transfer**: Learn from human expertise about business logic, edge cases, and decisions
4. **Requirement Refinement**: Update and clarify requirements based on conversation
5. **Question Everything Unclear**: Don't make assumptions - if something is unclear, ask
6. **Document Conversation**: Keep track of what you learn for future reference

# CONSTRAINTS
- This is conversational, not just Q&A - engage naturally
- Focus on resolving ambiguities that impact design decisions
- Don't ask implementation details - focus on requirements and approach
- Seek domain knowledge that's not available in the codebase
- Be specific with your questions and provide context

# OUTPUT
Create a ClarificationArtifact with:
- `resolved_ambiguities`: Each question and its resolution with context
- `updated_requirements`: Requirements refined based on clarifications
- `domain_knowledge_gained`: Key insights provided by human expertise
- `conversation_log`: Record of the clarification dialogue

**Required Action:** Call `alfred.submit_work` with a `ClarificationArtifact`

# EXAMPLES
Good conversation starter: "I found two authentication systems in your codebase. The OAuth2Service handles JWT tokens for API endpoints, while LegacyAuthService manages sessions for web interface. Your task mentions 'authentication updates' - which system should I focus on, or do you want both updated?"

Good follow-up: "You mentioned OAuth2Service should be the focus. I see it currently supports Google and GitHub providers. Are you looking to add new providers, modify existing flows, or enhance security features?"

Bad question: "How should I implement authentication?" (too vague, no context)
```

### 3.3 Contracts Template
**File**: `src/alfred/templates/prompts/plan_task/contracts.md`

```markdown
<!--
Template: plan_task.contracts
Purpose: Interface-first design of all APIs and contracts
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Design all interfaces, method signatures, data models, and contracts before any implementation details. This is contract-first design.

# BACKGROUND
Context has been discovered and ambiguities resolved. Now you must design the complete interface layer:
- Method signatures with exact parameters and return types
- Data models with validation and relationships
- API contracts for external interfaces
- Integration contracts for component interactions
- Error handling strategies and exception types

This is ARCHITECTURAL design - focus on WHAT interfaces exist and HOW they interact, not implementation details.

**Previous Phase Results:**
- Discovery: ${discovery_artifact}
- Clarifications: ${clarification_artifact}

${feedback_section}

# INSTRUCTIONS
1. **Method Contract Design**: Define all new methods with exact signatures, parameters, return types, and error conditions
2. **Data Model Specification**: Create or update data structures, validation rules, and relationships
3. **API Contract Definition**: Specify external interfaces, request/response schemas, and error responses
4. **Integration Contracts**: Define how components will interact, dependencies, and communication patterns
5. **Error Handling Strategy**: Design exception types, error codes, and recovery patterns
6. **Testing Interface Design**: Consider how each contract will be tested and validated

# CONSTRAINTS
- Focus on interfaces and contracts, not implementation
- Follow existing patterns discovered in codebase exploration
- Ensure all contracts are testable and verifiable
- Consider error cases and edge conditions
- Design for the requirements clarified in previous phase

# OUTPUT
Create a ContractDesignArtifact with:
- `method_contracts`: All method signatures with specifications
- `data_models`: Data structure definitions and validation rules
- `api_contracts`: External interface specifications
- `integration_contracts`: Component interaction specifications
- `error_handling_strategy`: Exception types and error patterns

**Required Action:** Call `alfred.submit_work` with a `ContractDesignArtifact`

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

### 3.4 Implementation Plan Template
**File**: `src/alfred/templates/prompts/plan_task/implementation_plan.md`

```markdown
<!--
Template: plan_task.implementation_plan
Purpose: Create detailed implementation plan with self-contained subtasks
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - contracts_artifact: Results from contracts phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Create a detailed implementation plan with completely self-contained subtasks that include all necessary context and can execute independently.

# BACKGROUND
All design work is complete. Now you must create the implementation roadmap:
- Exact file operations (create/modify/delete)
- Self-contained subtasks with complete context bundles
- Comprehensive test plan integrated with implementation
- Implementation notes and guidance

Each subtask must be COMPLETELY SELF-CONTAINED - include all code snippets, patterns, examples, and context needed so no additional discovery is required.

**Previous Phase Results:**
- Discovery: ${discovery_artifact}
- Clarifications: ${clarification_artifact}
- Contracts: ${contracts_artifact}

${feedback_section}

# INSTRUCTIONS
1. **File-Level Planning**: Specify exactly which files to create/modify/delete
2. **Self-Contained Subtask Creation**: Each subtask must include complete context bundle with:
   - Existing code snippets from affected files
   - Related code patterns from other files
   - Data models and utility functions needed
   - Testing patterns and examples
   - Error handling patterns from codebase
3. **Test Strategy Integration**: Plan unit tests, integration tests, and validation approaches
4. **Implementation Sequencing**: Consider order dependencies (though subtasks should be independent)
5. **Context Bundling**: Ensure each subtask has everything needed without external lookups

# CONSTRAINTS
- Subtasks must be truly independent and self-contained
- Include sufficient context for any developer to execute
- Follow LOST framework (Location, Operation, Specification, Test)
- Base implementation on approved contracts from previous phase
- Ensure subtasks can be assigned to different developers/agents

# OUTPUT
Create an ImplementationPlanArtifact with:
- `file_operations`: Exact file changes with current content and modifications
- `subtasks`: List of SelfContainedSubtask objects with complete context bundles
- `test_plan`: Comprehensive testing strategy for all components
- `implementation_notes`: Additional guidance and considerations
- `dependency_order`: Suggested execution sequence (though subtasks should be independent)

**Required Action:** Call `alfred.submit_work` with an `ImplementationPlanArtifact`

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

### 3.5 Validation Template
**File**: `src/alfred/templates/prompts/plan_task/validation.md`

```markdown
<!--
Template: plan_task.validation
Purpose: Final plan validation and coherence check
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - contracts_artifact: Results from contracts phase
  - implementation_artifact: Results from implementation planning phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Perform final validation that the complete plan works cohesively and will successfully achieve all requirements.

# BACKGROUND
All planning phases are complete. Now you must validate the entire plan end-to-end:
- Does the plan achieve all acceptance criteria?
- Are all components consistent and coherent?
- Are subtasks truly independent and complete?
- What are the risks and how can they be mitigated?
- Is the human ready to approve this plan?

This is the final quality gate before implementation begins.

**Complete Plan:**
- Discovery: ${discovery_artifact}
- Clarifications: ${clarification_artifact}
- Contracts: ${contracts_artifact}
- Implementation: ${implementation_artifact}

${feedback_section}

# INSTRUCTIONS
1. **End-to-End Validation**: Review the complete plan from discovery through implementation
2. **Requirement Coverage**: Verify every acceptance criterion is addressed in the plan
3. **Contract Consistency**: Ensure all pieces fit together and interfaces align
4. **Subtask Independence**: Validate that subtasks are truly self-contained
5. **Risk Assessment**: Identify potential issues and mitigation strategies
6. **Completeness Check**: Ensure nothing critical is missing
7. **Plan Summary**: Create human-readable summary for approval

# CONSTRAINTS
- Be thorough but concise in validation
- Focus on coherence and completeness
- Identify real risks, not hypothetical concerns
- Ensure plan is ready for implementation
- Provide clear approval recommendation

# OUTPUT
Create a ValidationArtifact with:
- `plan_summary`: High-level statistics and overview
- `requirement_coverage`: How each acceptance criterion is addressed
- `risk_assessment`: Identified risks with probability, impact, and mitigation
- `subtask_independence_check`: Verification of subtask self-containment
- `final_approval_status`: APPROVED/NEEDS_REVISION/REJECTED with reasoning

**Required Action:** Call `alfred.submit_work` with a `ValidationArtifact`

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

Good independence check:
```
subtask_id: "ST-001"
is_independent: true
dependencies_found: []
```
```

---

## 4. FILES TO DEPRECATE (LATER)

After successful deployment, these files can be removed:

```
src/alfred/templates/prompts/plan_task/contextualize.md
src/alfred/templates/prompts/plan_task/strategize.md
src/alfred/templates/prompts/plan_task/design.md
src/alfred/templates/prompts/plan_task/generate_subtasks.md
```

---

## 5. IMPLEMENTATION SEQUENCE

### Phase 1: Foundation
1. Create `src/alfred/models/discovery_artifacts.py`
2. Create `src/alfred/core/discovery_context.py`
3. Update `src/alfred/models/planning_artifacts.py` (imports)

### Phase 2: State Machine
1. Create `src/alfred/core/discovery_workflow.py`
2. Update `src/alfred/core/workflow.py` (remove old, import new)

### Phase 3: Configuration
1. Update `src/alfred/core/workflow_config.py`
2. Update `src/alfred/tools/tool_definitions.py`
3. Update `src/alfred/tools/plan_task.py`

### Phase 4: Templates
1. Create all template files in `src/alfred/templates/prompts/plan_task/`
2. Test template rendering with sample data

### Phase 5: Testing
1. Create unit tests for new artifacts
2. Create integration tests for state machine
3. Create end-to-end workflow tests

---

## 6. VALIDATION CHECKLIST

Before deployment, verify:

- [ ] All new files created with exact content specified
- [ ] All modifications made to existing files
- [ ] State machine uses Pattern 1 with builder
- [ ] GenericWorkflowHandler used (no custom handlers)
- [ ] Templates follow strict section format
- [ ] Context loaders are pure functions
- [ ] Artifact models have proper validation
- [ ] Tool registration follows principles
- [ ] All tests pass
- [ ] No breaking changes to existing functionality

---

This file creation plan provides the complete blueprint for implementing the Discovery Planning system while maintaining full compliance with Alfred's architectural principles.