"""Tests for Alfred configuration management."""

import json
from pathlib import Path

import pytest

from src.alfred.config import AlfredConfig, ConfigManager, FeaturesConfig


def test_alfred_config_model():
    """Test the AlfredConfig model."""
    # Test default values
    config = AlfredConfig()
    assert config.version == "2.0.0"
    assert isinstance(config.features, FeaturesConfig)
    assert config.features.scaffolding_mode is False

    # Test custom values
    config = AlfredConfig(version="2.1.0", features=FeaturesConfig(scaffolding_mode=True))
    assert config.version == "2.1.0"
    assert config.features.scaffolding_mode is True


def test_config_manager_create_default(tmp_path):
    """Test creating a default configuration."""
    manager = ConfigManager(tmp_path)
    config = manager.create_default()

    # Check the config object
    assert isinstance(config, AlfredConfig)
    assert config.version == "2.0.0"
    assert config.features.scaffolding_mode is False

    # Check the file was created
    config_file = tmp_path / "config.json"
    assert config_file.exists()

    # Check file content
    with open(config_file) as f:
        data = json.load(f)
    assert data["version"] == "2.0.0"
    assert data["features"]["scaffolding_mode"] is False


def test_config_manager_load(tmp_path):
    """Test loading a configuration."""
    # Create a config file manually
    config_data = {"version": "2.0.0", "features": {"scaffolding_mode": True}}
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Load it
    manager = ConfigManager(tmp_path)
    config = manager.load()

    assert config.version == "2.0.0"
    assert config.features.scaffolding_mode is True


def test_config_manager_update_feature(tmp_path):
    """Test updating a feature flag."""
    manager = ConfigManager(tmp_path)
    manager.create_default()

    # Update feature
    manager.update_feature("scaffolding_mode", True)

    # Check it was updated
    assert manager.is_feature_enabled("scaffolding_mode") is True

    # Verify it was saved to disk
    with open(tmp_path / "config.json") as f:
        data = json.load(f)
    assert data["features"]["scaffolding_mode"] is True


def test_config_manager_unknown_feature(tmp_path):
    """Test accessing unknown feature."""
    manager = ConfigManager(tmp_path)
    manager.create_default()

    # Try to update unknown feature
    with pytest.raises(ValueError, match="Unknown feature: unknown_feature"):
        manager.update_feature("unknown_feature", True)

    # Try to check unknown feature
    with pytest.raises(ValueError, match="Unknown feature: unknown_feature"):
        manager.is_feature_enabled("unknown_feature")


def test_config_manager_not_loaded():
    """Test accessing config before loading."""
    manager = ConfigManager(Path("/tmp"))

    with pytest.raises(RuntimeError, match="Configuration not loaded"):
        manager.get()

    with pytest.raises(RuntimeError, match="Configuration not loaded"):
        manager.update_feature("scaffolding_mode", True)
