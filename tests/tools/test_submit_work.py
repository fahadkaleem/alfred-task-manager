"""
Comprehensive tests for submit_for_review tool covering artifact writing, state transitions, and validation
"""

from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import pytest

from epic_task_manager.tools.task_tools import submit_for_review


class TestSubmitWork:
    """Test submit_for_review tool functionality"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with patch("epic_task_manager.config.settings.settings") as mock_settings:
                mock_settings.config_file = temp_path / ".epictaskmanager" / "config.json"
                mock_settings.workspace_dir = temp_path / ".epictaskmanager" / "workspace"
                yield temp_path

    @pytest.fixture
    def mock_state_manager(self):
        """Mock StateManager for testing"""
        with patch("epic_task_manager.tools.task_tools.state_manager") as mock_manager:
            yield mock_manager

    @pytest.fixture
    def mock_artifact_manager(self):
        """Mock ArtifactManager for testing"""
        with patch("epic_task_manager.tools.task_tools.artifact_manager") as mock_manager:
            yield mock_manager

    @pytest.fixture
    def mock_prompter(self):
        """Mock Prompter for testing"""
        with patch("epic_task_manager.tools.task_tools.prompter") as mock_prompter:
            yield mock_prompter

    @pytest.fixture
    def initialized_project(self, temp_project_dir):
        """Create initialized project structure"""
        config_file = temp_project_dir / ".epictaskmanager" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text('{"version": "1.0"}')
        return temp_project_dir

    @pytest.mark.asyncio
    async def test_submit_work_writes_structured_artifact_with_yaml_front_matter(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review correctly writes structured artifact with YAML front matter"""
        # Mock existing task in working state
        mock_machine = Mock()
        mock_machine.state = "gatherrequirements_working"
        mock_state_manager.get_machine.return_value = mock_machine

        # Mock template loading
        mock_prompter._load_template.return_value = "# Template\n{task_summary}\n{task_description}"

        # Mock artifact building
        mock_artifact_manager.build_structured_artifact.return_value = "Built artifact content"
        mock_prompter.generate_prompt.return_value = "Generated prompt for next steps"

        work_artifact = {"task_summary": "Test task summary", "task_description": "Test task description", "acceptance_criteria": ["Criterion 1", "Criterion 2"]}

        result = await submit_for_review("TEST-123", work_artifact)

        # Verify template was loaded
        mock_prompter._load_template.assert_called_with("artifacts", "gatherrequirements_artifact")

        # Verify artifact was built with metadata
        build_call_args = mock_artifact_manager.build_structured_artifact.call_args
        template, data = build_call_args[0]

        assert "task_summary" in data
        assert "task_description" in data
        assert "metadata" in data
        assert data["metadata"]["task_id"] == "TEST-123"
        assert data["metadata"]["phase"] == "gatherrequirements"
        assert data["metadata"]["status"] == "working"

        # Verify artifact was written
        mock_artifact_manager.write_artifact.assert_called_with("TEST-123", "Built artifact content")

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_submit_work_transitions_state_from_working_to_aireview(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review correctly transitions state from working to aireview"""
        # Mock existing task in working state
        mock_machine = Mock()
        mock_machine.state = "planning_working"
        mock_state_manager.get_machine.return_value = mock_machine

        # Mock template and artifact building
        mock_prompter._load_template.return_value = "Template"
        mock_artifact_manager.build_structured_artifact.return_value = "Artifact"
        mock_prompter.generate_prompt.return_value = "Generated prompt for next steps"

        work_artifact = {"scope_verification": "Verified", "technical_approach": "Approach"}

        result = await submit_for_review("TEST-456", work_artifact)

        # Verify state transition
        mock_machine.submit_for_ai_review.assert_called_once()
        mock_state_manager.save_machine_state.assert_called_with("TEST-456", mock_machine)

        assert result.status == "success"
        assert "planning_working" in result.message or "aireview" in result.message

    @pytest.mark.asyncio
    async def test_submit_work_validates_required_artifact_fields_per_phase(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review validates required artifact fields per phase"""
        test_cases = [
            ("gatherrequirements_working", {"task_summary": "Summary", "task_description": "Desc", "acceptance_criteria": []}),
            ("planning_strategy", {"high_level_strategy": "Strategy", "key_components": ["comp1"], "architectural_decisions": "Decisions", "risk_analysis": "Risks"}),
            ("coding_working", {"implementation_summary": "Summary", "execution_steps_completed": [], "testing_notes": "Notes"}),
            ("testing_working", {"test_results": {"command_run": "pytest", "exit_code": 0, "full_output": "All tests passed"}}),
            ("finalize_working", {"commit_hash": "abc123", "pull_request_url": "https://github.com/test/test/pull/1"}),
        ]

        for state, work_artifact in test_cases:
            # Mock task in specific state
            mock_machine = Mock()
            mock_machine.state = state
            mock_state_manager.get_machine.return_value = mock_machine

            # Mock template and artifact building
            phase = state.split("_")[0]
            mock_prompter._load_template.return_value = f"# {phase} template"
            mock_artifact_manager.build_structured_artifact.return_value = "Artifact"
            mock_prompter.generate_prompt.return_value = "Generated prompt for next steps"

            result = await submit_for_review("TEST-123", work_artifact)

            # Should succeed with valid fields
            if result.status != "success":
                pass
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_submit_work_handles_task_not_found_error(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review handles task not found error"""
        # Mock no existing task
        mock_state_manager.get_machine.return_value = None

        work_artifact = {"task_summary": "Summary"}

        result = await submit_for_review("NONEXISTENT-TASK", work_artifact)

        assert result.status == "error"
        assert "not found" in result.message

    @pytest.mark.asyncio
    async def test_submit_work_handles_invalid_state_transitions(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review handles invalid state transitions"""
        # Mock task in non-working state
        mock_machine = Mock()
        mock_machine.state = "gatherrequirements_devreview"
        # Use StateTransitionError instead of generic Exception
        from epic_task_manager.exceptions import StateTransitionError

        mock_machine.submit_for_ai_review.side_effect = StateTransitionError("Invalid transition", "gatherrequirements_devreview", "submit_for_ai_review")
        mock_state_manager.get_machine.return_value = mock_machine

        work_artifact = {"task_summary": "Summary"}

        result = await submit_for_review("INVALID-STATE", work_artifact)

        assert result.status == "error"
        assert "Invalid state transition" in result.message or "Invalid transition" in result.message
        assert "gatherrequirements_devreview" in result.message

    @pytest.mark.asyncio
    async def test_submit_work_adds_correct_metadata_to_artifact(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review adds correct metadata to work artifact"""
        # Mock task in coding state
        mock_machine = Mock()
        mock_machine.state = "coding_working"
        mock_state_manager.get_machine.return_value = mock_machine

        # Mock template and artifact building
        mock_prompter._load_template.return_value = "Template"
        mock_artifact_manager.build_structured_artifact.return_value = "Artifact"
        mock_prompter.generate_prompt.return_value = "Generated prompt for next steps"

        work_artifact = {"implementation_summary": "Summary", "execution_steps_completed": [], "testing_notes": "Test notes", "acceptance_criteria_met": ["Criteria met"]}

        await submit_for_review("TEST-123", work_artifact)

        # Verify metadata was added correctly
        build_call_args = mock_artifact_manager.build_structured_artifact.call_args
        template, data = build_call_args[0]

        metadata = data["metadata"]
        assert metadata["task_id"] == "TEST-123"
        assert metadata["phase"] == "coding"
        assert metadata["status"] == "working"
        assert metadata["version"] == "1.0"
        assert metadata["ai_model"] == "claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_submit_work_handles_template_loading_errors(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review handles template loading errors gracefully"""
        # Mock task in working state
        mock_machine = Mock()
        mock_machine.state = "testing_working"
        mock_state_manager.get_machine.return_value = mock_machine

        # Mock template loading failure
        mock_prompter._load_template.side_effect = FileNotFoundError("Template not found")

        work_artifact = {"test_results": {"command_run": "pytest", "exit_code": 0, "full_output": "All tests passed"}}

        result = await submit_for_review("TEST-124", work_artifact)

        assert result.status == "error"
        assert "Could not submit work" in result.message

    @pytest.mark.asyncio
    async def test_submit_work_handles_artifact_building_errors(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review handles artifact building errors gracefully"""
        # Mock task in working state
        mock_machine = Mock()
        mock_machine.state = "finalize_working"
        mock_state_manager.get_machine.return_value = mock_machine

        # Mock template loading success but artifact building failure
        mock_prompter._load_template.return_value = "Template"
        # Use ArtifactError instead of generic Exception
        from epic_task_manager.exceptions import ArtifactError

        mock_artifact_manager.build_structured_artifact.side_effect = ArtifactError("Build error")

        work_artifact = {"commit_hash": "abc123", "pull_request_url": "https://github.com/repo/pull/1"}

        result = await submit_for_review("TEST-125", work_artifact)

        assert result.status == "error"
        assert "Could not submit work" in result.message

    @pytest.mark.asyncio
    async def test_submit_work_returns_appropriate_review_prompt(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review returns appropriate prompt for AI self-review"""
        # Mock task in working state
        mock_machine = Mock()
        mock_machine.state = "gatherrequirements_working"
        mock_state_manager.get_machine.return_value = mock_machine

        # Mock template and artifact building
        mock_prompter._load_template.return_value = "Template"
        mock_artifact_manager.build_structured_artifact.return_value = "Artifact"
        mock_prompter.generate_prompt.return_value = "Please review the work and provide feedback"

        work_artifact = {"task_summary": "Summary", "task_description": "Description", "acceptance_criteria": []}

        result = await submit_for_review("TEST-126", work_artifact)

        assert result.status == "success"
        assert hasattr(result, "next_prompt")
        assert "review the work" in result.next_prompt

    @pytest.mark.asyncio
    async def test_submit_work_preserves_task_id_in_work_artifact(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review preserves task_id in work artifact data"""
        # Mock task in working state
        mock_machine = Mock()
        mock_machine.state = "planning_working"
        mock_state_manager.get_machine.return_value = mock_machine

        # Mock template and artifact building
        mock_prompter._load_template.return_value = "Template"
        mock_artifact_manager.build_structured_artifact.return_value = "Artifact"
        mock_prompter.generate_prompt.return_value = "Generated prompt for next steps"

        work_artifact = {"scope_verification": "Verified", "technical_approach": "Approach", "file_breakdown": []}

        result = await submit_for_review("TEST-128", work_artifact)

        # Verify task_id was added to work_artifact
        build_call_args = mock_artifact_manager.build_structured_artifact.call_args
        template, data = build_call_args[0]

        assert data["task_id"] == "TEST-128"
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_submit_work_handles_different_phase_templates(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review loads correct templates for different phases"""
        phases = ["gatherrequirements", "planning", "coding", "testing", "finalize"]

        for phase in phases:
            # Mock task in specific phase working state
            mock_machine = Mock()
            mock_machine.state = f"{phase}_working"
            mock_state_manager.get_machine.return_value = mock_machine

            # Mock template and artifact building
            mock_prompter._load_template.return_value = f"{phase} template"
            mock_artifact_manager.build_structured_artifact.return_value = "Artifact"
            mock_prompter.generate_prompt.return_value = "Generated prompt for next steps"

            # Use minimal valid artifact for each phase
            valid_artifacts = {
                "gatherrequirements": {"task_summary": "Summary", "task_description": "Description", "acceptance_criteria": []},
                "planning": {"scope_verification": "Verified", "technical_approach": "Approach", "file_breakdown": []},
                "coding": {"implementation_summary": "Summary", "execution_steps_completed": [], "testing_notes": "Notes", "acceptance_criteria_met": []},
                "testing": {"test_results": {"command_run": "pytest", "exit_code": 0, "full_output": "Tests passed"}},
                "finalize": {"commit_hash": "abc123", "pull_request_url": "https://github.com/test/pull/1"},
            }
            work_artifact = valid_artifacts.get(phase, {"task_summary": "Summary", "task_description": "Description", "acceptance_criteria": []})

            result = await submit_for_review(f"TEST-{ord(phase[0]):03d}", work_artifact)

            # Verify correct template was requested
            mock_prompter._load_template.assert_called_with("artifacts", f"{phase}_artifact")
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_submit_work_validates_machine_state_before_submission(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review validates machine is in valid state before submission"""
        invalid_states = ["gatherrequirements_aireview", "planning_devreview", "coding_verified"]

        for state in invalid_states:
            # Mock task in invalid state
            mock_machine = Mock()
            mock_machine.state = state
            # Use StateTransitionError instead of generic Exception
            from epic_task_manager.exceptions import StateTransitionError

            mock_machine.submit_for_ai_review.side_effect = StateTransitionError("Invalid transition", state, "submit_for_ai_review")
            mock_state_manager.get_machine.return_value = mock_machine

            work_artifact = {"task_summary": "Summary", "task_description": "Description", "acceptance_criteria": []}

            result = await submit_for_review(f"TEST-{hash(state) % 1000:03d}", work_artifact)

            # Should handle invalid state gracefully
            assert result.status == "error"
            assert "Invalid state transition" in result.message or "Invalid transition" in result.message

    @pytest.mark.asyncio
    async def test_submit_work_response_format_consistency(self, initialized_project, mock_state_manager, mock_artifact_manager, mock_prompter):
        """Test submit_for_review responses follow consistent format"""
        # Mock successful submission
        mock_machine = Mock()
        mock_machine.state = "gatherrequirements_working"
        mock_state_manager.get_machine.return_value = mock_machine

        mock_prompter._load_template.return_value = "Template"
        mock_artifact_manager.build_structured_artifact.return_value = "Artifact"
        mock_prompter.generate_prompt.return_value = "Generated prompt for next steps"

        work_artifact = {"task_summary": "Summary", "task_description": "Description", "acceptance_criteria": []}

        result = await submit_for_review("TEST-127", work_artifact)

        # Verify response format
        assert hasattr(result, "status")
        assert hasattr(result, "message")
        assert hasattr(result, "next_prompt")
        assert result.status == "success"
        assert isinstance(result.message, str)
        assert isinstance(result.next_prompt, str)
        assert len(result.message) > 0
        assert len(result.next_prompt) > 0
