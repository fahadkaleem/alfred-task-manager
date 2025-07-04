# Discovery Planning Artifact Specifications
## Detailed Pydantic Model Definitions and Validation Rules

> **Author**: Claude Code (Sonnet 4)  
> **Date**: July 3, 2025  
> **Status**: Complete Specification  
> **Purpose**: Comprehensive artifact model definitions for discovery planning

---

## Overview

This document provides complete specifications for all Pydantic models used in the Discovery Planning system. Each artifact represents the output of a specific planning phase and includes detailed validation rules, field specifications, and usage examples.

---

## 1. ContextDiscoveryArtifact

### Purpose
Captures comprehensive context discovery results from the DISCOVERY phase, including codebase understanding, ambiguities, and extracted context for subtasks.

### Full Model Definition
```python
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class IntegrationType(str, Enum):
    API_ENDPOINT = "API_ENDPOINT"
    DATABASE = "DATABASE"
    SERVICE_CALL = "SERVICE_CALL"
    FILE_SYSTEM = "FILE_SYSTEM"
    EXTERNAL_API = "EXTERNAL_API"


class CodePattern(BaseModel):
    """Represents a discovered code pattern."""
    pattern_type: str = Field(description="Type of pattern (e.g., 'error_handling', 'service_pattern')")
    example_code: str = Field(description="Code snippet demonstrating the pattern")
    usage_context: str = Field(description="When and how this pattern is used")
    file_locations: List[str] = Field(description="Files where this pattern is found")


class IntegrationPoint(BaseModel):
    """Represents an integration point discovered in the codebase."""
    component_name: str = Field(description="Name of the component to integrate with")
    integration_type: IntegrationType = Field(description="Type of integration")
    interface_signature: str = Field(description="Method signature or API endpoint")
    dependencies: List[str] = Field(description="Required dependencies for integration")
    examples: List[str] = Field(description="Code examples of integration usage")


class AmbiguityItem(BaseModel):
    """Represents a discovered ambiguity that needs clarification."""
    question: str = Field(description="The specific question that needs answering")
    context: str = Field(description="Code or contextual information related to the ambiguity")
    impact_if_wrong: str = Field(description="What could go wrong if we guess incorrectly")
    discovery_source: str = Field(description="Where this ambiguity was discovered")
    
    @validator('question')
    def question_must_be_specific(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Question must be specific and detailed')
        if v.strip().endswith('?') is False:
            raise ValueError('Question must end with a question mark')
        return v.strip()


class ContextDiscoveryArtifact(BaseModel):
    """Comprehensive context discovery results from DISCOVERY state."""
    
    # Core understanding
    codebase_understanding: Dict[str, Any] = Field(
        description="Deep understanding of relevant codebase components",
        default_factory=dict
    )
    
    # Discovered patterns
    code_patterns: List[CodePattern] = Field(
        description="Discovered code patterns that should be followed",
        default_factory=list
    )
    
    # Integration analysis
    integration_points: List[IntegrationPoint] = Field(
        description="Integration points and dependencies discovered",
        default_factory=list
    )
    
    # Files and components
    relevant_files: List[str] = Field(
        description="Files that will be affected by this task",
        default_factory=list
    )
    
    existing_components: Dict[str, str] = Field(
        description="Existing components and their purposes",
        default_factory=dict
    )
    
    # Ambiguities for clarification
    ambiguities_discovered: List[AmbiguityItem] = Field(
        description="Specific ambiguities that need human clarification",
        default_factory=list
    )
    
    # Context for subtasks
    extracted_context: Dict[str, Any] = Field(
        description="Code snippets and context for subtask inclusion",
        default_factory=dict
    )
    
    # Assessment
    complexity_assessment: ComplexityLevel = Field(
        description="Overall complexity assessment",
        default=ComplexityLevel.MEDIUM
    )
    
    # Metadata
    discovery_notes: List[str] = Field(
        description="Additional notes from the discovery process",
        default_factory=list
    )
    
    @validator('relevant_files')
    def validate_file_paths(cls, v):
        for file_path in v:
            if not file_path.strip():
                raise ValueError('File paths cannot be empty')
            if not file_path.startswith(('src/', 'tests/', 'docs/')):
                # Allow flexibility but warn about unusual paths
                pass
        return v
    
    @validator('complexity_assessment')
    def validate_complexity_reasoning(cls, v, values):
        # Validate complexity assessment makes sense
        file_count = len(values.get('relevant_files', []))
        integration_count = len(values.get('integration_points', []))
        
        if v == ComplexityLevel.LOW and (file_count > 3 or integration_count > 1):
            raise ValueError('LOW complexity should affect <= 3 files and <= 1 integration point')
        
        return v
```

### Usage Example
```python
discovery_artifact = ContextDiscoveryArtifact(
    codebase_understanding={
        "architecture": "microservices with shared authentication",
        "testing_framework": "pytest with fixtures",
        "error_handling": "custom exception hierarchy"
    },
    code_patterns=[
        CodePattern(
            pattern_type="service_initialization",
            example_code="class UserService(BaseService): def __init__(self, db_client): super().__init__()",
            usage_context="All services inherit from BaseService and take dependencies in __init__",
            file_locations=["src/services/user_service.py", "src/services/auth_service.py"]
        )
    ],
    integration_points=[
        IntegrationPoint(
            component_name="DatabaseClient",
            integration_type=IntegrationType.DATABASE,
            interface_signature="async def execute_query(query: str, params: dict) -> List[dict]",
            dependencies=["asyncpg", "connection_pool"],
            examples=["await self.db.execute_query('SELECT * FROM users WHERE id = $1', {'id': user_id})"]
        )
    ],
    relevant_files=["src/services/auth_service.py", "src/models/user.py", "tests/test_auth.py"],
    ambiguities_discovered=[
        AmbiguityItem(
            question="Should the new OAuth provider integrate with existing UserService or create separate OAuthService?",
            context="Found both UserService (handles user management) and separate OAuth2Service (handles tokens)",
            impact_if_wrong="Could create duplicate user handling logic or break existing OAuth flows",
            discovery_source="File analysis of src/services/"
        )
    ],
    complexity_assessment=ComplexityLevel.MEDIUM
)
```

---

## 2. ClarificationArtifact

### Purpose
Captures the results of human-AI conversational clarification, including resolved ambiguities and gained domain knowledge.

### Full Model Definition
```python
class ConversationEntry(BaseModel):
    """Represents one exchange in the clarification conversation."""
    speaker: str = Field(description="'AI' or 'Human'")
    message: str = Field(description="The message content")
    timestamp: Optional[str] = Field(description="When this was said")
    
    @validator('speaker')
    def validate_speaker(cls, v):
        if v not in ['AI', 'Human']:
            raise ValueError('Speaker must be either "AI" or "Human"')
        return v


class ResolvedAmbiguity(BaseModel):
    """Represents a resolved ambiguity from the clarification process."""
    original_question: str = Field(description="The original question from discovery")
    human_response: str = Field(description="The human's response/guidance")
    clarification: str = Field(description="AI's understanding of the resolution")
    follow_up_questions: List[str] = Field(description="Any follow-up questions asked", default_factory=list)
    final_decision: str = Field(description="The final decision or direction")
    
    @validator('final_decision')
    def decision_must_be_actionable(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Final decision must be specific and actionable')
        return v.strip()


class RequirementUpdate(BaseModel):
    """Represents an update to requirements based on clarification."""
    original_requirement: str = Field(description="Original requirement text")
    updated_requirement: str = Field(description="Updated requirement after clarification")
    reason_for_change: str = Field(description="Why this change was needed")


class ClarificationArtifact(BaseModel):
    """Results of human-AI clarification dialogue from CLARIFICATION state."""
    
    # Resolved ambiguities
    resolved_ambiguities: List[ResolvedAmbiguity] = Field(
        description="All ambiguities and their resolutions",
        default_factory=list
    )
    
    # Updated requirements
    updated_requirements: List[RequirementUpdate] = Field(
        description="Requirements refined based on clarifications",
        default_factory=list
    )
    
    # Domain knowledge
    domain_knowledge_gained: List[str] = Field(
        description="Key domain insights provided by human expertise",
        default_factory=list
    )
    
    # Conversation log
    conversation_log: List[ConversationEntry] = Field(
        description="Complete log of the clarification conversation",
        default_factory=list
    )
    
    # Business context
    business_context: Dict[str, str] = Field(
        description="Business context and decisions that impact technical approach",
        default_factory=dict
    )
    
    # New constraints discovered
    additional_constraints: List[str] = Field(
        description="New constraints discovered during clarification",
        default_factory=list
    )
    
    @validator('resolved_ambiguities')
    def all_ambiguities_resolved(cls, v):
        for ambiguity in v:
            if not ambiguity.final_decision.strip():
                raise ValueError('All ambiguities must have final decisions')
        return v
```

### Usage Example
```python
clarification_artifact = ClarificationArtifact(
    resolved_ambiguities=[
        ResolvedAmbiguity(
            original_question="Should OAuth provider integrate with UserService or create separate OAuthService?",
            human_response="We want to keep OAuth separate because we're planning to migrate away from UserService to a microservices architecture next quarter",
            clarification="Create separate OAuthService that can work independently of UserService, with clean interfaces for future microservices migration",
            follow_up_questions=["Should the OAuthService still validate users against the current user database?"],
            final_decision="Create OAuthService with user validation interface that can be easily swapped during microservices migration"
        )
    ],
    updated_requirements=[
        RequirementUpdate(
            original_requirement="Add OAuth authentication support",
            updated_requirement="Add OAuth authentication support via standalone OAuthService with pluggable user validation",
            reason_for_change="Future microservices migration requires service isolation"
        )
    ],
    domain_knowledge_gained=[
        "Company is migrating to microservices architecture next quarter",
        "Current UserService is considered legacy and should not be extended",
        "OAuth integration needs to support eventual transition to separate user service"
    ],
    business_context={
        "migration_timeline": "Q2 2025 microservices migration planned",
        "legacy_system": "UserService will be deprecated",
        "architecture_direction": "Service isolation and clean interfaces"
    }
)
```

---

## 3. ContractDesignArtifact

### Purpose
Captures interface-first design specifications including method contracts, data models, and API definitions.

### Full Model Definition
```python
class MethodContract(BaseModel):
    """Represents a method contract specification."""
    class_name: str = Field(description="Name of the class containing this method")
    method_name: str = Field(description="Name of the method")
    signature: str = Field(description="Complete method signature with types")
    purpose: str = Field(description="What this method does")
    parameters: List[Dict[str, str]] = Field(description="Parameter details", default_factory=list)
    return_type: str = Field(description="Return type specification")
    error_handling: List[str] = Field(description="Exceptions that can be raised", default_factory=list)
    test_approach: str = Field(description="How this method will be tested")
    
    @validator('signature')
    def signature_has_types(cls, v):
        if '->' not in v:
            raise ValueError('Method signature must include return type annotation')
        return v


class DataModel(BaseModel):
    """Represents a data model specification."""
    name: str = Field(description="Model name")
    description: str = Field(description="What this model represents")
    fields: List[Dict[str, Any]] = Field(description="Field definitions")
    validation_rules: List[Dict[str, str]] = Field(description="Validation requirements", default_factory=list)
    relationships: List[Dict[str, str]] = Field(description="Relationships to other models", default_factory=list)
    example_data: Optional[Dict[str, Any]] = Field(description="Example instance data")


class APIContract(BaseModel):
    """Represents an API contract specification."""
    endpoint: str = Field(description="API endpoint path")
    method: str = Field(description="HTTP method")
    description: str = Field(description="What this endpoint does")
    request_schema: Dict[str, Any] = Field(description="Request body schema")
    response_schema: Dict[str, Any] = Field(description="Response body schema")
    error_responses: List[Dict[str, str]] = Field(description="Possible error responses", default_factory=list)
    authentication: str = Field(description="Authentication requirements")


class IntegrationContract(BaseModel):
    """Represents component integration specifications."""
    component: str = Field(description="Component name")
    interface: str = Field(description="Interface or protocol used")
    dependencies: List[str] = Field(description="Required dependencies")
    communication_pattern: str = Field(description="How components communicate")
    error_handling: str = Field(description="How errors are handled in integration")


class ContractDesignArtifact(BaseModel):
    """Interface-first design specifications from CONTRACTS state."""
    
    # Method specifications
    method_contracts: List[MethodContract] = Field(
        description="All method contracts and specifications",
        default_factory=list
    )
    
    # Data model specifications
    data_models: List[DataModel] = Field(
        description="Data structure definitions and validation rules",
        default_factory=list
    )
    
    # API specifications
    api_contracts: List[APIContract] = Field(
        description="External interface specifications",
        default_factory=list
    )
    
    # Integration specifications
    integration_contracts: List[IntegrationContract] = Field(
        description="Component interaction specifications",
        default_factory=list
    )
    
    # Error handling strategy
    error_handling_strategy: Dict[str, Any] = Field(
        description="Overall error handling patterns and exception types",
        default_factory=dict
    )
    
    # Design principles
    design_principles: List[str] = Field(
        description="Key design principles guiding this contract design",
        default_factory=list
    )
```

### Usage Example
```python
contract_artifact = ContractDesignArtifact(
    method_contracts=[
        MethodContract(
            class_name="OAuthService",
            method_name="authenticate",
            signature="async def authenticate(provider: str, code: str) -> AuthResult",
            purpose="Authenticate user via OAuth provider and return auth result",
            parameters=[
                {"name": "provider", "type": "str", "description": "OAuth provider name (google, github)"},
                {"name": "code", "type": "str", "description": "Authorization code from OAuth callback"}
            ],
            return_type="AuthResult",
            error_handling=["ValidationError for invalid provider", "OAuthError for failed authentication"],
            test_approach="Mock OAuth provider responses, test with valid/invalid codes"
        )
    ],
    data_models=[
        DataModel(
            name="AuthResult",
            description="Result of authentication operation",
            fields=[
                {"name": "user_id", "type": "str", "required": True, "description": "Unique user identifier"},
                {"name": "access_token", "type": "str", "required": True, "description": "JWT access token"},
                {"name": "refresh_token", "type": "str", "required": False, "description": "Optional refresh token"}
            ],
            validation_rules=[
                {"field": "access_token", "rule": "Must be valid JWT format"},
                {"field": "user_id", "rule": "Must be non-empty string"}
            ]
        )
    ],
    error_handling_strategy={
        "base_exception": "OAuthServiceError",
        "specific_exceptions": ["ValidationError", "OAuthError", "UserNotFoundError"],
        "error_response_format": {"error": "error_code", "message": "human_readable_message"}
    }
)
```

---

## 4. ImplementationPlanArtifact & SelfContainedSubtask

### Purpose
Captures detailed implementation plan with completely self-contained subtasks that include all necessary context.

### Full Model Definition
```python
class FileOperation(BaseModel):
    """Represents a file operation in the implementation plan."""
    file_path: str = Field(description="Absolute path to the file")
    operation: str = Field(description="CREATE, MODIFY, or DELETE")
    existing_content: Optional[str] = Field(description="Current file content (for MODIFY)")
    changes_description: str = Field(description="Description of changes to make")
    affected_methods: List[str] = Field(description="Methods that will be added/modified", default_factory=list)
    
    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['CREATE', 'MODIFY', 'DELETE']:
            raise ValueError('Operation must be CREATE, MODIFY, or DELETE')
        return v


class ContextBundle(BaseModel):
    """Complete context bundle for a subtask - no external dependencies needed."""
    existing_code: str = Field(description="Current file content where work will be done")
    related_code_snippets: Dict[str, str] = Field(description="Code snippets from other files needed as examples")
    data_models: List[str] = Field(description="Data model definitions needed", default_factory=list)
    utility_functions: List[str] = Field(description="Utility functions available", default_factory=list)
    testing_patterns: str = Field(description="How to write tests in this codebase")
    error_handling_patterns: str = Field(description="How errors are handled in this codebase")
    dependencies_available: List[str] = Field(description="Available imports and dependencies", default_factory=list)


class MethodImplementation(BaseModel):
    """Specification for implementing a method."""
    method_name: str = Field(description="Name of the method to implement")
    signature: str = Field(description="Complete method signature")
    implementation_approach: str = Field(description="High-level approach for implementation")
    edge_cases: List[str] = Field(description="Edge cases to handle", default_factory=list)
    integration_points: List[str] = Field(description="How this integrates with other code", default_factory=list)


class TestingRequirements(BaseModel):
    """Testing requirements for a subtask."""
    unit_tests_to_create: List[str] = Field(description="Unit tests that need to be created", default_factory=list)
    test_data: List[Dict[str, Any]] = Field(description="Test data needed", default_factory=list)
    verification_steps: List[str] = Field(description="Manual verification steps", default_factory=list)
    expected_outcomes: List[str] = Field(description="Expected test outcomes", default_factory=list)


class SelfContainedSubtask(BaseModel):
    """Self-contained subtask with all necessary context - LOST framework implementation."""
    
    # Basic identification
    subtask_id: str = Field(description="Unique subtask identifier")
    title: str = Field(description="Human-readable subtask title")
    
    # LOST Framework fields
    location: str = Field(description="File or directory location (L)")
    operation: str = Field(description="CREATE, MODIFY, or DELETE (O)")
    
    # Complete context bundle - no external dependencies
    context_bundle: ContextBundle = Field(description="Complete context - no external dependencies needed")
    
    # Detailed specifications (S)
    specification: Dict[str, Any] = Field(
        description="Detailed specifications for implementation",
        default_factory=dict
    )
    
    # Testing requirements (T)
    testing: TestingRequirements = Field(description="Testing requirements and verification")
    
    # Success criteria
    acceptance_criteria: List[str] = Field(
        description="Success criteria for this subtask",
        default_factory=list
    )
    
    # Should be empty for true independence
    dependencies: List[str] = Field(
        description="Should be empty for true independence",
        default_factory=list
    )
    
    @validator('dependencies')
    def validate_independence(cls, v):
        if v:
            raise ValueError('Subtask should be independent - dependencies list should be empty')
        return v
    
    @validator('operation')
    def validate_operation_type(cls, v):
        if v not in ['CREATE', 'MODIFY', 'DELETE']:
            raise ValueError('Operation must be CREATE, MODIFY, or DELETE')
        return v


class TestPlan(BaseModel):
    """Comprehensive testing strategy."""
    unit_tests: List[Dict[str, str]] = Field(description="Unit test specifications", default_factory=list)
    integration_tests: List[Dict[str, str]] = Field(description="Integration test specifications", default_factory=list)
    test_data_requirements: List[Dict[str, Any]] = Field(description="Test data needed", default_factory=list)
    coverage_requirements: Dict[str, Any] = Field(description="Coverage expectations", default_factory=dict)


class ImplementationPlanArtifact(BaseModel):
    """Detailed implementation plan with self-contained subtasks from IMPLEMENTATION_PLAN state."""
    
    # File-level operations
    file_operations: List[FileOperation] = Field(
        description="Exact file changes required",
        default_factory=list
    )
    
    # Self-contained subtasks
    subtasks: List[SelfContainedSubtask] = Field(
        description="Self-contained LOST subtasks",
        default_factory=list
    )
    
    # Testing strategy
    test_plan: TestPlan = Field(description="Comprehensive testing strategy")
    
    # Additional guidance
    implementation_notes: List[str] = Field(
        description="Additional implementation guidance",
        default_factory=list
    )
    
    # Suggested order (though subtasks should be independent)
    dependency_order: List[str] = Field(
        description="Suggested order for subtask execution",
        default_factory=list
    )
    
    @validator('subtasks')
    def validate_subtask_independence(cls, v):
        for subtask in v:
            if subtask.dependencies:
                raise ValueError(f'Subtask {subtask.subtask_id} has dependencies - should be independent')
        return v
```

### Usage Example
```python
implementation_artifact = ImplementationPlanArtifact(
    file_operations=[
        FileOperation(
            file_path="src/services/oauth_service.py",
            operation="CREATE",
            changes_description="Create new OAuthService class with authenticate method",
            affected_methods=["authenticate", "__init__"]
        )
    ],
    subtasks=[
        SelfContainedSubtask(
            subtask_id="ST-001",
            title="Create OAuthService.authenticate method",
            location="src/services/oauth_service.py",
            operation="CREATE",
            context_bundle=ContextBundle(
                existing_code="# Empty file - creating new service",
                related_code_snippets={
                    "base_service_pattern": "class UserService(BaseService):\n    def __init__(self, db_client):\n        super().__init__()\n        self.db = db_client",
                    "error_handling_pattern": "try:\n    result = await operation()\nexcept ValidationError as e:\n    logger.error(f'Validation failed: {e}')\n    raise"
                },
                data_models=["AuthResult", "User"],
                testing_patterns="Use pytest with async fixtures, mock external dependencies",
                error_handling_patterns="Raise specific exceptions, log errors, return error responses"
            ),
            specification={
                "exact_changes": [
                    "Create OAuthService class inheriting from BaseService",
                    "Implement async authenticate method with provider and code parameters",
                    "Add error handling for invalid providers and failed authentication"
                ],
                "method_implementations": [
                    MethodImplementation(
                        method_name="authenticate",
                        signature="async def authenticate(self, provider: str, code: str) -> AuthResult",
                        implementation_approach="Validate provider, exchange code for token, validate user, return AuthResult",
                        edge_cases=["Invalid provider", "Expired code", "User not found"]
                    )
                ]
            },
            testing=TestingRequirements(
                unit_tests_to_create=["test_authenticate_success", "test_authenticate_invalid_provider"],
                verification_steps=["Method exists with correct signature", "Returns AuthResult on success"],
                expected_outcomes=["All tests pass", "Method integrates with existing auth flow"]
            ),
            acceptance_criteria=[
                "OAuthService class created with authenticate method",
                "Method handles google and github providers",
                "Proper error handling for invalid inputs",
                "Unit tests pass with 100% coverage"
            ]
        )
    ],
    test_plan=TestPlan(
        unit_tests=[
            {"name": "test_oauth_service_authenticate", "description": "Test OAuth authentication flow"}
        ],
        integration_tests=[
            {"name": "test_oauth_integration", "description": "Test OAuth service integration with auth system"}
        ]
    )
)
```

---

## 5. ValidationArtifact

### Purpose
Captures final plan validation and coherence check before implementation begins.

### Full Model Definition
```python
class PlanSummary(BaseModel):
    """High-level summary of the implementation plan."""
    files_affected: int = Field(description="Number of files that will be modified")
    methods_created: int = Field(description="Number of new methods to create")
    methods_modified: int = Field(description="Number of existing methods to modify")
    tests_planned: int = Field(description="Number of tests planned")
    estimated_complexity: ComplexityLevel = Field(description="Overall complexity assessment")
    estimated_effort_hours: Optional[int] = Field(description="Estimated implementation effort in hours")


class RequirementCoverage(BaseModel):
    """How a specific requirement is addressed in the plan."""
    requirement: str = Field(description="The original requirement")
    implementation_approach: str = Field(description="How the plan addresses this requirement")
    coverage_confidence: float = Field(description="Confidence that this requirement will be met (0-1)")
    implementation_location: str = Field(description="Where in the plan this is implemented")
    
    @validator('coverage_confidence')
    def confidence_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Coverage confidence must be between 0 and 1')
        return v


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"


class RiskAssessment(BaseModel):
    """Assessment of a potential risk in the implementation plan."""
    risk: str = Field(description="Description of the risk")
    probability: RiskLevel = Field(description="Likelihood of this risk occurring")
    impact: RiskLevel = Field(description="Impact if this risk occurs")
    mitigation: str = Field(description="How to mitigate or handle this risk")
    contingency_plan: Optional[str] = Field(description="Backup plan if mitigation fails")


class SubtaskIndependenceCheck(BaseModel):
    """Verification that a subtask is truly independent."""
    subtask_id: str = Field(description="ID of the subtask being checked")
    is_independent: bool = Field(description="Whether the subtask is truly independent")
    dependencies_found: List[str] = Field(description="Any dependencies discovered", default_factory=list)
    context_completeness: float = Field(description="How complete the context bundle is (0-1)")
    
    @validator('is_independent')
    def validate_independence_consistency(cls, v, values):
        dependencies = values.get('dependencies_found', [])
        if v and dependencies:
            raise ValueError('Subtask cannot be independent if dependencies are found')
        if not v and not dependencies:
            raise ValueError('If subtask is not independent, dependencies must be specified')
        return v


class ValidationArtifact(BaseModel):
    """Final plan validation and coherence check from VALIDATION state."""
    
    # Plan overview
    plan_summary: PlanSummary = Field(description="High-level plan summary and statistics")
    
    # Requirement coverage
    requirement_coverage: List[RequirementCoverage] = Field(
        description="How each requirement is addressed in the plan",
        default_factory=list
    )
    
    # Risk analysis
    risk_assessment: List[RiskAssessment] = Field(
        description="Identified risks with probability, impact, and mitigation",
        default_factory=list
    )
    
    # Subtask validation
    subtask_independence_check: List[SubtaskIndependenceCheck] = Field(
        description="Verification of subtask independence and completeness",
        default_factory=list
    )
    
    # Overall assessment
    final_approval_status: str = Field(
        description="APPROVED, NEEDS_REVISION, or REJECTED",
        default="PENDING"
    )
    
    approval_reasoning: str = Field(
        description="Reasoning for the approval status",
        default=""
    )
    
    # Quality metrics
    quality_metrics: Dict[str, float] = Field(
        description="Quality scores for various aspects (0-1)",
        default_factory=dict
    )
    
    @validator('final_approval_status')
    def validate_approval_status(cls, v):
        if v not in ['APPROVED', 'NEEDS_REVISION', 'REJECTED', 'PENDING']:
            raise ValueError('Approval status must be APPROVED, NEEDS_REVISION, REJECTED, or PENDING')
        return v
    
    @validator('requirement_coverage')
    def validate_complete_coverage(cls, v):
        # Ensure all requirements have reasonable confidence
        for coverage in v:
            if coverage.coverage_confidence < 0.7:
                # Warning: low confidence in requirement coverage
                pass
        return v
```

### Usage Example
```python
validation_artifact = ValidationArtifact(
    plan_summary=PlanSummary(
        files_affected=3,
        methods_created=5,
        methods_modified=2,
        tests_planned=12,
        estimated_complexity=ComplexityLevel.MEDIUM,
        estimated_effort_hours=16
    ),
    requirement_coverage=[
        RequirementCoverage(
            requirement="Add OAuth authentication support",
            implementation_approach="OAuthService with authenticate method supporting google/github providers",
            coverage_confidence=0.95,
            implementation_location="ST-001: Create OAuthService.authenticate method"
        )
    ],
    risk_assessment=[
        RiskAssessment(
            risk="OAuth provider API changes could break authentication",
            probability=RiskLevel.MEDIUM,
            impact=RiskLevel.HIGH,
            mitigation="Comprehensive integration tests with provider APIs, error handling for API failures",
            contingency_plan="Fallback to existing authentication until provider APIs stabilized"
        )
    ],
    subtask_independence_check=[
        SubtaskIndependenceCheck(
            subtask_id="ST-001",
            is_independent=True,
            dependencies_found=[],
            context_completeness=0.9
        )
    ],
    final_approval_status="APPROVED",
    approval_reasoning="Plan comprehensively addresses all requirements with good risk mitigation and independent subtasks",
    quality_metrics={
        "requirement_coverage": 0.95,
        "subtask_independence": 0.9,
        "risk_mitigation": 0.85,
        "implementation_detail": 0.9
    }
)
```

---

## 6. Validation Rules Summary

### Cross-Artifact Validation
1. **Consistency**: Artifacts must be consistent with each other
2. **Completeness**: Later artifacts must address all items from earlier artifacts
3. **Traceability**: Requirements must be traceable through all artifacts

### Quality Gates
1. **Discovery**: Must identify all ambiguities and extract sufficient context
2. **Clarification**: Must resolve all discovered ambiguities
3. **Contracts**: Must define complete interfaces for all planned functionality
4. **Implementation**: Must create truly independent, self-contained subtasks
5. **Validation**: Must verify plan coherence and readiness for implementation

### Independence Requirements
- Subtasks must have no dependencies on each other
- Context bundles must include all necessary code snippets and patterns
- Each subtask must be assignable to different developers/agents

This comprehensive artifact specification ensures all Discovery Planning data models are robust, validated, and support the complete workflow from discovery through implementation.