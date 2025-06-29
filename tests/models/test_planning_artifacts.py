# tests/models/test_planning_artifacts.py
import pytest
from pydantic import ValidationError

from src.alfred.models.planning_artifacts import (
    ContextAnalysisArtifact, 
    StrategyArtifact, 
    DesignArtifact, 
    ExecutionPlanArtifact
)
from src.alfred.models.schemas import SLOT, OperationType, Taskflow


class TestContextAnalysisArtifact:
    """Test cases for ContextAnalysisArtifact model."""
    
    def test_valid_context_analysis_artifact(self):
        """Test that a valid ContextAnalysisArtifact can be created."""
        data = {
            "context_summary": "This task involves adding user authentication",
            "affected_files": ["src/auth.py", "tests/test_auth.py"],
            "questions_for_developer": ["Should we use JWT or sessions?", "What's the password policy?"]
        }
        
        artifact = ContextAnalysisArtifact.model_validate(data)
        
        assert artifact.context_summary == data["context_summary"]
        assert artifact.affected_files == data["affected_files"]
        assert artifact.questions_for_developer == data["questions_for_developer"]
    
    def test_missing_required_field_context_summary(self):
        """Test that ValidationError is raised when context_summary is missing."""
        data = {
            "affected_files": ["src/auth.py"],
            "questions_for_developer": ["Should we use JWT?"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContextAnalysisArtifact.model_validate(data)
        
        assert "context_summary" in str(exc_info.value)
    
    def test_missing_required_field_affected_files(self):
        """Test that ValidationError is raised when affected_files is missing."""
        data = {
            "context_summary": "Adding auth",
            "questions_for_developer": ["Should we use JWT?"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContextAnalysisArtifact.model_validate(data)
        
        assert "affected_files" in str(exc_info.value)


class TestStrategyArtifact:
    """Test cases for StrategyArtifact model."""
    
    def test_valid_strategy_artifact_minimal(self):
        """Test that a minimal valid StrategyArtifact can be created."""
        data = {
            "high_level_strategy": "Implement OAuth 2.0 authentication flow",
            "key_components": ["OAuth provider", "Token validation", "User session management"]
        }
        
        artifact = StrategyArtifact.model_validate(data)
        
        assert artifact.high_level_strategy == data["high_level_strategy"]
        assert artifact.key_components == data["key_components"]
        assert artifact.new_dependencies == []  # Default empty list
        assert artifact.risk_analysis is None  # Default None
    
    def test_valid_strategy_artifact_complete(self):
        """Test that a complete StrategyArtifact can be created."""
        data = {
            "high_level_strategy": "Implement OAuth 2.0 authentication flow",
            "key_components": ["OAuth provider", "Token validation"],
            "new_dependencies": ["requests", "pyjwt"],
            "risk_analysis": "Risk of breaking existing authentication system"
        }
        
        artifact = StrategyArtifact.model_validate(data)
        
        assert artifact.high_level_strategy == data["high_level_strategy"]
        assert artifact.key_components == data["key_components"]
        assert artifact.new_dependencies == data["new_dependencies"]
        assert artifact.risk_analysis == data["risk_analysis"]
    
    def test_missing_required_field_high_level_strategy(self):
        """Test that ValidationError is raised when high_level_strategy is missing."""
        data = {
            "key_components": ["OAuth provider"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            StrategyArtifact.model_validate(data)
        
        assert "high_level_strategy" in str(exc_info.value)


class TestDesignArtifact:
    """Test cases for DesignArtifact model."""
    
    def test_valid_design_artifact(self):
        """Test that a valid DesignArtifact can be created."""
        data = {
            "design_summary": "The OAuth system will consist of three main components...",
            "file_breakdown": [
                {
                    "file_path": "src/auth/oauth.py", 
                    "change_summary": "Main OAuth implementation",
                    "operation": "create"
                },
                {
                    "file_path": "src/auth/tokens.py", 
                    "change_summary": "Token validation and management",
                    "operation": "modify"
                }
            ]
        }
        
        artifact = DesignArtifact.model_validate(data)
        
        assert artifact.design_summary == data["design_summary"]
        assert len(artifact.file_breakdown) == 2
        assert artifact.file_breakdown[0].file_path == "src/auth/oauth.py"
        assert artifact.file_breakdown[0].change_summary == "Main OAuth implementation"
        assert artifact.file_breakdown[0].operation == "create"
    
    def test_missing_required_field_detailed_design(self):
        """Test that ValidationError is raised when design_summary is missing."""
        data = {
            "file_breakdown": [
                {
                    "file_path": "src/auth.py", 
                    "change_summary": "Authentication implementation",
                    "operation": "create"
                }
            ]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            DesignArtifact.model_validate(data)
        
        assert "design_summary" in str(exc_info.value)


class TestExecutionPlanArtifact:
    """Test cases for ExecutionPlanArtifact (List[SLOT])."""
    
    def test_valid_execution_plan_artifact(self):
        """Test that a valid ExecutionPlanArtifact (list of SLOTs) can be created."""
        slot_data = {
            "slot_id": "slot_1.1",
            "title": "Create OAuth provider class",
            "spec": "Implement OAuth2Provider class with authenticate method",
            "location": "src/auth/oauth.py", 
            "operation": OperationType.CREATE,
            "taskflow": {
                "procedural_steps": ["Create class skeleton", "Implement authenticate method"],
                "verification_steps": ["Run unit tests", "Verify OAuth flow works"]
            }
        }
        
        execution_plan = [slot_data]
        
        # ExecutionPlanArtifact is just List[SLOT], so we validate each SLOT
        validated_slots = [SLOT.model_validate(slot) for slot in execution_plan]
        
        assert len(validated_slots) == 1
        assert validated_slots[0].slot_id == slot_data["slot_id"]
        assert validated_slots[0].title == slot_data["title"]
    
    def test_empty_execution_plan_artifact(self):
        """Test that an empty ExecutionPlanArtifact is valid."""
        execution_plan = []
        
        # An empty list should be valid
        validated_slots = [SLOT.model_validate(slot) for slot in execution_plan]
        
        assert len(validated_slots) == 0
    
    def test_invalid_slot_in_execution_plan(self):
        """Test that ValidationError is raised for invalid SLOT in ExecutionPlanArtifact."""
        invalid_slot_data = {
            "slot_id": "slot_1.1",
            # Missing required fields like title, spec, etc.
        }
        
        execution_plan = [invalid_slot_data]
        
        with pytest.raises(ValidationError):
            [SLOT.model_validate(slot) for slot in execution_plan]