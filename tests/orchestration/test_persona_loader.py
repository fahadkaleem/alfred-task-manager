"""Tests for persona_loader module."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from src.alfred.orchestration.persona_loader import load_persona


class TestPersonaLoader:
    """Test cases for the persona loader functions."""

    def test_load_persona_success(self):
        """Test successful persona loading."""
        mock_persona_data = {
            "name": "Alex",
            "title": "Solution Architect",
            "role": "planning"
        }
        
        with patch('src.alfred.orchestration.persona_loader.settings') as mock_settings, \
             patch('builtins.open', mock_open(read_data="name: Alex\ntitle: Solution Architect\nrole: planning")) as mock_file:
            
            # Setup mock paths
            mock_alfred_dir = MagicMock()
            mock_alfred_dir.__truediv__ = MagicMock()
            mock_alfred_dir.__truediv__.return_value.__truediv__ = MagicMock()
            mock_persona_file = MagicMock()
            mock_persona_file.exists.return_value = True
            mock_alfred_dir.__truediv__.return_value.__truediv__.return_value = mock_persona_file
            
            mock_settings.alfred_dir = mock_alfred_dir
            mock_settings.packaged_personas_dir = MagicMock()
            
            result = load_persona("planning")
            
            assert result == mock_persona_data
            mock_file.assert_called_once()

    def test_load_persona_fallback_to_packaged(self):
        """Test persona loading falls back to packaged personas."""
        mock_persona_data = {
            "name": "Alex",
            "title": "Solution Architect", 
            "role": "planning"
        }
        
        with patch('builtins.open', mock_open(read_data="name: Alex\ntitle: Solution Architect\nrole: planning")) as mock_file:
            
            # Mock the first file (alfred_dir) to not exist
            mock_alfred_file = MagicMock()
            mock_alfred_file.exists.return_value = False
            
            # Mock the second file (packaged) to exist
            mock_packaged_file = MagicMock()
            mock_packaged_file.exists.return_value = True
            
            with patch('src.alfred.orchestration.persona_loader.settings') as mock_settings:
                mock_alfred_dir = MagicMock()
                mock_alfred_dir.__truediv__ = MagicMock()
                mock_alfred_dir.__truediv__.return_value.__truediv__ = MagicMock()
                mock_alfred_dir.__truediv__.return_value.__truediv__.return_value = mock_alfred_file
                
                mock_packaged_dir = MagicMock() 
                mock_packaged_dir.__truediv__ = MagicMock()
                mock_packaged_dir.__truediv__.return_value = mock_packaged_file
                
                mock_settings.alfred_dir = mock_alfred_dir
                mock_settings.packaged_personas_dir = mock_packaged_dir
                
                result = load_persona("planning")
                
                assert result == mock_persona_data
                mock_file.assert_called_once()

    def test_load_persona_file_not_found_error(self):
        """Test persona loading raises FileNotFoundError when file doesn't exist."""
        # Mock both files to not exist
        mock_alfred_file = MagicMock()
        mock_alfred_file.exists.return_value = False
        
        mock_packaged_file = MagicMock()
        mock_packaged_file.exists.return_value = False
        
        with patch('src.alfred.orchestration.persona_loader.settings') as mock_settings:
            mock_alfred_dir = MagicMock()
            mock_alfred_dir.__truediv__ = MagicMock()
            mock_alfred_dir.__truediv__.return_value.__truediv__ = MagicMock()
            mock_alfred_dir.__truediv__.return_value.__truediv__.return_value = mock_alfred_file
            
            mock_packaged_dir = MagicMock() 
            mock_packaged_dir.__truediv__ = MagicMock()
            mock_packaged_dir.__truediv__.return_value = mock_packaged_file
            
            mock_settings.alfred_dir = mock_alfred_dir
            mock_settings.packaged_personas_dir = mock_packaged_dir
            
            with pytest.raises(FileNotFoundError) as exc_info:
                load_persona("nonexistent")
            
            assert "Persona config 'nonexistent.yml' not found" in str(exc_info.value)