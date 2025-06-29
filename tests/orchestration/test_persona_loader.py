"""Tests for persona_loader module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.alfred.orchestration.persona_loader import load_persona
from tests.conftest import AlfredTestProject


class TestPersonaLoader:
    """Test cases for the persona loader functions using real files."""

    def test_load_persona_success(self, alfred_test_project: AlfredTestProject):
        """Test successful persona loading from alfred directory."""
        alfred_test_project.initialize()
        
        # Create a real persona file in the test project
        personas_dir = alfred_test_project.alfred_dir / "personas"
        personas_dir.mkdir(exist_ok=True)
        
        persona_file = personas_dir / "planning.yml"
        persona_content = """name: Alex
title: Solution Architect
role: planning
description: Handles strategic planning and solution architecture
capabilities:
  - Strategic thinking
  - Technical architecture
  - Problem decomposition
"""
        persona_file.write_text(persona_content)
        
        with patch('src.alfred.orchestration.persona_loader.settings', alfred_test_project.settings):
            result = load_persona("planning")
            
            assert result["name"] == "Alex"
            assert result["title"] == "Solution Architect"
            assert result["role"] == "planning"
            assert result["description"] == "Handles strategic planning and solution architecture"
            assert len(result["capabilities"]) == 3

    def test_load_persona_fallback_to_packaged(self, alfred_test_project: AlfredTestProject):
        """Test persona loading falls back to packaged personas when not found in alfred_dir."""
        alfred_test_project.initialize()
        
        # Create a packaged persona directory
        packaged_dir = alfred_test_project.root / "packaged_personas"
        packaged_dir.mkdir(exist_ok=True)
        
        persona_file = packaged_dir / "test_persona.yml"
        persona_content = """name: Quinn
title: Quality Assurance Specialist
role: qa
description: Ensures code quality and testing coverage
capabilities:
  - Test planning
  - Bug detection
  - Quality assurance
"""
        persona_file.write_text(persona_content)
        
        # Create a mock settings object with the right packaged directory
        mock_settings = MagicMock()
        mock_settings.alfred_dir = alfred_test_project.alfred_dir
        mock_settings.packaged_personas_dir = packaged_dir
        
        with patch('src.alfred.orchestration.persona_loader.settings', mock_settings):
            result = load_persona("test_persona")
            
            assert result["name"] == "Quinn"
            assert result["title"] == "Quality Assurance Specialist"
            assert result["role"] == "qa"

    def test_load_persona_alfred_dir_overrides_packaged(self, alfred_test_project: AlfredTestProject):
        """Test that persona in alfred_dir takes precedence over packaged version."""
        alfred_test_project.initialize()
        
        # Create both alfred_dir and packaged versions
        personas_dir = alfred_test_project.alfred_dir / "personas"
        personas_dir.mkdir(exist_ok=True)
        
        packaged_dir = alfred_test_project.root / "packaged_personas"
        packaged_dir.mkdir(exist_ok=True)
        
        # Alfred dir version (should be used)
        alfred_persona = personas_dir / "developer.yml"
        alfred_persona.write_text("""name: Custom Developer
title: Custom Development Lead
role: developer
""")
        
        # Packaged version (should be ignored)
        packaged_persona = packaged_dir / "developer.yml"
        packaged_persona.write_text("""name: Default Developer
title: Default Developer
role: developer
""")
        
        # Create a mock settings object with the right packaged directory
        mock_settings = MagicMock()
        mock_settings.alfred_dir = alfred_test_project.alfred_dir
        mock_settings.packaged_personas_dir = packaged_dir
        
        with patch('src.alfred.orchestration.persona_loader.settings', mock_settings):
            result = load_persona("developer")
            
            # Should use the alfred_dir version, not the packaged one
            assert result["name"] == "Custom Developer"
            assert result["title"] == "Custom Development Lead"

    def test_load_persona_file_not_found_error(self, alfred_test_project: AlfredTestProject):
        """Test persona loading raises FileNotFoundError when file doesn't exist."""
        alfred_test_project.initialize()
        
        # Create empty packaged personas directory
        packaged_dir = alfred_test_project.root / "packaged_personas"
        packaged_dir.mkdir(exist_ok=True)
        
        # Create a mock settings object with the right packaged directory
        mock_settings = MagicMock()
        mock_settings.alfred_dir = alfred_test_project.alfred_dir
        mock_settings.packaged_personas_dir = packaged_dir
        
        with patch('src.alfred.orchestration.persona_loader.settings', mock_settings):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_persona("nonexistent")
            
            assert "Persona config 'nonexistent.yml' not found" in str(exc_info.value)

    def test_load_persona_invalid_yaml(self, alfred_test_project: AlfredTestProject):
        """Test persona loading handles invalid YAML gracefully."""
        alfred_test_project.initialize()
        
        personas_dir = alfred_test_project.alfred_dir / "personas"
        personas_dir.mkdir(exist_ok=True)
        
        # Create a file with invalid YAML
        persona_file = personas_dir / "invalid.yml"
        persona_file.write_text("""
invalid: yaml: content:
  - missing quotes"
  - [unclosed bracket
""")
        
        with patch('src.alfred.orchestration.persona_loader.settings', alfred_test_project.settings):
            with pytest.raises(Exception):  # Should raise some YAML parsing exception
                load_persona("invalid")