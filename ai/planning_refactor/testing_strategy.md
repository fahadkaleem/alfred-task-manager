# Discovery Planning Testing Strategy
## Comprehensive Testing Approach for New Planning System

> **Author**: Claude Code (Sonnet 4)  
> **Date**: July 3, 2025  
> **Status**: Complete Testing Strategy  
> **Purpose**: Ensure Discovery Planning system quality and reliability

---

## Overview

This document provides a comprehensive testing strategy for the Discovery Planning system implementation. The strategy covers unit tests, integration tests, end-to-end workflows, and validation of all architectural principles compliance.

---

## 1. Testing Philosophy

### Core Principles
1. **Test Behavior, Not Implementation**: Focus on outcomes and contracts, not internal mechanics
2. **State Machine Validation**: Ensure FSM transitions work correctly per builder patterns
3. **Artifact Quality Assurance**: Validate all Pydantic models and their constraints
4. **Template Compliance**: Verify all templates follow architectural principles
5. **End-to-End Workflow**: Test complete planning flows from discovery to validation

### Testing Pyramid Structure
```
                   /\
                  /  \
                 / E2E \
                /______\
               /        \
              /Integration\
             /____________\
            /              \
           /  Unit Tests     \
          /__________________\
```

---

## 2. Unit Testing Strategy

### 2.1 Artifact Model Testing

#### Test Coverage
- **Pydantic validation rules**
- **Field constraints and relationships**
- **Custom validators**
- **Serialization/deserialization**

#### Test Structure
```python
# tests/unit/models/test_discovery_artifacts.py

import pytest
from pydantic import ValidationError
from src.alfred.models.discovery_artifacts import (
    ContextDiscoveryArtifact,
    ClarificationArtifact,
    ContractDesignArtifact,
    ImplementationPlanArtifact,
    SelfContainedSubtask,
    ValidationArtifact
)


class TestContextDiscoveryArtifact:
    """Test suite for ContextDiscoveryArtifact validation."""
    
    def test_valid_artifact_creation(self):
        """Test creating valid ContextDiscoveryArtifact."""
        artifact = ContextDiscoveryArtifact(
            codebase_understanding={"test": "data"},
            complexity_assessment="MEDIUM",
            relevant_files=["src/test.py"]
        )
        assert artifact.complexity_assessment == "MEDIUM"
        assert len(artifact.relevant_files) == 1
    
    def test_complexity_validation(self):
        """Test complexity assessment validation rules."""
        # Test low complexity with too many files should raise warning
        with pytest.warns(UserWarning):
            ContextDiscoveryArtifact(
                complexity_assessment="LOW",
                relevant_files=["file1.py", "file2.py", "file3.py", "file4.py"]
            )
    
    def test_ambiguity_question_validation(self):
        """Test ambiguity question format validation."""
        from src.alfred.models.discovery_artifacts import AmbiguityItem
        
        # Valid question
        valid_ambiguity = AmbiguityItem(
            question="Should we use OAuth2Service or LegacyAuthService?",
            context="Found two auth systems in codebase",
            impact_if_wrong="Could break existing auth flows",
            discovery_source="File analysis"
        )
        assert valid_ambiguity.question.endswith("?")
        
        # Invalid question - too short
        with pytest.raises(ValidationError):
            AmbiguityItem(
                question="How?",
                context="Context",
                impact_if_wrong="Impact",
                discovery_source="Source"
            )
        
        # Invalid question - no question mark
        with pytest.raises(ValidationError):
            AmbiguityItem(
                question="This is not a question",
                context="Context",
                impact_if_wrong="Impact", 
                discovery_source="Source"
            )


class TestSelfContainedSubtask:
    """Test suite for SelfContainedSubtask independence validation."""
    
    def test_subtask_independence_validation(self):
        """Test that subtasks with dependencies are rejected."""
        from src.alfred.models.discovery_artifacts import ContextBundle, TestingRequirements
        
        context_bundle = ContextBundle(
            existing_code="# test code",
            related_code_snippets={},
            testing_patterns="pytest patterns",
            error_handling_patterns="try/except patterns"
        )
        
        testing = TestingRequirements()
        
        # Valid independent subtask
        valid_subtask = SelfContainedSubtask(
            subtask_id="ST-001",
            title="Test subtask",
            location="src/test.py",
            operation="CREATE",
            context_bundle=context_bundle,
            testing=testing,
            dependencies=[]  # No dependencies - should pass
        )
        assert len(valid_subtask.dependencies) == 0
        
        # Invalid subtask with dependencies
        with pytest.raises(ValidationError):
            SelfContainedSubtask(
                subtask_id="ST-002",
                title="Dependent subtask",
                location="src/test.py", 
                operation="CREATE",
                context_bundle=context_bundle,
                testing=testing,
                dependencies=["ST-001"]  # Has dependency - should fail
            )
    
    def test_operation_validation(self):
        """Test operation type validation."""
        from src.alfred.models.discovery_artifacts import ContextBundle, TestingRequirements
        
        context_bundle = ContextBundle(
            existing_code="",
            related_code_snippets={},
            testing_patterns="",
            error_handling_patterns=""
        )
        testing = TestingRequirements()
        
        # Valid operations
        for operation in ["CREATE", "MODIFY", "DELETE"]:
            subtask = SelfContainedSubtask(
                subtask_id=f"ST-{operation}",
                title=f"Test {operation}",
                location="src/test.py",
                operation=operation,
                context_bundle=context_bundle,
                testing=testing
            )
            assert subtask.operation == operation
        
        # Invalid operation
        with pytest.raises(ValidationError):
            SelfContainedSubtask(
                subtask_id="ST-INVALID",
                title="Invalid operation",
                location="src/test.py",
                operation="UPDATE",  # Invalid operation
                context_bundle=context_bundle,
                testing=testing
            )


class TestValidationArtifact:
    """Test suite for ValidationArtifact approval logic."""
    
    def test_approval_status_validation(self):
        """Test approval status validation."""
        from src.alfred.models.discovery_artifacts import PlanSummary
        
        plan_summary = PlanSummary(
            files_affected=1,
            methods_created=1,
            methods_modified=0,
            tests_planned=2,
            estimated_complexity="LOW"
        )
        
        # Valid approval statuses
        for status in ["APPROVED", "NEEDS_REVISION", "REJECTED", "PENDING"]:
            artifact = ValidationArtifact(
                plan_summary=plan_summary,
                final_approval_status=status
            )
            assert artifact.final_approval_status == status
        
        # Invalid approval status
        with pytest.raises(ValidationError):
            ValidationArtifact(
                plan_summary=plan_summary,
                final_approval_status="INVALID_STATUS"
            )
    
    def test_requirement_coverage_confidence(self):
        """Test requirement coverage confidence validation."""
        from src.alfred.models.discovery_artifacts import RequirementCoverage, PlanSummary
        
        plan_summary = PlanSummary(
            files_affected=1,
            methods_created=1,
            methods_modified=0,
            tests_planned=2,
            estimated_complexity="LOW"
        )
        
        # Valid confidence values
        for confidence in [0.0, 0.5, 1.0]:
            coverage = RequirementCoverage(
                requirement="Test requirement",
                implementation_approach="Test approach",
                coverage_confidence=confidence,
                implementation_location="ST-001"
            )
            assert coverage.coverage_confidence == confidence
        
        # Invalid confidence values
        for invalid_confidence in [-0.1, 1.1, 2.0]:
            with pytest.raises(ValidationError):
                RequirementCoverage(
                    requirement="Test requirement",
                    implementation_approach="Test approach",
                    coverage_confidence=invalid_confidence,
                    implementation_location="ST-001"
                )
```

### 2.2 State Machine Testing

#### Test Coverage
- **State transitions per builder patterns**
- **Review state generation**
- **Terminal state validation**
- **Initial state handling**

#### Test Structure
```python
# tests/unit/core/test_discovery_workflow.py

import pytest
from src.alfred.core.discovery_workflow import PlanTaskTool, PlanTaskState


class TestPlanTaskToolStateMachine:
    """Test suite for PlanTaskTool state machine behavior."""
    
    def test_initial_state(self):
        """Test tool starts in correct initial state."""
        tool = PlanTaskTool("test-task-001")
        assert tool.state == PlanTaskState.DISCOVERY.value
    
    def test_state_machine_creation(self):
        """Test state machine is created with builder pattern."""
        tool = PlanTaskTool("test-task-001")
        
        # Verify machine exists
        assert tool.machine is not None
        
        # Verify states include work states and review states
        state_names = [state.name for state in tool.machine.states]
        
        # Check work states exist
        for work_state in PlanTaskState:
            if work_state != PlanTaskState.VERIFIED:
                assert work_state.value in state_names
        
        # Check review states exist (generated by builder)
        assert "discovery_awaiting_ai_review" in state_names
        assert "discovery_awaiting_human_review" in state_names
        assert "clarification_awaiting_ai_review" in state_names
        assert "clarification_awaiting_human_review" in state_names
    
    def test_artifact_mapping(self):
        """Test artifact mapping is correctly configured."""
        tool = PlanTaskTool("test-task-001")
        
        # Check artifact mapping exists for all work states
        expected_artifacts = {
            PlanTaskState.DISCOVERY: "ContextDiscoveryArtifact",
            PlanTaskState.CLARIFICATION: "ClarificationArtifact",
            PlanTaskState.CONTRACTS: "ContractDesignArtifact",
            PlanTaskState.IMPLEMENTATION_PLAN: "ImplementationPlanArtifact",
            PlanTaskState.VALIDATION: "ValidationArtifact"
        }
        
        for state, artifact_name in expected_artifacts.items():
            assert state in tool.artifact_map
            assert tool.artifact_map[state].__name__.endswith(artifact_name.split(".")[-1])
    
    def test_restart_context_handling(self):
        """Test re-planning context is handled correctly."""
        restart_context = {
            "restart_from": "CONTRACTS",
            "preserve_artifacts": ["discovery", "clarification"],
            "changes": "New requirements added"
        }
        
        tool = PlanTaskTool("test-task-001", restart_context=restart_context)
        
        # Should start from the specified restart state
        assert tool.state == PlanTaskState.CONTRACTS.value
        
        # Should have preserved artifacts in context store
        assert "preserved_discovery" in tool.context_store
        assert "preserved_clarification" in tool.context_store
    
    def test_final_work_state(self):
        """Test final work state identification."""
        tool = PlanTaskTool("test-task-001")
        assert tool.get_final_work_state() == PlanTaskState.VALIDATION.value
    
    def test_terminal_state_detection(self):
        """Test terminal state detection."""
        tool = PlanTaskTool("test-task-001")
        
        # Not terminal initially
        assert not tool.is_terminal
        
        # Manually set to terminal state for testing
        tool.state = PlanTaskState.VERIFIED.value
        assert tool.is_terminal
```

### 2.3 Context Loader Testing

#### Test Coverage
- **Pure function behavior**
- **Context data completeness**
- **Error handling for missing dependencies**
- **Re-planning context handling**

#### Test Structure
```python
# tests/unit/core/test_discovery_context.py

import pytest
from src.alfred.core.discovery_context import load_plan_task_context
from src.alfred.models.schemas import Task, TaskState


class TestDiscoveryContextLoaders:
    """Test suite for context loader functions."""
    
    def test_load_plan_task_context_basic(self):
        """Test basic context loading."""
        # Create mock task
        task = Task(
            id="test-task-001",
            title="Test Task",
            context="Test context",
            implementation_details="Test implementation",
            acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
        
        # Create mock task state
        task_state = TaskState(
            task_id="test-task-001",
            current_state="discovery",
            context_store={}
        )
        
        # Load context
        context = load_plan_task_context(task, task_state)
        
        # Verify basic context
        assert context["task_title"] == "Test Task"
        assert context["task_context"] == "Test context"
        assert context["implementation_details"] == "Test implementation"
        assert context["acceptance_criteria"] == ["Criterion 1", "Criterion 2"]
        assert context["restart_context"] is None
        assert context["preserved_artifacts"] == []
    
    def test_load_plan_task_context_with_restart(self):
        """Test context loading with restart context."""
        task = Task(
            id="test-task-001",
            title="Test Task",
            context="Test context"
        )
        
        restart_context = {
            "restart_from": "CONTRACTS",
            "preserve_artifacts": ["discovery", "clarification"]
        }
        
        task_state = TaskState(
            task_id="test-task-001",
            current_state="contracts",
            context_store={
                "restart_context": restart_context,
                "preserved_artifacts": ["discovery", "clarification"]
            }
        )
        
        context = load_plan_task_context(task, task_state)
        
        assert context["restart_context"] == restart_context
        assert context["preserved_artifacts"] == ["discovery", "clarification"]
    
    def test_load_plan_task_context_with_artifacts(self):
        """Test context loading includes previous phase artifacts."""
        task = Task(id="test-task-001", title="Test Task")
        
        # Mock artifacts from previous phases
        discovery_artifact = {"complexity": "MEDIUM", "files": ["test.py"]}
        clarification_artifact = {"resolved": ["question1"]}
        
        task_state = TaskState(
            task_id="test-task-001",
            current_state="contracts",
            artifacts={
                "discovery": discovery_artifact,
                "clarification": clarification_artifact
            }
        )
        
        context = load_plan_task_context(task, task_state)
        
        assert context["discovery_artifact"] == discovery_artifact
        assert context["clarification_artifact"] == clarification_artifact
    
    def test_context_loader_is_pure_function(self):
        """Test that context loader doesn't modify inputs."""
        task = Task(id="test-task-001", title="Original Title")
        task_state = TaskState(task_id="test-task-001", context_store={})
        
        original_task_title = task.title
        original_context_store = task_state.context_store.copy()
        
        # Call context loader
        load_plan_task_context(task, task_state)
        
        # Verify inputs weren't modified
        assert task.title == original_task_title
        assert task_state.context_store == original_context_store
```

---

## 3. Integration Testing Strategy

### 3.1 Workflow Integration Testing

#### Test Coverage
- **State machine transitions**
- **Tool configuration integration**
- **Handler execution**
- **Artifact persistence**

#### Test Structure
```python
# tests/integration/test_discovery_workflow_integration.py

import pytest
from src.alfred.tools.tool_factory import ToolFactory
from src.alfred.models.schemas import Task, TaskState, TaskStatus
from src.alfred.models.discovery_artifacts import ContextDiscoveryArtifact


class TestDiscoveryWorkflowIntegration:
    """Integration tests for discovery planning workflow."""
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task for testing."""
        return Task(
            id="test-task-001",
            title="Implement OAuth authentication",
            context="Add OAuth support for Google and GitHub providers",
            implementation_details="Create OAuthService with provider support",
            acceptance_criteria=[
                "Users can login with Google OAuth",
                "Users can login with GitHub OAuth",
                "OAuth tokens are validated properly"
            ],
            status=TaskStatus.NEW
        )
    
    @pytest.fixture
    def sample_task_state(self):
        """Create sample task state for testing."""
        return TaskState(
            task_id="test-task-001",
            current_state="discovery",
            status=TaskStatus.PLANNING,
            context_store={},
            artifacts={}
        )
    
    async def test_plan_task_tool_creation(self, sample_task, sample_task_state):
        """Test plan_task tool can be created via factory."""
        handler = ToolFactory.get_handler("plan_task")
        assert handler is not None
        
        # Test tool creation
        response = await handler.execute(task_id="test-task-001")
        assert response.success is True
        assert "discovery" in response.data.get("next_action", "")
    
    async def test_discovery_phase_execution(self, sample_task, sample_task_state):
        """Test discovery phase can execute and produce artifact."""
        handler = ToolFactory.get_handler("plan_task")
        
        # Mock discovery artifact submission
        discovery_artifact = ContextDiscoveryArtifact(
            codebase_understanding={
                "auth_systems": "Found OAuth2Service and LegacyAuthService"
            },
            ambiguities_discovered=[{
                "question": "Which auth system should be extended?",
                "context": "Two auth systems exist",
                "impact_if_wrong": "Could break existing flows",
                "discovery_source": "Code analysis"
            }],
            complexity_assessment="MEDIUM",
            relevant_files=["src/services/oauth_service.py"]
        )
        
        # Submit work for discovery phase
        response = await handler.submit_work(
            task_id="test-task-001",
            artifact=discovery_artifact.dict()
        )
        
        assert response.success is True
        assert "ai_review" in response.data.get("next_state", "")
    
    async def test_state_transitions_follow_builder_pattern(self, sample_task):
        """Test that state transitions follow the builder-generated pattern."""
        handler = ToolFactory.get_handler("plan_task")
        
        # Create tool instance
        tool_response = await handler.execute(task_id="test-task-001")
        
        # Get the tool instance (this would be from the handler's state)
        from src.alfred.core.discovery_workflow import PlanTaskTool
        tool = PlanTaskTool("test-task-001")
        
        # Test initial state
        assert tool.state == "discovery"
        
        # Test that review states are generated correctly
        discovery_review_states = tool.get_review_states_for_state("discovery")
        assert "discovery_awaiting_ai_review" in discovery_review_states
        assert "discovery_awaiting_human_review" in discovery_review_states
    
    async def test_artifact_persistence_across_states(self):
        """Test that artifacts are persisted across state transitions."""
        from src.alfred.state.manager import StateManager
        
        state_manager = StateManager()
        
        # Create initial state
        await state_manager.create_task_state("test-task-001")
        
        # Store discovery artifact
        discovery_artifact = ContextDiscoveryArtifact(
            complexity_assessment="LOW",
            relevant_files=["test.py"]
        )
        
        await state_manager.store_artifact(
            "test-task-001", 
            "discovery", 
            discovery_artifact.dict()
        )
        
        # Verify artifact can be retrieved
        stored_artifact = await state_manager.get_artifact("test-task-001", "discovery")
        assert stored_artifact is not None
        assert stored_artifact["complexity_assessment"] == "LOW"
```

### 3.2 Template Integration Testing

#### Test Coverage
- **Template rendering with real context**
- **Variable substitution**
- **Template structure validation**
- **Prompt quality validation**

#### Test Structure
```python
# tests/integration/test_template_integration.py

import pytest
from src.alfred.core.prompt_templates import PromptBuilder
from src.alfred.models.schemas import Task, TaskState


class TestTemplateIntegration:
    """Integration tests for template rendering and prompt generation."""
    
    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance."""
        return PromptBuilder()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample context for template rendering."""
        return {
            "task_id": "test-task-001",
            "tool_name": "plan_task",
            "current_state": "discovery",
            "task_title": "Implement OAuth authentication",
            "task_context": "Add OAuth support for providers",
            "implementation_details": "Create OAuthService class",
            "acceptance_criteria": [
                "Users can login with Google OAuth",
                "Users can login with GitHub OAuth"
            ],
            "feedback_section": ""
        }
    
    def test_discovery_template_rendering(self, prompt_builder, sample_context):
        """Test discovery template renders correctly."""
        prompt = prompt_builder.build_prompt(
            tool_name="plan_task",
            state="discovery",
            context=sample_context
        )
        
        # Verify template structure
        assert "# CONTEXT" in prompt
        assert "# OBJECTIVE" in prompt
        assert "# BACKGROUND" in prompt
        assert "# INSTRUCTIONS" in prompt
        assert "# CONSTRAINTS" in prompt
        assert "# OUTPUT" in prompt
        assert "# EXAMPLES" in prompt
        
        # Verify variable substitution
        assert "test-task-001" in prompt
        assert "Implement OAuth authentication" in prompt
        assert "ContextDiscoveryArtifact" in prompt
    
    def test_clarification_template_with_discovery_artifact(self, prompt_builder):
        """Test clarification template includes discovery results."""
        discovery_artifact = {
            "complexity_assessment": "MEDIUM",
            "relevant_files": ["src/oauth.py"],
            "ambiguities_discovered": [{
                "question": "Which auth system to use?",
                "context": "Found two systems"
            }]
        }
        
        context = {
            "task_id": "test-task-001",
            "tool_name": "plan_task",
            "current_state": "clarification",
            "task_title": "Test Task",
            "discovery_artifact": discovery_artifact,
            "feedback_section": ""
        }
        
        prompt = prompt_builder.build_prompt(
            tool_name="plan_task",
            state="clarification",
            context=context
        )
        
        # Verify discovery results are included
        assert "MEDIUM" in prompt
        assert "src/oauth.py" in prompt
        assert "Which auth system to use?" in prompt
    
    def test_all_templates_render_without_errors(self, prompt_builder, sample_context):
        """Test all planning templates can render without errors."""
        states = ["discovery", "clarification", "contracts", "implementation_plan", "validation"]
        
        for state in states:
            context = sample_context.copy()
            context["current_state"] = state
            
            # Add state-specific artifacts
            if state != "discovery":
                context["discovery_artifact"] = {"complexity": "MEDIUM"}
            if state in ["contracts", "implementation_plan", "validation"]:
                context["clarification_artifact"] = {"resolved": ["question1"]}
            if state in ["implementation_plan", "validation"]:
                context["contracts_artifact"] = {"methods": ["authenticate"]}
            if state == "validation":
                context["implementation_artifact"] = {"subtasks": ["ST-001"]}
            
            # Should not raise any exceptions
            prompt = prompt_builder.build_prompt(
                tool_name="plan_task",
                state=state,
                context=context
            )
            
            assert len(prompt) > 0
            assert f"State: {state}" in prompt
```

---

## 4. End-to-End Testing Strategy

### 4.1 Complete Workflow Testing

#### Test Coverage
- **Full planning workflow execution**
- **State transitions and reviews**
- **Artifact quality and consistency**
- **Human interaction simulation**

#### Test Structure
```python
# tests/e2e/test_complete_planning_workflow.py

import pytest
from src.alfred.tools.tool_factory import ToolFactory
from src.alfred.models.schemas import Task, TaskStatus


class TestCompletePlanningWorkflow:
    """End-to-end tests for complete planning workflow."""
    
    @pytest.fixture
    async def planning_workflow(self):
        """Set up complete planning workflow test environment."""
        # Create test task
        task = Task(
            id="e2e-test-001",
            title="Add user profile management",
            context="Users need ability to update their profiles",
            implementation_details="Add profile editing forms and API endpoints",
            acceptance_criteria=[
                "Users can view their profile",
                "Users can edit profile fields",
                "Profile changes are validated",
                "Profile updates are saved to database"
            ],
            status=TaskStatus.NEW
        )
        
        return {
            "task": task,
            "handler": ToolFactory.get_handler("plan_task")
        }
    
    async def test_complete_planning_flow(self, planning_workflow):
        """Test complete planning flow from discovery to validation."""
        handler = planning_workflow["handler"]
        task_id = planning_workflow["task"].id
        
        # Phase 1: Discovery
        discovery_response = await handler.execute(task_id=task_id)
        assert discovery_response.success
        assert "discovery" in discovery_response.data["current_state"]
        
        # Submit discovery artifact
        discovery_artifact = {
            "codebase_understanding": {
                "user_model": "Found User model in src/models/user.py",
                "existing_endpoints": "Profile endpoints exist but limited"
            },
            "ambiguities_discovered": [{
                "question": "Should profile updates be real-time or batch processed?",
                "context": "Current system uses real-time for some fields",
                "impact_if_wrong": "Performance implications",
                "discovery_source": "API analysis"
            }],
            "extracted_context": {
                "user_model_code": "class User(BaseModel): ...",
                "validation_patterns": "def validate_email(email): ..."
            },
            "complexity_assessment": "MEDIUM",
            "relevant_files": [
                "src/models/user.py",
                "src/api/profile.py",
                "src/forms/profile_form.py"
            ]
        }
        
        submit_response = await handler.submit_work(
            task_id=task_id,
            artifact=discovery_artifact
        )
        assert submit_response.success
        
        # Phase 2: Clarification (simulate human responses)
        # In real scenario, human would answer the ambiguity questions
        clarification_artifact = {
            "resolved_ambiguities": [{
                "original_question": "Should profile updates be real-time or batch processed?",
                "human_response": "Real-time updates for better UX, batch for audit logs",
                "clarification": "Use real-time updates with async audit logging",
                "final_decision": "Real-time updates with background audit trail"
            }],
            "updated_requirements": [{
                "original_requirement": "Profile updates are saved to database",
                "updated_requirement": "Profile updates are saved in real-time with async audit logging",
                "reason_for_change": "Better UX with audit trail requirement"
            }],
            "domain_knowledge_gained": [
                "Audit logging is required for compliance",
                "Real-time feedback improves user experience"
            ]
        }
        
        clarification_response = await handler.submit_work(
            task_id=task_id,
            artifact=clarification_artifact
        )
        assert clarification_response.success
        
        # Phase 3: Contracts
        contracts_artifact = {
            "method_contracts": [{
                "class_name": "ProfileService",
                "method_name": "update_profile",
                "signature": "async def update_profile(user_id: str, updates: dict) -> ProfileUpdateResult",
                "purpose": "Update user profile with validation and audit logging",
                "error_handling": ["ValidationError", "UserNotFoundError"],
                "test_approach": "Mock user data, test validation scenarios"
            }],
            "data_models": [{
                "name": "ProfileUpdateResult",
                "fields": [
                    {"name": "success", "type": "bool", "required": True},
                    {"name": "updated_fields", "type": "List[str]", "required": True}
                ],
                "validation_rules": [
                    {"field": "updated_fields", "rule": "Must not be empty if success=True"}
                ]
            }],
            "error_handling_strategy": {
                "base_exception": "ProfileServiceError",
                "validation_errors": "ValidationError with field details"
            }
        }
        
        contracts_response = await handler.submit_work(
            task_id=task_id,
            artifact=contracts_artifact
        )
        assert contracts_response.success
        
        # Phase 4: Implementation Plan
        implementation_artifact = {
            "file_operations": [{
                "file_path": "src/services/profile_service.py",
                "operation": "CREATE",
                "changes_description": "Create ProfileService with update_profile method"
            }],
            "subtasks": [{
                "subtask_id": "ST-001",
                "title": "Create ProfileService.update_profile method",
                "location": "src/services/profile_service.py",
                "operation": "CREATE",
                "context_bundle": {
                    "existing_code": "# New file",
                    "related_code_snippets": {
                        "service_pattern": "class UserService(BaseService): ...",
                        "validation_pattern": "def validate_user_input(data): ..."
                    },
                    "testing_patterns": "Use pytest with mock database",
                    "error_handling_patterns": "Raise specific exceptions with details"
                },
                "specification": {
                    "exact_changes": ["Create ProfileService class", "Implement update_profile method"],
                    "method_implementations": [{
                        "method_name": "update_profile",
                        "signature": "async def update_profile(self, user_id: str, updates: dict) -> ProfileUpdateResult",
                        "implementation_approach": "Validate input, update database, trigger audit log"
                    }]
                },
                "testing": {
                    "unit_tests_to_create": ["test_update_profile_success", "test_update_profile_validation_error"],
                    "verification_steps": ["Method exists", "Validation works", "Audit logging triggered"]
                },
                "acceptance_criteria": [
                    "ProfileService class created",
                    "update_profile method implemented",
                    "Validation and error handling working",
                    "Unit tests pass"
                ],
                "dependencies": []
            }],
            "test_plan": {
                "unit_tests": [{"name": "test_profile_service", "description": "Test ProfileService methods"}],
                "integration_tests": [{"name": "test_profile_api", "description": "Test profile API endpoints"}]
            }
        }
        
        implementation_response = await handler.submit_work(
            task_id=task_id,
            artifact=implementation_artifact
        )
        assert implementation_response.success
        
        # Phase 5: Validation
        validation_artifact = {
            "plan_summary": {
                "files_affected": 3,
                "methods_created": 2,
                "methods_modified": 1,
                "tests_planned": 6,
                "estimated_complexity": "MEDIUM"
            },
            "requirement_coverage": [{
                "requirement": "Users can edit profile fields",
                "implementation_approach": "ProfileService.update_profile method with form validation",
                "coverage_confidence": 0.95,
                "implementation_location": "ST-001"
            }],
            "risk_assessment": [{
                "risk": "Profile validation could miss edge cases",
                "probability": "MEDIUM",
                "impact": "MEDIUM",
                "mitigation": "Comprehensive unit tests with edge case scenarios"
            }],
            "subtask_independence_check": [{
                "subtask_id": "ST-001",
                "is_independent": True,
                "dependencies_found": [],
                "context_completeness": 0.9
            }],
            "final_approval_status": "APPROVED",
            "approval_reasoning": "Plan addresses all requirements with good risk mitigation"
        }
        
        validation_response = await handler.submit_work(
            task_id=task_id,
            artifact=validation_artifact
        )
        assert validation_response.success
        
        # Verify final state
        assert "verified" in validation_response.data.get("current_state", "")
    
    async def test_replanning_workflow(self, planning_workflow):
        """Test re-planning workflow when requirements change."""
        handler = planning_workflow["handler"]
        task_id = planning_workflow["task"].id
        
        # Start initial planning
        await handler.execute(task_id=task_id)
        
        # Submit initial discovery
        discovery_artifact = {
            "complexity_assessment": "LOW",
            "relevant_files": ["src/simple.py"]
        }
        await handler.submit_work(task_id=task_id, artifact=discovery_artifact)
        
        # Trigger re-planning due to changed requirements
        restart_context = {
            "trigger": "requirements_changed",
            "restart_from": "DISCOVERY",
            "changes": "Added complex validation requirements",
            "preserve_artifacts": [],
            "invalidated_decisions": ["simple_implementation"]
        }
        
        replanning_response = await handler.execute(
            task_id=task_id,
            restart_context=restart_context
        )
        
        assert replanning_response.success
        assert "discovery" in replanning_response.data["current_state"]
        assert "restart_context" in replanning_response.data
```

### 4.2 Performance Testing

#### Test Coverage
- **Template rendering performance**
- **State transition latency**
- **Artifact serialization performance**
- **Memory usage validation**

#### Test Structure
```python
# tests/performance/test_planning_performance.py

import pytest
import time
import asyncio
from src.alfred.tools.tool_factory import ToolFactory
from src.alfred.core.prompt_templates import PromptBuilder


class TestPlanningPerformance:
    """Performance tests for planning system."""
    
    def test_template_rendering_performance(self):
        """Test template rendering completes within acceptable time."""
        prompt_builder = PromptBuilder()
        
        context = {
            "task_id": "perf-test-001",
            "tool_name": "plan_task",
            "current_state": "discovery",
            "task_title": "Performance Test Task",
            "task_context": "Test context",
            "implementation_details": "Test details",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "feedback_section": ""
        }
        
        start_time = time.time()
        
        # Render multiple templates
        for _ in range(100):
            prompt = prompt_builder.build_prompt(
                tool_name="plan_task",
                state="discovery",
                context=context
            )
            assert len(prompt) > 0
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should render each template in less than 10ms
        assert avg_time < 0.01, f"Template rendering too slow: {avg_time:.4f}s"
    
    async def test_state_transition_performance(self):
        """Test state transitions complete within acceptable time."""
        handler = ToolFactory.get_handler("plan_task")
        
        start_time = time.time()
        
        # Execute initial planning
        response = await handler.execute(task_id="perf-test-001")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within 1 second
        assert execution_time < 1.0, f"State transition too slow: {execution_time:.4f}s"
        assert response.success
    
    def test_artifact_serialization_performance(self):
        """Test artifact serialization performance."""
        from src.alfred.models.discovery_artifacts import ImplementationPlanArtifact, SelfContainedSubtask
        
        # Create large artifact
        subtasks = []
        for i in range(100):
            subtask = SelfContainedSubtask(
                subtask_id=f"ST-{i:03d}",
                title=f"Subtask {i}",
                location=f"src/file_{i}.py",
                operation="CREATE",
                context_bundle={
                    "existing_code": "# Large code snippet " * 100,
                    "related_code_snippets": {f"pattern_{j}": "code" * 50 for j in range(10)},
                    "testing_patterns": "test pattern " * 20,
                    "error_handling_patterns": "error pattern " * 20
                },
                specification={"changes": [f"Change {i}"] * 10},
                testing={"tests": [f"test_{i}_{j}" for j in range(5)]},
                acceptance_criteria=[f"Criterion {i}_{j}" for j in range(3)]
            )
            subtasks.append(subtask)
        
        artifact = ImplementationPlanArtifact(subtasks=subtasks)
        
        # Test serialization performance
        start_time = time.time()
        
        for _ in range(10):
            json_data = artifact.dict()
            assert len(json_data["subtasks"]) == 100
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Should serialize large artifact in less than 100ms
        assert avg_time < 0.1, f"Artifact serialization too slow: {avg_time:.4f}s"
```

---

## 5. Compliance Testing Strategy

### 5.1 Architectural Principles Compliance

#### Test Coverage
- **State machine builder usage**
- **Handler configuration compliance**
- **Template structure validation**
- **Tool registration compliance**

#### Test Structure
```python
# tests/compliance/test_architectural_compliance.py

import pytest
import inspect
from src.alfred.core.discovery_workflow import PlanTaskTool
from src.alfred.tools.tool_definitions import PLAN_TASK_TOOL
from src.alfred.core.workflow_config import WORKFLOW_TOOL_CONFIGS


class TestArchitecturalCompliance:
    """Tests to ensure compliance with Alfred architectural principles."""
    
    def test_state_machine_uses_builder_pattern(self):
        """Test that state machine uses builder pattern (no manual construction)."""
        # Get the PlanTaskTool source code
        source = inspect.getsource(PlanTaskTool.__init__)
        
        # Should use workflow_builder
        assert "workflow_builder.build_workflow_with_reviews" in source
        
        # Should NOT manually create states or transitions
        assert "states=" not in source or "machine_config[" in source
        assert "transitions=" not in source or "machine_config[" in source
        
    def test_no_custom_handler_classes(self):
        """Test that no custom handler classes are created."""
        # Check tool configuration uses GenericWorkflowHandler
        plan_task_config = WORKFLOW_TOOL_CONFIGS.get("plan_task")
        assert plan_task_config is not None
        
        # Should use the standard handler (configured via tool factory)
        # The handler should come from GenericWorkflowHandler, not a custom class
        from src.alfred.tools.tool_factory import ToolFactory
        handler = ToolFactory.get_handler("plan_task")
        
        # Handler should be GenericWorkflowHandler instance
        assert handler.__class__.__name__ == "GenericWorkflowHandler"
    
    def test_context_loader_is_pure_function(self):
        """Test that context loader is a pure function."""
        from src.alfred.core.discovery_context import load_plan_task_context
        
        # Get function source
        source = inspect.getsource(load_plan_task_context)
        
        # Should not have side effects (no global variables, no external state modification)
        forbidden_patterns = [
            "global ",
            "self.",
            "cls.",
            "import ",  # Should not import inside function
            "print(",   # Should not have side effects
            "logging.", # Should not log (side effect)
        ]
        
        for pattern in forbidden_patterns:
            if pattern == "import " and "from typing import" in source:
                continue  # Type imports are OK
            assert pattern not in source, f"Context loader should not contain '{pattern}'"
        
        # Should return a dictionary
        assert "return" in source
        assert "dict" in source or "{" in source
    
    def test_template_structure_compliance(self):
        """Test that templates follow the required structure."""
        from pathlib import Path
        import re
        
        template_dir = Path("src/alfred/templates/prompts/plan_task")
        required_sections = [
            "# CONTEXT",
            "# OBJECTIVE", 
            "# BACKGROUND",
            "# INSTRUCTIONS",
            "# CONSTRAINTS",
            "# OUTPUT",
            "# EXAMPLES"
        ]
        
        for template_file in template_dir.glob("*.md"):
            if template_file.name.startswith("_"):
                continue  # Skip private templates
                
            content = template_file.read_text()
            
            # Check required sections
            for section in required_sections:
                assert section in content, f"Template {template_file.name} missing {section}"
            
            # Check for header comment
            assert content.startswith("<!--"), f"Template {template_file.name} missing header comment"
            
            # Check no Jinja2 logic
            assert "{%" not in content, f"Template {template_file.name} contains forbidden logic"
            
            # Check only standard variables
            variables = re.findall(r'\$\{(\w+)\}', content)
            standard_vars = {
                'task_id', 'tool_name', 'current_state', 'task_title',
                'task_context', 'implementation_details', 'acceptance_criteria',
                'artifact_json', 'feedback_section', 'discovery_artifact',
                'clarification_artifact', 'contracts_artifact', 'implementation_artifact'
            }
            
            unknown_vars = set(variables) - standard_vars
            assert not unknown_vars, f"Template {template_file.name} uses unknown variables: {unknown_vars}"
    
    def test_tool_registration_compliance(self):
        """Test that tool registration follows principles."""
        # Check tool definition exists
        assert PLAN_TASK_TOOL is not None
        assert PLAN_TASK_TOOL.name == "plan_task"
        
        # Check tool configuration exists
        plan_task_config = WORKFLOW_TOOL_CONFIGS.get("plan_task")
        assert plan_task_config is not None
        assert plan_task_config.tool_name == "plan_task"
        
        # Check required configuration fields
        required_fields = [
            'tool_name', 'tool_class', 'required_status',
            'entry_status_map', 'dispatch_on_init', 'context_loader'
        ]
        
        for field in required_fields:
            assert hasattr(plan_task_config, field), f"Missing required field: {field}"
        
        # Check context loader is callable
        assert callable(plan_task_config.context_loader)
```

---

## 6. Test Execution Strategy

### 6.1 Test Organization

```
tests/
├── unit/                          # Unit tests
│   ├── models/
│   │   ├── test_discovery_artifacts.py
│   │   └── test_artifact_validation.py
│   ├── core/
│   │   ├── test_discovery_workflow.py
│   │   ├── test_discovery_context.py
│   │   └── test_state_machine_builder.py
│   └── tools/
│       └── test_plan_task_tool.py
├── integration/                   # Integration tests
│   ├── test_discovery_workflow_integration.py
│   ├── test_template_integration.py
│   └── test_handler_integration.py
├── e2e/                          # End-to-end tests
│   ├── test_complete_planning_workflow.py
│   └── test_replanning_scenarios.py
├── performance/                   # Performance tests
│   └── test_planning_performance.py
├── compliance/                    # Architectural compliance tests
│   └── test_architectural_compliance.py
└── fixtures/                     # Test fixtures and utilities
    ├── sample_tasks.py
    ├── mock_artifacts.py
    └── test_helpers.py
```

### 6.2 Test Execution Commands

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run unit tests only
uv run python -m pytest tests/unit/ -v

# Run integration tests
uv run python -m pytest tests/integration/ -v

# Run end-to-end tests
uv run python -m pytest tests/e2e/ -v

# Run performance tests
uv run python -m pytest tests/performance/ -v

# Run compliance tests
uv run python -m pytest tests/compliance/ -v

# Run with coverage
uv run python -m pytest tests/ --cov=src/alfred --cov-report=html

# Run specific test patterns
uv run python -m pytest tests/ -k "discovery" -v
uv run python -m pytest tests/ -k "artifact" -v
uv run python -m pytest tests/ -k "template" -v
```

### 6.3 Continuous Integration

```yaml
# .github/workflows/discovery_planning_tests.yml
name: Discovery Planning Tests

on:
  push:
    paths:
      - 'src/alfred/core/discovery_*'
      - 'src/alfred/models/discovery_*'
      - 'src/alfred/templates/prompts/plan_task/*'
      - 'tests/**'
  pull_request:
    paths:
      - 'src/alfred/core/discovery_*'
      - 'src/alfred/models/discovery_*'
      - 'src/alfred/templates/prompts/plan_task/*'
      - 'tests/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      
      - name: Run unit tests
        run: uv run python -m pytest tests/unit/ -v
      
      - name: Run integration tests
        run: uv run python -m pytest tests/integration/ -v
      
      - name: Run compliance tests
        run: uv run python -m pytest tests/compliance/ -v
      
      - name: Run performance tests
        run: uv run python -m pytest tests/performance/ -v
      
      - name: Generate coverage report
        run: uv run python -m pytest tests/ --cov=src/alfred --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 7. Success Criteria

### 7.1 Coverage Requirements
- **Unit Test Coverage**: ≥ 95% for new code
- **Integration Test Coverage**: ≥ 90% for workflow paths
- **End-to-End Coverage**: 100% of planning states tested

### 7.2 Performance Requirements
- **Template Rendering**: < 10ms per template
- **State Transitions**: < 1s per transition
- **Artifact Serialization**: < 100ms for large artifacts

### 7.3 Quality Requirements
- **All tests pass**: 100% test success rate
- **No regressions**: Existing functionality remains intact
- **Compliance validation**: 100% architectural principles compliance

This comprehensive testing strategy ensures the Discovery Planning system is robust, performant, and maintains full compliance with Alfred's architectural principles while delivering high-quality planning capabilities.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "docs-1", "content": "Create implementation design document", "status": "completed", "priority": "high"}, {"id": "docs-2", "content": "Create detailed file creation plan", "status": "completed", "priority": "high"}, {"id": "docs-3", "content": "Create artifact and model specifications", "status": "completed", "priority": "high"}, {"id": "docs-4", "content": "Create prompt template specifications", "status": "completed", "priority": "medium"}, {"id": "docs-5", "content": "Create testing strategy document", "status": "completed", "priority": "medium"}]