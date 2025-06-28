"""
Comprehensive tests for ArtifactManager class covering directory structure, YAML handling, and archiving
"""

import pytest

from epic_task_manager.constants import ARCHIVE_DIR_NAME, ARTIFACT_FILENAME, PHASE_NUMBERS
from epic_task_manager.execution.artifact_manager import ArtifactManager


class TestArtifactManager:
    """Test ArtifactManager functionality"""

    @pytest.fixture
    def artifact_manager(self, isolated_epic_settings):
        """Create ArtifactManager with isolated test settings."""
        return ArtifactManager()

    def test_create_task_structure_builds_correct_directory_layout(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test create_task_structure builds the correct workspace/ and archive/ directory layout."""
        # Create task structure
        artifact_manager.create_task_structure(sample_task_id)

        # Verify workspace directory structure
        task_dir = isolated_epic_settings.workspace_dir / sample_task_id
        assert task_dir.exists()
        assert task_dir.is_dir()

        # Verify archive directory
        archive_dir = task_dir / ARCHIVE_DIR_NAME
        assert archive_dir.exists()
        assert archive_dir.is_dir()

    def test_get_task_dir_returns_correct_path(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test get_task_dir returns correct path within workspace."""
        task_dir = artifact_manager.get_task_dir(sample_task_id)

        expected_path = isolated_epic_settings.workspace_dir / sample_task_id
        assert task_dir == expected_path

    def test_get_artifact_path_returns_correct_path(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test get_artifact_path returns correct scratchpad.md path."""
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)

        expected_path = isolated_epic_settings.workspace_dir / sample_task_id / ARTIFACT_FILENAME
        assert artifact_path == expected_path

    def test_get_archive_path_returns_correct_numbered_path(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test get_archive_path returns correctly numbered archive file."""
        # Test with known phase
        archive_path = artifact_manager.get_archive_path(sample_task_id, "planning", 1)

        expected_path = isolated_epic_settings.workspace_dir / sample_task_id / ARCHIVE_DIR_NAME / "03-planning.md"
        assert archive_path == expected_path

        # Test phase number mapping
        coding_path = artifact_manager.get_archive_path(sample_task_id, "coding", 1)
        expected_coding_path = isolated_epic_settings.workspace_dir / sample_task_id / ARCHIVE_DIR_NAME / "05-coding.md"
        assert coding_path == expected_coding_path

    def test_write_and_read_artifact_cycle(self, artifact_manager, sample_task_id):
        """Test writing and reading artifact content."""
        # Create task structure first
        artifact_manager.create_task_structure(sample_task_id)

        test_content = "# Test Artifact\n\nThis is test content for the artifact."

        # Write artifact
        artifact_manager.write_artifact(sample_task_id, test_content)

        # Read artifact back
        read_content = artifact_manager.read_artifact(sample_task_id)

        assert read_content == test_content

    def test_read_artifact_returns_none_for_nonexistent_file(self, artifact_manager, sample_task_id):
        """Test read_artifact returns None when file doesn't exist."""
        content = artifact_manager.read_artifact(sample_task_id)
        assert content is None

    def test_archive_artifact_copies_to_numbered_file(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test archive_artifact correctly copies scratchpad.md to sequentially numbered file."""
        # Create task structure and write artifact
        artifact_manager.create_task_structure(sample_task_id)
        original_content = "# Completed Phase\n\nThis phase is complete."
        artifact_manager.write_artifact(sample_task_id, original_content)

        # Archive the artifact
        phase_name = "gatherrequirements"
        artifact_manager.archive_artifact(sample_task_id, phase_name)

        # Verify archive file was created with correct content
        expected_archive_path = isolated_epic_settings.workspace_dir / sample_task_id / ARCHIVE_DIR_NAME / f"{PHASE_NUMBERS[phase_name]:02d}-{phase_name}.md"

        assert expected_archive_path.exists()
        archived_content = expected_archive_path.read_text(encoding="utf-8")
        assert archived_content == original_content

    def test_archive_artifact_creates_archive_directory_if_missing(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test archive_artifact creates archive directory if it doesn't exist."""
        # Create only task directory, not archive subdirectory
        task_dir = isolated_epic_settings.workspace_dir / sample_task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Write artifact
        artifact_content = "Test content for archiving"
        artifact_manager.write_artifact(sample_task_id, artifact_content)

        # Archive should create directory
        artifact_manager.archive_artifact(sample_task_id, "planning")

        # Verify archive directory was created
        archive_dir = task_dir / ARCHIVE_DIR_NAME
        assert archive_dir.exists()

    def test_archive_artifact_handles_missing_live_artifact(self, artifact_manager, sample_task_id):
        """Test archive_artifact handles case where live artifact doesn't exist."""
        # Create task structure but no artifact
        artifact_manager.create_task_structure(sample_task_id)

        # Archiving should not fail
        artifact_manager.archive_artifact(sample_task_id, "gatherrequirements")

        # No archive file should be created
        archive_path = artifact_manager.get_archive_path(sample_task_id, "gatherrequirements", 1)
        assert not archive_path.exists()

    def test_build_structured_artifact_handles_yaml_metadata(self, artifact_manager):
        """Test build_structured_artifact correctly handles YAML front matter."""
        template = """---
{{ metadata }}
---

# {{ title }}

{{ content }}
"""

        data = {"metadata": {"task_id": "TEST-456", "phase": "gatherrequirements", "status": "working"}, "title": "Test Task", "content": "This is the main content."}

        result = artifact_manager.build_structured_artifact(template, data)

        # Verify YAML front matter is properly formatted
        assert "---" in result
        assert "task_id: TEST-456" in result
        assert "phase: gatherrequirements" in result
        assert "status: working" in result
        assert "# Test Task" in result
        assert "This is the main content." in result

    def test_build_structured_artifact_handles_file_breakdown_json(self, artifact_manager):
        """Test build_structured_artifact converts file_breakdown to human-readable format."""
        template = """---
{{ metadata }}
---

## File Changes
{{ file_breakdown }}
"""

        file_breakdown = [{"file_path": "test.py", "action": "create", "change_summary": "New test file"}, {"file_path": "main.py", "action": "modify", "change_summary": "Updated logic"}]

        data = {"metadata": {"task_id": "TEST-789"}, "file_breakdown": file_breakdown}

        result = artifact_manager.build_structured_artifact(template, data)

        # Verify table formatting
        assert "| File Path" in result
        assert "| Action" in result
        assert "| Change Summary" in result
        assert "| test.py" in result
        assert "| create" in result
        assert "| New test file" in result
        assert "| main.py" in result
        assert "| modify" in result
        assert "| Updated logic" in result

    def test_build_structured_artifact_handles_acceptance_criteria_list(self, artifact_manager):
        """Test build_structured_artifact converts acceptance_criteria list to markdown."""
        template = """---
{{ metadata }}
---

## Acceptance Criteria
{{ acceptance_criteria }}
"""

        criteria_list = ["Feature works correctly", "Error handling is implemented", "Tests are passing"]

        data = {"metadata": {"task_id": "TEST-CRITERIA"}, "acceptance_criteria": criteria_list}

        result = artifact_manager.build_structured_artifact(template, data)

        # Verify numbered list formatting
        assert "1. Feature works correctly" in result
        assert "2. Error handling is implemented" in result
        assert "3. Tests are passing" in result

    def test_parse_artifact_extracts_metadata_and_content(self, artifact_manager):
        """Test parse_artifact correctly extracts YAML metadata and main content."""
        artifact_content = """---
task_id: PARSE-TEST
phase: planning
status: working
version: '1.0'
---

# Planning Document

This is the main content of the artifact.

## Section 1
Content here.
"""

        metadata, main_content = artifact_manager.parse_artifact(artifact_content)

        # Verify metadata extraction
        assert metadata["task_id"] == "PARSE-TEST"
        assert metadata["phase"] == "planning"
        assert metadata["status"] == "working"
        assert metadata["version"] == "1.0"

        # Verify main content extraction
        assert "# Planning Document" in main_content
        assert "This is the main content" in main_content
        assert "## Section 1" in main_content

    def test_parse_artifact_handles_missing_yaml_frontmatter(self, artifact_manager):
        """Test parse_artifact handles artifacts without YAML front matter."""
        artifact_content = """# Simple Document

This document has no YAML front matter.
"""

        metadata, main_content = artifact_manager.parse_artifact(artifact_content)

        # Should return empty metadata and full content
        assert metadata == {}
        assert main_content == artifact_content

    def test_parse_artifact_handles_invalid_yaml(self, artifact_manager):
        """Test parse_artifact handles corrupted YAML gracefully."""
        artifact_content = """---
invalid: yaml: content: here
broken [yaml
---

# Document with broken YAML

Content here.
"""

        metadata, main_content = artifact_manager.parse_artifact(artifact_content)

        # Should return empty metadata and full content on YAML error
        assert metadata == {}
        assert main_content == artifact_content

    @pytest.mark.parametrize(
        "phase_name,expected_number",
        [
            ("gatherrequirements", 1),
            ("planning", 3),
            ("coding", 5),
            ("testing", 6),
            ("finalize", 7),
        ],
        ids=["gatherrequirements", "planning", "coding", "testing", "finalize"],
    )
    def test_phase_number_mapping_in_archive_paths(self, artifact_manager, sample_task_id, phase_name, expected_number):
        """Test that phase names map to correct numbers in archive paths."""
        archive_path = artifact_manager.get_archive_path(sample_task_id, phase_name, 1)

        expected_filename = f"{expected_number:02d}-{phase_name}.md"
        assert archive_path.name == expected_filename

    def test_build_structured_artifact_handles_code_modifications_json(self, artifact_manager):
        """Test build_structured_artifact converts code_modifications to human-readable format."""
        template = """---
{{ metadata }}
---

## Code Changes
{{ code_modifications }}
"""

        code_modifications = [{"file_path": "src/main.py", "code_block": "def new_function():\n    pass", "description": "Added new function"}]

        data = {"metadata": {"task_id": "CODE-TEST"}, "code_modifications": code_modifications}

        result = artifact_manager.build_structured_artifact(template, data)

        # Verify human-readable formatting of code modifications
        assert "### File: `src/main.py`" in result
        assert "**Description:** Added new function" in result
        assert "def new_function():" in result

    def test_multiple_archive_operations_maintain_consistency(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test multiple archive operations maintain file consistency."""
        # Create task structure
        artifact_manager.create_task_structure(sample_task_id)

        # Archive multiple phases
        phases_content = {
            "gatherrequirements": "# Gather Requirements Complete\nRequirements gathered successfully.",
            "planning": "# Planning Complete\nDetailed plan created.",
            "coding": "# Coding Complete\nImplementation finished.",
        }

        for phase, content in phases_content.items():
            # Write and archive each phase
            artifact_manager.write_artifact(sample_task_id, content)
            artifact_manager.archive_artifact(sample_task_id, phase)

        # Verify all archives exist with correct content
        archive_dir = isolated_epic_settings.workspace_dir / sample_task_id / ARCHIVE_DIR_NAME

        for phase, expected_content in phases_content.items():
            phase_number = PHASE_NUMBERS[phase]
            archive_file = archive_dir / f"{phase_number:02d}-{phase}.md"

            assert archive_file.exists()
            actual_content = archive_file.read_text(encoding="utf-8")
            assert actual_content == expected_content

    def test_append_to_artifact_creates_new_file_when_none_exists(self, artifact_manager, sample_task_id):
        """Test append_to_artifact creates new file when artifact doesn't exist."""
        # Create task structure but no artifact
        artifact_manager.create_task_structure(sample_task_id)

        content_to_append = "# First Content\n\nThis is the first content."

        # Append should create new file
        artifact_manager.append_to_artifact(sample_task_id, content_to_append)

        # Verify file was created with content
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        assert artifact_path.exists()

        actual_content = artifact_path.read_text(encoding="utf-8")
        assert actual_content == content_to_append

    def test_append_to_artifact_appends_to_existing_file(self, artifact_manager, sample_task_id):
        """Test append_to_artifact correctly appends to existing artifact."""
        # Create task structure and initial artifact
        artifact_manager.create_task_structure(sample_task_id)
        initial_content = "# Initial Content\n\nThis is the initial content."
        artifact_manager.write_artifact(sample_task_id, initial_content)

        # Append new content
        appended_content = "# Appended Content\n\nThis is the appended content."
        artifact_manager.append_to_artifact(sample_task_id, appended_content)

        # Verify content was appended with separator
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        actual_content = artifact_path.read_text(encoding="utf-8")

        expected_content = f"{initial_content}\n\n---\n\n{appended_content}"
        assert actual_content == expected_content

    def test_append_to_artifact_uses_correct_separator(self, artifact_manager, sample_task_id):
        """Test append_to_artifact uses markdown horizontal rule as separator."""
        # Create task structure and initial artifact
        artifact_manager.create_task_structure(sample_task_id)

        # Write initial content
        first_content = "# Strategy Phase\n\nInitial strategy content."
        artifact_manager.write_artifact(sample_task_id, first_content)

        # Append second content
        second_content = "# Solution Design Phase\n\nDetailed solution design."
        artifact_manager.append_to_artifact(sample_task_id, second_content)

        # Append third content
        third_content = "# Execution Plan Generation Phase\n\nDetailed execution plan with specific implementation steps."
        artifact_manager.append_to_artifact(sample_task_id, third_content)

        # Verify all content is separated correctly
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        actual_content = artifact_path.read_text(encoding="utf-8")

        expected_content = f"{first_content}\n\n---\n\n{second_content}\n\n---\n\n{third_content}"
        assert actual_content == expected_content

    def test_append_to_artifact_handles_empty_existing_file(self, artifact_manager, sample_task_id):
        """Test append_to_artifact handles empty existing artifact file."""
        # Create task structure and empty artifact
        artifact_manager.create_task_structure(sample_task_id)
        artifact_manager.write_artifact(sample_task_id, "")

        # Append content to empty file
        content_to_append = "# New Content\n\nThis is new content."
        artifact_manager.append_to_artifact(sample_task_id, content_to_append)

        # Verify content was added without separator (since file was empty)
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        actual_content = artifact_path.read_text(encoding="utf-8")

        assert actual_content == content_to_append

    def test_append_to_artifact_handles_whitespace_only_file(self, artifact_manager, sample_task_id):
        """Test append_to_artifact handles file with only whitespace."""
        # Create task structure and whitespace-only artifact
        artifact_manager.create_task_structure(sample_task_id)
        whitespace_content = "   \n\t\n   "
        artifact_manager.write_artifact(sample_task_id, whitespace_content)

        # Append content
        content_to_append = "# New Content\n\nThis is new content."
        artifact_manager.append_to_artifact(sample_task_id, content_to_append)

        # Verify content was added without separator (since file was effectively empty)
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        actual_content = artifact_path.read_text(encoding="utf-8")

        # The whitespace is preserved but no separator is added since it's effectively empty
        expected_content = whitespace_content + content_to_append
        assert actual_content == expected_content

    def test_append_to_artifact_validates_task_id(self, artifact_manager):
        """Test append_to_artifact validates task_id parameter."""
        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            artifact_manager.append_to_artifact("", "some content")

    def test_append_to_artifact_validates_content(self, artifact_manager, sample_task_id):
        """Test append_to_artifact validates content parameter."""
        artifact_manager.create_task_structure(sample_task_id)

        with pytest.raises(ValueError, match="Content cannot be empty"):
            artifact_manager.append_to_artifact(sample_task_id, "")

        with pytest.raises(ValueError, match="Content cannot be empty"):
            artifact_manager.append_to_artifact(sample_task_id, "   \n\t   ")

    def test_append_to_artifact_creates_directory_structure_if_missing(self, artifact_manager, sample_task_id, isolated_epic_settings):
        """Test append_to_artifact creates directory structure if it doesn't exist."""
        # Don't create task structure first
        content_to_append = "# Content\n\nThis is content."

        # Append should create directory structure
        artifact_manager.append_to_artifact(sample_task_id, content_to_append)

        # Verify directory and file were created
        task_dir = isolated_epic_settings.workspace_dir / sample_task_id
        assert task_dir.exists()

        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        assert artifact_path.exists()
        assert artifact_path.read_text(encoding="utf-8") == content_to_append

    def test_append_to_artifact_multiple_operations(self, artifact_manager, sample_task_id):
        """Test append_to_artifact handles multiple append operations correctly."""
        # Create task structure and initial content
        artifact_manager.create_task_structure(sample_task_id)
        initial_content = "# Initial\n\nInitial content."
        artifact_manager.write_artifact(sample_task_id, initial_content)

        # First append
        first_append = "# First Append\n\nFirst appended content."
        artifact_manager.append_to_artifact(sample_task_id, first_append)

        # Second append
        second_append = "# Second Append\n\nSecond appended content."
        artifact_manager.append_to_artifact(sample_task_id, second_append)

        # Verify all content is properly separated
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        actual_content = artifact_path.read_text(encoding="utf-8")

        expected_content = f"{initial_content}\n\n---\n\n{first_append}\n\n---\n\n{second_append}"
        assert actual_content == expected_content

    def test_append_to_artifact_preserves_encoding(self, artifact_manager, sample_task_id):
        """Test append_to_artifact preserves UTF-8 encoding for special characters."""
        # Create task structure and initial content with special characters
        artifact_manager.create_task_structure(sample_task_id)
        initial_content = "# Initial 🚀\n\nContent with émojis and ñice characters."
        artifact_manager.write_artifact(sample_task_id, initial_content)

        # Append content with more special characters
        appended_content = "# Appended 🎯\n\nMore special characters: café, naïve, résumé."
        artifact_manager.append_to_artifact(sample_task_id, appended_content)

        # Verify encoding is preserved
        artifact_path = artifact_manager.get_artifact_path(sample_task_id)
        actual_content = artifact_path.read_text(encoding="utf-8")

        expected_content = f"{initial_content}\n\n---\n\n{appended_content}"
        assert actual_content == expected_content

        # Verify specific special characters are preserved
        assert "🚀" in actual_content
        assert "🎯" in actual_content
        assert "émojis" in actual_content
        assert "ñice" in actual_content
        assert "café" in actual_content

    def test_format_numbered_text_normalizes_patterns(self, artifact_manager):
        """Test that _format_numbered_text normalizes '1)' to '1.' format."""
        # Test mixed formats
        input_text = "Core approach: 1) Extend the state machine 2) Implement conditional routing 3) Create templates"
        result = artifact_manager._format_numbered_text(input_text)

        # Should normalize to "1." format
        assert "1." in result
        assert "2." in result
        assert "3." in result
        assert "1)" not in result
        assert "2)" not in result

        # Test already correct format
        correct_text = "Steps: 1. First step 2. Second step 3. Third step"
        result = artifact_manager._format_numbered_text(correct_text)
        assert "1." in result
        assert "2." in result

        # Test with intro text
        intro_text = "Risks: 1) State explosion - Mitigated by patterns 2) Context size - Mitigated by limits"
        result = artifact_manager._format_numbered_text(intro_text)
        assert result.startswith("Risks:")
        assert "\n1." in result
        assert "\n2." in result
        assert "1)" not in result

    def test_yaml_metadata_no_extra_newline(self, artifact_manager):
        """Test that YAML metadata doesn't add extra newlines in front matter."""
        template = """---
{{ metadata }}
---

# Test Document"""

        data = {"metadata": {"task_id": "TEST-123", "phase": "gatherrequirements"}}

        result = artifact_manager.build_structured_artifact(template, data)
        lines = result.split("\n")

        # Find the second --- marker
        yaml_end_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "---" and i > 0:
                yaml_end_idx = i
                break

        # Ensure no blank line before the closing ---
        assert yaml_end_idx is not None, "Could not find closing --- marker"
        assert lines[yaml_end_idx - 1].strip() != "", "Extra blank line found before closing --- marker"
