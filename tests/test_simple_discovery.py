"""Test simplified discovery artifacts."""

import pytest
from alfred.models.planning_artifacts import ContextDiscoveryArtifact, ClarificationArtifact, ComplexityLevel


def test_simple_discovery_artifact():
    """Test the simplified discovery artifact."""
    artifact = ContextDiscoveryArtifact(
        findings="""## Discovery Results
        
### Current State
- Task model uses Pydantic
- No priority field exists
        
### Patterns
- String-based enums for JSON compatibility
""",
        questions=["Should priority be required or optional?", "How should priority affect ranking?"],
        files_to_modify=["src/alfred/models/schemas.py", "src/alfred/lib/md_parser.py"],
        complexity=ComplexityLevel.MEDIUM,
        implementation_context={"enum_pattern": "class Status(str, Enum):", "existing_fields": ["task_id", "title", "status"]},
    )

    # Verify all fields
    assert "Task model uses Pydantic" in artifact.findings
    assert len(artifact.questions) == 2
    assert all(q.endswith("?") for q in artifact.questions)
    assert len(artifact.files_to_modify) == 2
    assert artifact.complexity == ComplexityLevel.MEDIUM
    assert "enum_pattern" in artifact.implementation_context


def test_simple_clarification_artifact():
    """Test the simplified clarification artifact."""
    artifact = ClarificationArtifact(
        clarification_dialogue="""## Q&A Session
        
**AI**: Should priority be required?
**Human**: Make it optional with MEDIUM default.
**AI**: Got it. Where in ranking?
**Human**: After in-progress, before ready.
""",
        decisions=["Priority is optional with default=MEDIUM", "Priority ranks second after in-progress"],
        additional_constraints=["Must maintain backward compatibility"],
    )

    assert "Should priority be required?" in artifact.clarification_dialogue
    assert len(artifact.decisions) == 2
    assert len(artifact.additional_constraints) == 1


def test_question_validation():
    """Test that questions must end with ?"""
    with pytest.raises(ValueError, match="must end with"):
        ContextDiscoveryArtifact(
            findings="Some findings",
            questions=["This is not a question"],  # Missing ?
            files_to_modify=[],
            complexity=ComplexityLevel.LOW,
        )


def test_empty_findings_validation():
    """Test that findings cannot be empty."""
    with pytest.raises(ValueError, match="cannot be empty"):
        ContextDiscoveryArtifact(
            findings="   ",  # Just whitespace
            questions=[],
            files_to_modify=[],
            complexity=ComplexityLevel.LOW,
        )


def test_minimal_artifact():
    """Test creating artifact with minimal required fields."""
    artifact = ContextDiscoveryArtifact(
        findings="Found the issue in auth module",
        questions=[],  # Empty is OK
        files_to_modify=[],  # Empty is OK
        complexity=ComplexityLevel.LOW,
        implementation_context={},  # Empty is OK
    )

    assert artifact.findings
    assert artifact.questions == []
    assert artifact.implementation_context == {}


# Backward compatibility test removed - old module doesn't exist
