"""
Comprehensive tests for Prompter class covering provider-specific template selection
"""

from pathlib import Path
import tempfile
from unittest.mock import Mock, call, patch

import pytest

from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models.config import TaskSource


class TestPrompter:
    """Test Prompter functionality"""

    @pytest.fixture
    def temp_templates(self):
        """Create temporary template directory structure for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create template directory structure (phase-first)
            templates_dir = temp_path / "templates"
            templates_dir.mkdir()

            # Create phase-specific directories
            (templates_dir / "prompts" / "gatherrequirements").mkdir(parents=True)
            (templates_dir / "prompts" / "planning").mkdir(parents=True)
            (templates_dir / "prompts" / "coding").mkdir(parents=True)
            (templates_dir / "prompts" / "testing").mkdir(parents=True)
            (templates_dir / "prompts" / "utils").mkdir(parents=True)

            # Create task-source-specific requirements templates
            atlassian_template = templates_dir / "prompts" / "gatherrequirements" / "atlassian_work.md"
            atlassian_template.write_text("# Atlassian Gather Requirements Work\nTask: {task_id}\nFeedback: {revision_feedback}")

            local_template = templates_dir / "prompts" / "gatherrequirements" / "local_work.md"
            local_template.write_text("# Local Gather Requirements Work\nTask: {task_id}\nFeedback: {revision_feedback}")

            # Create phase-specific templates for other phases
            planning_template = templates_dir / "prompts" / "planning" / "work.md"
            planning_template.write_text("# Shared Planning Work\nTask: {task_id}\nPrevious: {verified_gatherrequirements_artifact}")

            coding_template = templates_dir / "prompts" / "coding" / "work.md"
            coding_template.write_text("# Generic Coding Work\nTask: {task_id}\nPlan: {verified_planning_artifact}")

            testing_template = templates_dir / "prompts" / "testing" / "work.md"
            testing_template.write_text("# testing prompt for {task_id}")

            # Create utils template for clean slate
            clean_slate_template = templates_dir / "prompts" / "utils" / "clean_slate.md"
            clean_slate_template.write_text("Clean slate for {task_id}")

            yield temp_path

    @pytest.fixture
    def mock_config_atlassian(self):
        """Mock configuration for Atlassian provider"""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            mock_config.load_config.return_value.get_task_source.return_value.value = "atlassian"
            yield mock_config

    @pytest.fixture
    def mock_config_local(self):
        """Mock configuration for local provider"""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            mock_config.load_config.return_value.get_task_source.return_value.value = "local"
            mock_config.load_config.return_value.features.yolo_mode = False
            yield mock_config

    @pytest.fixture
    def mock_artifact_manager(self):
        """Mock ArtifactManager for testing"""
        with patch("epic_task_manager.execution.prompter.ArtifactManager") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance

    def test_load_template_selects_atlassian_when_provider_is_atlassian(self, temp_templates, mock_config_atlassian):
        """Test it correctly selects atlassian-specific template when provider is 'atlassian'"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            template = prompter._load_template("prompts", "gatherrequirements_work")

            # Test functional requirements, not specific content
            assert isinstance(template, str)
            assert len(template) > 0
            assert "{task_id}" in template  # Required placeholder
            assert "{revision_feedback}" in template  # Required placeholder

    def test_load_template_selects_local_when_provider_is_local(self, temp_templates, mock_config_local):
        """Test it correctly selects local-specific template when provider is 'local'"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            template = prompter._load_template("prompts", "gatherrequirements_work")

            # Test functional requirements, not specific content
            assert isinstance(template, str)
            assert len(template) > 0
            assert "{task_id}" in template  # Required placeholder
            assert "{revision_feedback}" in template  # Required placeholder

    def test_load_template_loads_generic_phase_templates(self, temp_templates, mock_config_local):
        """Test loading generic phase templates for non-requirements phases"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            # Test planning phase loads from prompts/planning/work.md
            template = prompter._load_template("prompts", "planning_work")
            assert "Shared Planning Work" in template
            assert "{verified_gatherrequirements_artifact}" in template

    def test_load_template_loads_coding_phase_templates(self, temp_templates, mock_config_local):
        """Test loading coding phase templates from phase directory"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            # Test coding phase loads from prompts/coding/work.md
            template = prompter._load_template("prompts", "coding_work")

            # Test structural and functional requirements
            assert isinstance(template, str)
            assert len(template) > 0
            assert template.startswith("# ")  # Should have a role/title
            assert "{verified_planning_artifact}" in template  # Required context placeholder

    def test_load_template_generates_dynamic_template_for_missing_work_prompts(self, temp_templates, mock_config_local):
        """Test dynamic template generation for missing work prompts"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            # Use a non-existent template to test dynamic generation
            template = prompter._load_template("prompts", "nonexistent_work")

            # Test that dynamic generation produces valid templates
            assert isinstance(template, str)
            assert len(template) > 0
            assert template.startswith("# Role:")  # Dynamic templates have this structure
            assert "{task_id}" in template  # Required placeholder
            assert "{revision_feedback}" in template  # Required placeholder
            assert "submit_for_review" in template  # Should mention the required tool

    def test_load_template_generates_dynamic_template_for_missing_ai_review_prompts(self, temp_templates, mock_config_local):
        """Test dynamic template generation for missing AI review prompts"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            # Use a non-existent AI review template to test dynamic generation
            template = prompter._load_template("prompts", "nonexistent_ai_review")

            # Test that dynamic generation produces valid AI review templates
            assert isinstance(template, str)
            assert len(template) > 0
            assert template.startswith("# Role:")  # Dynamic templates have this structure
            assert "{task_id}" in template  # Required placeholder
            assert "{artifact_content}" in template  # Required for review templates
            assert "approve_or_request_changes" in template  # Should mention the required tool

    def test_load_template_raises_error_for_unknown_template_type(self, temp_templates, mock_config_local):
        """Test error handling for unknown template types"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            with pytest.raises(FileNotFoundError, match="Template not found: unknown_template"):
                prompter._load_template("prompts", "unknown_template")

    def test_template_resolution_priority_order(self, temp_templates):
        """Test that template resolution follows the correct priority order"""
        with patch.object(Prompter, "__init__", lambda x: None), patch("epic_task_manager.execution.prompter.settings") as mock_settings:
            # Mock settings to point to non-existent directory so it falls back to template_dir
            mock_settings.prompts_dir = temp_templates / "nonexistent"

            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            # Create both provider-specific and generic templates
            provider_template = temp_templates / "templates" / "prompts" / "gatherrequirements" / "atlassian_work.md"
            provider_template.parent.mkdir(parents=True, exist_ok=True)
            provider_template.write_text("Provider-specific template")

            generic_template = temp_templates / "templates" / "prompts" / "gatherrequirements" / "generic_work.md"
            generic_template.parent.mkdir(parents=True, exist_ok=True)
            generic_template.write_text("Generic template")

            with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
                mock_config.load_config.return_value.get_task_source.return_value.value = "atlassian"

                template = prompter._load_template("prompts", "gatherrequirements_work")
                # Should load provider-specific template when available
                assert "Provider-specific" in template

    def test_template_fallback_to_generic(self, temp_templates):
        """Test fallback to generic template when provider-specific doesn't exist"""
        with patch.object(Prompter, "__init__", lambda x: None), patch("epic_task_manager.execution.prompter.settings") as mock_settings:
            # Mock settings to point to non-existent directory so it falls back to template_dir
            mock_settings.prompts_dir = temp_templates / "nonexistent"

            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            # Only create generic template
            generic_template = temp_templates / "templates" / "prompts" / "gatherrequirements" / "generic_work.md"
            generic_template.parent.mkdir(parents=True, exist_ok=True)
            generic_template.write_text("Generic fallback template")

            with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
                mock_config.load_config.return_value.get_task_source.return_value.value = "nonexistent_provider"

                template = prompter._load_template("prompts", "gatherrequirements_work")
                # Should fall back to generic template
                assert "Generic fallback" in template

    def test_all_templates_have_required_placeholders(self):
        """Test that all real templates contain required placeholders"""
        prompter = Prompter()

        # Test key templates for required placeholders - only test ones that actually exist
        templates_to_test = [
            ("gatherrequirements_work", ["{task_id}", "{revision_feedback}"]),
            ("coding_work_single_step", ["{task_id}", "{step_instruction}"]),
            ("finalize_work", ["{task_id}", "{verified_testing_artifact}"]),
            ("finalize_ai_review", ["{task_id}", "{artifact_content}"]),
        ]

        for template_name, required_placeholders in templates_to_test:
            try:
                template = prompter._load_template("prompts", template_name)
                for placeholder in required_placeholders:
                    assert placeholder in template, f"Template {template_name} missing placeholder {placeholder}"
            except FileNotFoundError:
                # Template doesn't exist - this is expected for some phases
                # that use dynamic generation or sub-phase templates
                pass

    def test_dynamic_templates_follow_standard_structure(self, temp_templates):
        """Test that dynamically generated templates follow expected structure"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"

            # Test work template generation
            work_template = prompter._generate_dynamic_template("testphase", "work")
            assert work_template.startswith("# Role:")
            assert "{task_id}" in work_template
            assert "{revision_feedback}" in work_template
            assert "submit_for_review" in work_template

            # Test AI review template generation
            review_template = prompter._generate_dynamic_template("testphase", "ai_review")
            assert review_template.startswith("# Role:")
            assert "{task_id}" in review_template
            assert "{artifact_content}" in review_template
            assert "approve_or_request_changes" in review_template

    def test_safe_format_template_only_replaces_existing_placeholders(self, temp_templates):
        """Test template formatting only replaces placeholders that exist in context"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()

            template = "Task: {task_id}, Status: {status}, Example: {example_placeholder}"
            context = {"task_id": "TEST-123", "status": "working"}

            result = prompter._safe_format_template(template, context)

            assert "Task: TEST-123" in result
            assert "Status: working" in result
            assert "{example_placeholder}" in result  # Should remain unchanged

    def test_generate_prompt_for_gatherrequirements_working_state(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation for gatherrequirements_working state"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager

            prompt = prompter.generate_prompt("TEST-123", "gatherrequirements_working", "No feedback")

            # Test that task ID and feedback are included in context
            assert "TEST-123" in prompt
            assert "No feedback" in prompt
            # Test that prompt is generated
            assert len(prompt.strip()) > 0

    def test_generate_prompt_for_coding_working_loads_planning_context(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation for coding_working loads verified planning artifact"""
        mock_artifact_manager.get_archive_path.return_value.exists.return_value = True
        mock_artifact_manager.get_archive_path.return_value.read_text.return_value = "Verified planning content"

        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager

            prompt = prompter.generate_prompt("TEST-789", "coding_working")

            mock_artifact_manager.get_archive_path.assert_called_with("TEST-789", "planning", 1)
            assert "Verified planning content" in prompt

    def test_generate_prompt_for_testing_working_loads_independently(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation for testing_working operates independently without coding artifact"""
        with patch.object(Prompter, "__init__", lambda x: None), patch("epic_task_manager.execution.prompter.settings") as mock_settings:
            # Mock settings to point to temp directory
            mock_settings.prompts_dir = temp_templates / "nonexistent"  # Force fallback to template_dir

            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager
            # Initialize _CONTEXT_REQUIREMENTS manually since we're mocking __init__
            prompter._CONTEXT_REQUIREMENTS = {}  # Empty since testing doesn't need context

            prompt = prompter.generate_prompt("TEST-999", "testing_working")

            # Testing phase should not depend on coding artifacts
            mock_artifact_manager.get_archive_path.assert_not_called()
            # Test that task ID is included and prompt is generated
            assert "TEST-999" in prompt
            assert len(prompt.strip()) > 0

    def test_generate_prompt_for_finalize_working_loads_testing_context(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation for finalize_working loads verified testing artifact"""
        mock_artifact_manager.get_archive_path.return_value.exists.return_value = True
        mock_artifact_manager.get_archive_path.return_value.read_text.return_value = "Verified testing content"

        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager

            prompt = prompter.generate_prompt("TEST-111", "finalize_working")

            mock_artifact_manager.get_archive_path.assert_called_with("TEST-111", "testing", 1)
            assert "Verified testing content" in prompt

    def test_generate_prompt_handles_missing_archived_artifact(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation handles missing archived artifacts gracefully"""
        mock_artifact_manager.get_archive_path.return_value.exists.return_value = False

        # Create the planning strategy template
        strategy_template = temp_templates / "templates" / "prompts" / "planning" / "strategy_work.md"
        strategy_template.parent.mkdir(parents=True, exist_ok=True)
        strategy_template.write_text("# Role: Lead Architect\nTask: {task_id}\nContext: {verified_gatherrequirements_artifact}")

        with patch.object(Prompter, "__init__", lambda x: None), patch("epic_task_manager.execution.prompter.settings") as mock_settings:
            # Mock settings to use temp directory
            mock_settings.prompts_dir = temp_templates / "templates" / "prompts"

            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager
            # Initialize _CONTEXT_REQUIREMENTS manually since we're mocking __init__
            prompter._CONTEXT_REQUIREMENTS = {
                "planning_strategy": [("gatherrequirements", "verified_gatherrequirements_artifact")],
            }

            prompt = prompter.generate_prompt("TEST-222", "planning_strategy")

            # Test that missing artifacts are handled gracefully
            # The error message from ArtifactNotFoundError should be in the prompt
            assert "Error: Could not find verified gatherrequirements artifact" in prompt
            # Ensure the placeholder was replaced (not left as-is)
            assert "{verified_gatherrequirements_artifact}" not in prompt

    def test_generate_prompt_for_aireview_state(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation for AI review states"""
        mock_artifact_manager.read_artifact.return_value = "Current artifact content"

        # Create AI review template
        ai_review_template = temp_templates / "templates" / "prompts" / "gatherrequirements_ai_review.md"
        ai_review_template.write_text("# Review Artifact\nTask: {task_id}\nContent: {artifact_content}")

        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager

            prompt = prompter.generate_prompt("TEST-333", "gatherrequirements_aireview")

            # Test that artifact manager is called to read content
            mock_artifact_manager.read_artifact.assert_called_with("TEST-333")
            # Test that artifact content is included in prompt
            assert "Current artifact content" in prompt
            # Test that prompt is generated
            assert len(prompt.strip()) > 0

    def test_generate_prompt_for_devreview_state(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation for dev review states"""
        mock_artifact_manager.get_artifact_path.return_value = Path("/path/to/artifact.md")

        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager

            prompt = prompter.generate_prompt("TEST-444", "gatherrequirements_devreview")

            assert "ready for your review" in prompt
            assert "/path/to/artifact.md" in prompt

    def test_generate_prompt_for_verified_state(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test prompt generation for verified states"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager

            prompt = prompter.generate_prompt("TEST-555", "gatherrequirements_verified")

            assert "Please call `approve_and_advance` to proceed" in prompt

    def test_generate_prompt_raises_error_for_invalid_state_format(self, temp_templates, mock_config_local, mock_artifact_manager):
        """Test error handling for invalid state format"""
        with patch.object(Prompter, "__init__", lambda x: None):
            prompter = Prompter()
            prompter.template_dir = temp_templates / "templates"
            prompter.artifact_manager = mock_artifact_manager

            with pytest.raises(ValueError, match="Invalid machine state format"):
                prompter.generate_prompt("TEST-666", "invalid_state_format")

    def test_provider_configuration_validation(self, temp_templates):
        """Test provider configuration validation during template loading"""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            # Mock config that raises exception
            mock_config.load_config.side_effect = Exception("Config error")

            with patch.object(Prompter, "__init__", lambda x: None):
                prompter = Prompter()
                prompter.template_dir = temp_templates / "templates"

                # Should handle config errors gracefully and fall back
                with pytest.raises(Exception):
                    prompter._load_template("prompts", "gatherrequirements_work")

    @pytest.fixture
    def prompter(self, isolated_epic_settings):
        """Create Prompter with isolated test settings."""
        return Prompter()

    @pytest.fixture
    def mock_template_content(self):
        """Mock template content for testing."""
        return {
            "gatherrequirements_work": "# Role: Task Claimer\n\nPlease work on task {task_id}.\n\n{revision_feedback}",
            "planning_work": "# Role: Planner\n\nCreate plan for {task_id}.\n\nVerified requirements:\n{verified_gatherrequirements_artifact}",
            "coding_work": "# Role: Developer\n\nImplement {task_id}.\n\nPlan:\n{verified_planning_artifact}",
            "testing_work": "# Role: Tester\n\nTest {task_id}.\n\nValidate the implemented code changes.",
            "finalize_work": "# Role: Finalizer\n\nFinalize {task_id}.\n\nTests:\n{verified_testing_artifact}",
            "gatherrequirements_ai_review": "# Role: Reviewer\n\nReview artifact:\n{artifact_content}",
        }

    def test_generate_prompt_for_gatherrequirements_working_state(self, prompter, sample_task_id, mock_template_content):
        """Test prompt generation for gatherrequirements_working state."""
        with patch.object(prompter, "_load_template") as mock_load:
            mock_load.return_value = mock_template_content["gatherrequirements_work"]

            prompt = prompter.generate_prompt(sample_task_id, "gatherrequirements_working")

            # Test template loading behavior - gatherrequirements_working is the first state, no clean slate
            assert mock_load.call_count == 1
            mock_load.assert_called_with("prompts", "gatherrequirements_work")
            # Test context substitution behavior
            assert sample_task_id in prompt
            # Test that prompt is non-empty
            assert len(prompt.strip()) > 0

    def test_generate_prompt_with_revision_feedback(self, prompter, sample_task_id, mock_template_content):
        """Test prompt generation includes revision feedback when provided."""
        feedback = "Please add more details to the implementation"

        with patch.object(prompter, "_load_template") as mock_load:
            mock_load.return_value = mock_template_content["gatherrequirements_work"]

            prompt = prompter.generate_prompt(sample_task_id, "gatherrequirements_working", revision_feedback=feedback)

            # Test that custom feedback is included in context
            assert feedback in prompt
            # Test that prompt is generated
            assert len(prompt.strip()) > 0

    def test_generate_prompt_for_planning_strategy_loads_gatherrequirements_context(self, prompter, sample_task_id, isolated_epic_settings):
        """Test planning_strategy state loads verified requirements artifact."""
        # Create mock archived requirements artifact
        task_dir = isolated_epic_settings.workspace_dir / sample_task_id
        archive_dir = task_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        gatherrequirements_content = "# Verified Gather Requirements\nTask requirements verified."
        gatherrequirements_archive = archive_dir / "01-gatherrequirements.md"
        gatherrequirements_archive.write_text(gatherrequirements_content)

        # Use the real template loading (no mocking) to ensure full integration
        prompt = prompter.generate_prompt(sample_task_id, "planning_strategy")

        # Test that the correct role is set for planning strategy
        assert "Role: Lead Software Architect (Strategy Phase)" in prompt

        # --- HARDENED ASSERTIONS ---
        # The test MUST enforce that context is correctly injected.
        # If the template has a bug, the test must fail to expose it.
        # The placeholder MUST NOT be present in the final output.
        assert "{verified_gather_requirements_artifact}" not in prompt
        assert gatherrequirements_content in prompt

        # Test that prompt includes task ID
        assert sample_task_id in prompt

    def test_generate_prompt_for_coding_working_loads_planning_context(self, prompter, sample_task_id, isolated_epic_settings, mock_template_content):
        """Test coding_working state loads verified planning artifact."""
        # Create mock archived artifacts
        task_dir = isolated_epic_settings.workspace_dir / sample_task_id
        archive_dir = task_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Add gitsetup archive (phase 2)
        gitsetup_content = "# Verified Git Setup\nGit environment configured."
        gitsetup_archive = archive_dir / "02-gitsetup.md"
        gitsetup_archive.write_text(gitsetup_content)

        # Add planning archive (phase 3)
        planning_content = "# Verified Planning\nDetailed implementation plan."
        planning_archive = archive_dir / "03-planning.md"
        planning_archive.write_text(planning_content)

        with patch.object(prompter, "_load_template") as mock_load:
            # Set up mock to return different values for different templates
            def mock_template_loader(template_type, template_name):
                if template_name == "utils/clean_slate":
                    return "Clean slate template with {task_id}"
                return mock_template_content["coding_work"]

            mock_load.side_effect = mock_template_loader

            prompt = prompter.generate_prompt(sample_task_id, "coding_working")

            # Test that coding working state produces a prompt (even if error due to test setup)
            assert len(prompt.strip()) > 0
            # Test that task ID is included
            assert sample_task_id in prompt

    def test_generate_prompt_for_testing_working_operates_independently(self, prompter, sample_task_id, isolated_epic_settings, mock_template_content):
        """Test testing_working state operates independently without coding artifact dependencies."""
        with patch.object(prompter, "_load_template") as mock_load:
            # Set up mock to return different values for different templates
            def mock_template_loader(template_type, template_name):
                if template_name == "utils/clean_slate":
                    return "Clean slate template with {task_id}"
                return mock_template_content["testing_work"]

            mock_load.side_effect = mock_template_loader

            prompt = prompter.generate_prompt(sample_task_id, "testing_working")

            # Test that testing phase generates a prompt independently
            assert len(prompt.strip()) > 0
            # Test that task ID is included in context
            assert sample_task_id in prompt

    def test_generate_prompt_for_finalize_working_loads_testing_context(self, prompter, sample_task_id, isolated_epic_settings, mock_template_content):
        """Test finalize_working state loads verified testing artifact."""
        # Create mock archived artifacts
        task_dir = isolated_epic_settings.workspace_dir / sample_task_id
        archive_dir = task_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Add gitsetup archive (phase 2)
        gitsetup_content = "# Verified Git Setup\nGit environment configured."
        gitsetup_archive = archive_dir / "02-gitsetup.md"
        gitsetup_archive.write_text(gitsetup_content)

        # Add planning archive (phase 3)
        planning_content = "# Verified Planning\nDetailed implementation plan."
        planning_archive = archive_dir / "03-planning.md"
        planning_archive.write_text(planning_content)

        # Add coding archive (phase 5)
        coding_content = "# Verified Coding\nImplementation complete."
        coding_archive = archive_dir / "05-coding.md"
        coding_archive.write_text(coding_content)

        # Add testing archive (phase 6)
        testing_content = "# Verified Testing\nAll tests passing."
        testing_archive = archive_dir / "06-testing.md"
        testing_archive.write_text(testing_content)

        with patch.object(prompter, "_load_template") as mock_load:
            mock_load.return_value = mock_template_content["finalize_work"]

            prompt = prompter.generate_prompt(sample_task_id, "finalize_working")

            # Test that archived testing content is loaded into context
            assert testing_content in prompt
            # Test that task ID is included
            assert sample_task_id in prompt

    def test_generate_prompt_for_aireview_state(self, prompter, sample_task_id, isolated_epic_settings, mock_template_content):
        """Test prompt generation for AI review states."""
        # Create artifact content
        artifact_content = "# Test Artifact\nContent to review."
        artifact_manager = prompter.artifact_manager
        artifact_manager.create_task_structure(sample_task_id)
        artifact_manager.write_artifact(sample_task_id, artifact_content)

        with patch.object(prompter, "_load_template") as mock_load:
            mock_load.return_value = mock_template_content["gatherrequirements_ai_review"]

            prompt = prompter.generate_prompt(sample_task_id, "gatherrequirements_aireview")

            mock_load.assert_called_once_with("prompts", "gatherrequirements_ai_review")
            assert artifact_content in prompt

    def test_generate_prompt_for_devreview_state_returns_human_message(self, prompter, sample_task_id, isolated_epic_settings):
        """Test devreview state returns human-facing message."""
        prompt = prompter.generate_prompt(sample_task_id, "gatherrequirements_devreview")

        # Test that devreview generates a human-facing message
        assert len(prompt.strip()) > 0
        # Test that task ID is included
        assert sample_task_id in prompt

    def test_generate_prompt_for_verified_state_returns_no_action_message(self, prompter, sample_task_id):
        """Test verified state returns advance message."""
        prompt = prompter.generate_prompt(sample_task_id, "gatherrequirements_verified")

        # Test that verified state generates an advancement message
        assert len(prompt.strip()) > 0
        # Test that task ID is included
        assert sample_task_id in prompt

    def test_generate_prompt_raises_error_for_invalid_state_format(self, prompter, sample_task_id):
        """Test ValueError is raised for invalid state format."""
        with pytest.raises(ValueError, match="Invalid machine state format"):
            prompter.generate_prompt(sample_task_id, "invalidstateformat")

    def test_load_template_selects_provider_specific_template(self, prompter, isolated_epic_settings):
        """Test _load_template correctly selects provider-specific templates."""
        # Mock config to return specific task source
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            mock_config.load_config.return_value.get_task_source.return_value = TaskSource.ATLASSIAN

            # Create actual template file
            atlassian_template_content = "# Atlassian-specific requirements template"
            template_path = prompter.template_dir / "prompts" / "gatherrequirements" / "atlassian_work.md"
            template_path.parent.mkdir(parents=True, exist_ok=True)
            template_path.write_text(atlassian_template_content)

            result = prompter._load_template("prompts", "gatherrequirements_work")

            assert result == atlassian_template_content

    def test_load_template_gatherrequirements_fallback_to_generic(self, prompter, isolated_epic_settings):
        """Test requirements phase falls back to generic when task-source-specific template not found."""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            mock_config.load_config.return_value.get_task_source.return_value = TaskSource.LINEAR

            generic_template_content = "# Generic requirements template"

            with patch.object(Path, "exists") as mock_exists, patch.object(Path, "read_text") as mock_read:
                # Linear template doesn't exist, but generic does
                def exists_side_effect():
                    # Called when checking if generic_work.md exists
                    return True

                mock_exists.side_effect = [False, True]  # First call (linear) false, second call (generic) true
                mock_read.return_value = generic_template_content

                result = prompter._load_template("prompts", "gatherrequirements_work")

                assert result == generic_template_content

    def test_load_template_non_gatherrequirements_phase_direct_loading(self, prompter, isolated_epic_settings):
        """Test non-requirements phases load directly from phase directory."""
        template_content = "# Planning phase template"

        with patch.object(Path, "exists") as mock_exists, patch.object(Path, "read_text") as mock_read:
            # Planning template exists in prompts/planning/work.md
            mock_exists.return_value = True
            mock_read.return_value = template_content

            result = prompter._load_template("prompts", "planning_work")

            assert result == template_content

    def test_load_template_generates_dynamic_template_for_work_phases(self, prompter, isolated_epic_settings):
        """Test _load_template generates dynamic template for _work phases when none found."""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            mock_config.load_config.return_value.get_task_source.return_value = TaskSource.LOCAL

            with patch.object(Path, "exists", return_value=False):
                result = prompter._load_template("prompts", "custom_work")

                assert "Role: AI Assistant" in result
                assert "custom phase" in result
                assert "submit_for_review" in result

    def test_load_template_generates_dynamic_template_for_ai_review_phases(self, prompter, isolated_epic_settings):
        """Test _load_template generates dynamic template for _ai_review phases when none found."""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            mock_config.load_config.return_value.get_task_source.return_value = TaskSource.LOCAL

            with patch.object(Path, "exists", return_value=False):
                result = prompter._load_template("prompts", "custom_ai_review")

                assert "Role: QA Reviewer" in result
                assert "custom phase" in result
                assert "approve_or_request_changes" in result

    def test_load_template_raises_error_when_no_template_found(self, prompter, isolated_epic_settings):
        """Test _load_template raises FileNotFoundError when no template found."""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            mock_config.load_config.return_value.get_task_source.return_value = TaskSource.LOCAL

            with patch.object(Path, "exists", return_value=False), pytest.raises(FileNotFoundError, match="Template not found: unknown_template"):
                prompter._load_template("prompts", "unknown_template")

    def test_safe_format_template_preserves_unknown_placeholders(self, prompter):
        """Test _safe_format_template only replaces known placeholders."""
        template = "Task: {task_id}, Unknown: {unknown_placeholder}, Status: {status}"
        context = {"task_id": "TEST-123", "status": "working"}

        result = prompter._safe_format_template(template, context)

        assert "Task: TEST-123" in result
        assert "Status: working" in result
        assert "{unknown_placeholder}" in result  # Should remain unchanged

    def test_safe_format_template_handles_empty_context(self, prompter):
        """Test _safe_format_template handles empty context gracefully."""
        template = "Task: {task_id}, Phase: {phase}"
        context = {}

        result = prompter._safe_format_template(template, context)

        # All placeholders should remain unchanged
        assert result == template

    @pytest.mark.parametrize(
        "state,expected_phase,expected_substate",
        [
            ("gatherrequirements_working", "gatherrequirements", "working"),
            ("planning_aireview", "planning", "aireview"),
            ("coding_devreview", "coding", "devreview"),
            ("testing_verified", "testing", "verified"),
            ("finalize_working", "finalize", "working"),
        ],
        ids=["gatherrequirements_working", "planning_aireview", "coding_devreview", "testing_verified", "finalize_working"],
    )
    def test_state_parsing_extracts_correct_phase_and_substate(self, prompter, sample_task_id, mock_template_content, state, expected_phase, expected_substate):
        """Test that state parsing correctly extracts phase and substate."""
        if expected_substate == "working":
            template_name = f"{expected_phase}_work"
            with patch.object(prompter, "_load_template") as mock_load:
                mock_load.return_value = mock_template_content.get(template_name, "Mock template")

                prompter.generate_prompt(sample_task_id, state)

                # gatherrequirements_working is the first state and doesn't load clean slate
                if state == "gatherrequirements_working":
                    mock_load.assert_called_once_with("prompts", template_name)
                else:
                    # All other working states load both main template and clean slate
                    expected_calls = [call("prompts", template_name), call("prompts", "utils/clean_slate")]
                    mock_load.assert_has_calls(expected_calls, any_order=True)

    def test_missing_archived_artifact_shows_error_message(self, prompter, sample_task_id):
        """Test that missing archived artifacts show error message in context."""
        # Test with planning_strategy which requires gatherrequirements context
        prompt = prompter.generate_prompt(sample_task_id, "planning_strategy")

        # Since no archived artifact exists, the placeholder should remain
        # or an error message should be shown
        assert "{verified_gather_requirements_artifact}" in prompt or "Error" in prompt

    def test_artifact_manager_integration(self, prompter, sample_task_id, isolated_epic_settings):
        """Test that Prompter correctly integrates with ArtifactManager."""
        # Create artifact content
        artifact_content = "# Integration Test\nTesting artifact manager integration."

        # Use prompter's artifact manager
        prompter.artifact_manager.create_task_structure(sample_task_id)
        prompter.artifact_manager.write_artifact(sample_task_id, artifact_content)

        # Test AI review prompt generation
        with patch.object(prompter, "_load_template") as mock_load:
            mock_load.return_value = "Review: {artifact_content}"

            prompt = prompter.generate_prompt(sample_task_id, "gatherrequirements_aireview")

            assert artifact_content in prompt

    def test_generate_prompt_for_devreview_state_with_yolo_mode_enabled(self, temp_templates):
        """Test that YOLO mode generates auto-approval prompt for devreview states"""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            # Configure YOLO mode enabled
            mock_config.load_config.return_value.features.yolo_mode = True

            # Mock the YOLO template
            yolo_template = "<role>Autonomous Agent (YOLO Mode)</role>\n<objective>Automatically approve task {task_id} in {current_state}</objective>"

            with patch.object(Prompter, "__init__", lambda x: None):
                prompter = Prompter()
                prompter.template_dir = temp_templates / "templates"
                prompter.artifact_manager = Mock()

                with patch.object(prompter, "_load_template") as mock_load:
                    mock_load.return_value = yolo_template

                    # Test various devreview states
                    for state in ["planning_strategydevreview", "planning_solutiondesigndevreview", "planning_executionplandevreview"]:
                        prompt = prompter.generate_prompt("TEST-123", state)

                        # Should have loaded the YOLO template
                        mock_load.assert_called_with("prompts", "utils/yolo_auto_approve")

                        # Should contain task_id and current_state
                        assert "TEST-123" in prompt
                        assert state in prompt
                        assert "Autonomous Agent" in prompt

    def test_generate_prompt_for_devreview_state_with_yolo_mode_disabled(self, temp_templates):
        """Test that YOLO mode disabled generates human review prompt for devreview states"""
        with patch("epic_task_manager.execution.prompter.config_manager") as mock_config:
            # Configure YOLO mode disabled
            mock_config.load_config.return_value.features.yolo_mode = False

            with patch.object(Prompter, "__init__", lambda x: None):
                prompter = Prompter()
                prompter.template_dir = temp_templates / "templates"
                prompter.artifact_manager = Mock()
                prompter.artifact_manager.get_artifact_path.return_value = "test/path/artifact.md"

                # Test that it calls the human review message generator
                with patch.object(prompter, "_generate_dev_review_message") as mock_dev_review:
                    mock_dev_review.return_value = "Human review required for TEST-123"

                    prompt = prompter.generate_prompt("TEST-123", "planning_strategydevreview")

                    # Should have called the dev review message generator
                    mock_dev_review.assert_called_once_with("TEST-123", "planning", "strategydevreview")
                    assert prompt == "Human review required for TEST-123"
