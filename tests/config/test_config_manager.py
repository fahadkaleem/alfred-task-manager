"""
Comprehensive tests for Epic Task Manager Configuration Management
Tests configuration loading, saving, validation, and provider setup.
"""

import json
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from epic_task_manager.config.config_manager import (
    ConfigManager,
    get_config_file_path,
    load_config,
    save_config,
)
from epic_task_manager.models.config import (
    ConnectionMethod,
    EpicConfig,
    FeatureFlags,
    JiraConfig,
    LinearConfig,
    TaskSource,
)


class TestConfigManager:
    """Test ConfigManager class functionality."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create temporary config file path."""
        return tmp_path / ".epictaskmanager" / "config.json"

    @pytest.fixture
    def config_manager(self, temp_config_file):
        """Create ConfigManager with temporary config file."""
        return ConfigManager(config_file=temp_config_file)

    def test_create_config_manager_with_default_path(self):
        """Test creating ConfigManager with default path."""
        manager = ConfigManager()

        assert manager.config_file is not None
        assert manager.config_file.name == "config.json"

    def test_create_config_manager_with_custom_path(self, temp_config_file):
        """Test creating ConfigManager with custom path."""
        manager = ConfigManager(config_file=temp_config_file)

        assert manager.config_file == temp_config_file

    def test_load_config_file_not_exists(self, config_manager, temp_config_file):
        """Test load_config creates default config when file doesn't exist."""
        # Ensure file doesn't exist
        assert not temp_config_file.exists()

        config = config_manager.load_config()

        # Should create default config
        assert isinstance(config, EpicConfig)
        assert config.providers.task_source == TaskSource.LOCAL
        assert config.version == "1.0"
        assert temp_config_file.exists()

    def test_load_config_valid_file(self, config_manager, temp_config_file):
        """Test load_config with valid configuration file."""
        # Create valid config file
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        valid_config = {
            "providers": {"task_source": "atlassian", "task_source_config": {"jira": {"cloud_id": "test-cloud-id", "project_key": "TEST", "default_issue_type": "Story"}, "linear": None}},
            "features": {"auto_assign": False, "auto_transition": True, "smart_context": False},
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "version": "1.0",
        }

        with open(temp_config_file, "w") as f:
            json.dump(valid_config, f)

        config = config_manager.load_config()

        assert config.providers.task_source == TaskSource.ATLASSIAN
        assert config.providers.task_source_config.jira.cloud_id == "test-cloud-id"
        assert config.providers.task_source_config.jira.project_key == "TEST"
        assert config.features.auto_assign is False

    def test_load_config_invalid_json(self, config_manager, temp_config_file):
        """Test load_config handles invalid JSON gracefully."""
        # Create invalid JSON file
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_file, "w") as f:
            f.write("{ invalid json")

        config = config_manager.load_config()

        # Should create backup and return default config
        backup_file = temp_config_file.with_suffix(".json.backup")
        assert backup_file.exists()
        assert isinstance(config, EpicConfig)
        assert config.providers.task_source == TaskSource.LOCAL

    def test_load_config_invalid_schema(self, config_manager, temp_config_file):
        """Test load_config handles invalid schema gracefully."""
        # Create valid JSON but invalid schema
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        invalid_config = {
            "providers": {
                "task_source": "invalid_source",  # Invalid enum value
                "task_source_config": {},
            },
            "version": "1.0",
        }

        with open(temp_config_file, "w") as f:
            json.dump(invalid_config, f)

        config = config_manager.load_config()

        # Should create backup and return default config
        backup_file = temp_config_file.with_suffix(".json.backup")
        assert backup_file.exists()
        assert isinstance(config, EpicConfig)
        assert config.providers.task_source == TaskSource.LOCAL

    def test_save_config_creates_directory(self, config_manager, temp_config_file):
        """Test save_config creates parent directory if it doesn't exist."""
        config = EpicConfig()

        # Ensure directory doesn't exist
        assert not temp_config_file.parent.exists()

        config_manager.save_config(config)

        assert temp_config_file.exists()
        assert temp_config_file.parent.exists()

    def test_save_config_updates_timestamp(self, config_manager, temp_config_file):
        """Test save_config updates the updated_at timestamp."""
        config = EpicConfig()
        original_timestamp = config.updated_at

        # Add a small delay to ensure timestamp difference
        import time

        time.sleep(0.01)

        config_manager.save_config(config)

        # Reload to check timestamp was updated
        saved_config = config_manager.load_config()
        assert saved_config.updated_at > original_timestamp

    def test_save_config_preserves_data(self, config_manager, temp_config_file):
        """Test save_config preserves all configuration data."""
        config = EpicConfig()
        config.providers.task_source = TaskSource.ATLASSIAN
        config.providers.task_source_config.jira = JiraConfig(cloud_id="test-id", project_key="PROJ", default_issue_type="Bug")
        config.features.auto_assign = False

        config_manager.save_config(config)

        # Reload and verify
        loaded_config = config_manager.load_config()
        assert loaded_config.providers.task_source == TaskSource.ATLASSIAN
        assert loaded_config.providers.task_source_config.jira.cloud_id == "test-id"
        assert loaded_config.providers.task_source_config.jira.project_key == "PROJ"
        assert loaded_config.features.auto_assign is False

    def test_validate_config_valid_data(self, config_manager):
        """Test validate_config with valid configuration data."""
        valid_data = {
            "providers": {"task_source": "linear", "task_source_config": {"jira": None, "linear": {"team_id": "team-123", "workspace": "test-workspace"}}},
            "features": {"auto_assign": True, "auto_transition": False, "smart_context": True},
            "version": "1.0",
        }

        config = config_manager.validate_config(valid_data)

        assert isinstance(config, EpicConfig)
        assert config.providers.task_source == TaskSource.LINEAR
        assert config.providers.task_source_config.linear.team_id == "team-123"

    def test_validate_config_invalid_data(self, config_manager):
        """Test validate_config with invalid configuration data."""
        invalid_data = {"providers": {"task_source": "nonexistent_source", "task_source_config": {}}}

        with pytest.raises(ValidationError):
            config_manager.validate_config(invalid_data)

    @pytest.mark.parametrize(
        "task_source,provider_config,expected_config_type",
        [
            (TaskSource.ATLASSIAN, {"cloud_id": "test", "project_key": "PROJ"}, JiraConfig),
            (TaskSource.LINEAR, {"team_id": "team123", "workspace": "work"}, LinearConfig),
            (TaskSource.LOCAL, None, type(None)),
        ],
        ids=["jira", "linear", "local"],
    )
    def test_setup_provider_config(self, config_manager, temp_config_file, task_source, provider_config, expected_config_type):
        """Test setup_provider_config for different providers."""
        config = config_manager.setup_provider_config(task_source, provider_config)

        assert config.providers.task_source == task_source

        if task_source == TaskSource.ATLASSIAN and provider_config:
            assert isinstance(config.providers.task_source_config.jira, JiraConfig)
            assert config.providers.task_source_config.jira.cloud_id == provider_config["cloud_id"]
        elif task_source == TaskSource.LINEAR and provider_config:
            assert isinstance(config.providers.task_source_config.linear, LinearConfig)
            assert config.providers.task_source_config.linear.team_id == provider_config["team_id"]

        # Verify config was saved
        assert temp_config_file.exists()

    @pytest.mark.parametrize(
        "task_source,expected_result",
        [
            (TaskSource.ATLASSIAN, True),  # Assumes MCP available
            (TaskSource.LINEAR, True),  # Assumes MCP available
            (TaskSource.LOCAL, True),  # Local doesn't need MCP
        ],
        ids=["jira", "linear", "local"],
    )
    def test_validate_mcp_availability(self, config_manager, task_source, expected_result):
        """Test validate_mcp_availability for different task sources."""
        result = config_manager.validate_mcp_availability(task_source)

        assert result == expected_result

    def test_validate_mcp_availability_import_error(self, config_manager):
        """Test validate_mcp_availability handles import errors."""
        with patch("builtins.__import__", side_effect=ImportError("MCP not available")):
            result = config_manager.validate_mcp_availability(TaskSource.ATLASSIAN)

            assert result is False

    def test_backup_invalid_config(self, config_manager, temp_config_file):
        """Test _backup_invalid_config creates backup file."""
        # Create invalid config file
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_file, "w") as f:
            f.write("invalid content")

        config_manager._backup_invalid_config()

        backup_file = temp_config_file.with_suffix(".json.backup")
        assert backup_file.exists()
        assert not temp_config_file.exists()


class TestGlobalConfigFunctions:
    """Test global configuration functions."""

    def test_load_config_function(self):
        """Test load_config global function."""
        with patch("epic_task_manager.config.config_manager.config_manager") as mock_manager:
            mock_config = EpicConfig()
            mock_manager.load_config.return_value = mock_config

            result = load_config()

            assert result == mock_config
            mock_manager.load_config.assert_called_once()

    def test_save_config_function(self):
        """Test save_config global function."""
        with patch("epic_task_manager.config.config_manager.config_manager") as mock_manager:
            mock_config = EpicConfig()

            save_config(mock_config)

            mock_manager.save_config.assert_called_once_with(mock_config)

    def test_get_config_file_path_function(self):
        """Test get_config_file_path global function."""
        with patch("epic_task_manager.config.config_manager.config_manager") as mock_manager:
            mock_path = Path("/test/path/config.json")
            mock_manager.config_file = mock_path

            result = get_config_file_path()

            assert result == mock_path


class TestConfigModels:
    """Test configuration model validation and behavior."""

    def test_epic_config_defaults(self):
        """Test EpicConfig creates with proper defaults."""
        config = EpicConfig()

        assert config.providers.task_source == TaskSource.LOCAL
        assert config.providers.task_source_config.jira is None
        assert config.providers.task_source_config.linear is None
        assert config.features.auto_assign is True
        assert config.features.auto_transition is True
        assert config.features.smart_context is True
        assert config.version == "1.0"

    def test_jira_config_validation(self):
        """Test JiraConfig validation and defaults."""
        # Test with minimal data
        config = JiraConfig()
        assert config.default_issue_type == "Task"
        assert config.connection_method == ConnectionMethod.MCP

        # Test with full data
        config = JiraConfig(cloud_id="test-id", project_key="PROJ", default_issue_type="Story", base_url="https://test.atlassian.net")
        assert config.cloud_id == "test-id"
        assert config.project_key == "PROJ"
        assert config.default_issue_type == "Story"
        assert config.base_url == "https://test.atlassian.net"

    def test_linear_config_validation(self):
        """Test LinearConfig validation and defaults."""
        # Test with minimal data
        config = LinearConfig()
        assert config.connection_method == ConnectionMethod.MCP

        # Test with full data
        config = LinearConfig(team_id="team-123", workspace="test-workspace", default_state_id="state-456")
        assert config.team_id == "team-123"
        assert config.workspace == "test-workspace"
        assert config.default_state_id == "state-456"

    def test_epic_config_get_active_config(self):
        """Test EpicConfig.get_active_config() method."""
        # Test with Jira
        config = EpicConfig()
        config.providers.task_source = TaskSource.ATLASSIAN
        config.providers.task_source_config.jira = JiraConfig(cloud_id="test")

        active_config = config.get_active_config()
        assert isinstance(active_config, JiraConfig)
        assert active_config.cloud_id == "test"

        # Test with Linear
        config.providers.task_source = TaskSource.LINEAR
        config.providers.task_source_config.linear = LinearConfig(team_id="team123")

        active_config = config.get_active_config()
        assert isinstance(active_config, LinearConfig)
        assert active_config.team_id == "team123"

        # Test with Local
        config.providers.task_source = TaskSource.LOCAL

        active_config = config.get_active_config()
        assert active_config is None

    def test_epic_config_get_task_source(self):
        """Test EpicConfig.get_task_source() method."""
        config = EpicConfig()

        # Test default
        assert config.get_task_source() == TaskSource.LOCAL

        # Test with different sources
        config.providers.task_source = TaskSource.ATLASSIAN
        assert config.get_task_source() == TaskSource.ATLASSIAN

        config.providers.task_source = TaskSource.LINEAR
        assert config.get_task_source() == TaskSource.LINEAR

    @pytest.mark.parametrize("task_source", [TaskSource.ATLASSIAN, TaskSource.LINEAR, TaskSource.LOCAL], ids=["jira", "linear", "local"])
    def test_task_source_enum_values(self, task_source):
        """Test TaskSource enum values are strings."""
        assert isinstance(task_source.value, str)
        assert task_source.value in ["atlassian", "linear", "local"]

    @pytest.mark.parametrize("connection_method", [ConnectionMethod.API, ConnectionMethod.MCP, ConnectionMethod.WEBHOOK], ids=["api", "mcp", "webhook"])
    def test_connection_method_enum_values(self, connection_method):
        """Test ConnectionMethod enum values are strings."""
        assert isinstance(connection_method.value, str)
        assert connection_method.value in ["api", "mcp", "webhook"]

    def test_feature_flags_validation(self):
        """Test FeatureFlags validation and defaults."""
        # Test defaults
        flags = FeatureFlags()
        assert flags.auto_assign is True
        assert flags.auto_transition is True
        assert flags.smart_context is True

        # Test custom values
        flags = FeatureFlags(auto_assign=False, auto_transition=False, smart_context=False)
        assert flags.auto_assign is False
        assert flags.auto_transition is False
        assert flags.smart_context is False

    def test_config_serialization_deserialization(self):
        """Test configuration can be serialized and deserialized."""
        # Create complex config
        original_config = EpicConfig()
        original_config.providers.task_source = TaskSource.ATLASSIAN
        original_config.providers.task_source_config.jira = JiraConfig(cloud_id="test-cloud", project_key="TEST", default_issue_type="Bug")
        original_config.features.auto_assign = False

        # Serialize
        config_data = original_config.model_dump()

        # Deserialize
        restored_config = EpicConfig(**config_data)

        # Verify
        assert restored_config.providers.task_source == TaskSource.ATLASSIAN
        assert restored_config.providers.task_source_config.jira.cloud_id == "test-cloud"
        assert restored_config.providers.task_source_config.jira.project_key == "TEST"
        assert restored_config.features.auto_assign is False


class TestConfigurationIntegration:
    """Test configuration integration with other components."""

    def test_config_workflow_complete_cycle(self, tmp_path):
        """Test complete configuration workflow cycle."""
        config_file = tmp_path / "config.json"
        manager = ConfigManager(config_file)

        # Step 1: Load initial config (should create default)
        config = manager.load_config()
        assert config.providers.task_source == TaskSource.LOCAL

        # Step 2: Setup Jira provider
        jira_config = {"cloud_id": "workflow-test", "project_key": "WORK", "default_issue_type": "Epic"}

        updated_config = manager.setup_provider_config(TaskSource.ATLASSIAN, jira_config)
        assert updated_config.providers.task_source == TaskSource.ATLASSIAN

        # Step 3: Reload and verify persistence
        reloaded_config = manager.load_config()
        assert reloaded_config.providers.task_source == TaskSource.ATLASSIAN
        assert reloaded_config.providers.task_source_config.jira.cloud_id == "workflow-test"

        # Step 4: Switch to Linear
        linear_config = {"team_id": "team-workflow", "workspace": "workflow-space"}

        linear_updated_config = manager.setup_provider_config(TaskSource.LINEAR, linear_config)
        assert linear_updated_config.providers.task_source == TaskSource.LINEAR

        # Step 5: Final verification
        final_config = manager.load_config()
        assert final_config.providers.task_source == TaskSource.LINEAR
        assert final_config.providers.task_source_config.linear.team_id == "team-workflow"

    def test_config_error_recovery(self, tmp_path):
        """Test configuration error recovery mechanisms."""
        config_file = tmp_path / "config.json"
        manager = ConfigManager(config_file)

        # Create valid config first
        manager.setup_provider_config(TaskSource.ATLASSIAN, {"cloud_id": "test"})
        assert config_file.exists()

        # Corrupt the config file
        with open(config_file, "w") as f:
            f.write("{ corrupted json")

        # Load should recover gracefully
        recovered_config = manager.load_config()
        assert isinstance(recovered_config, EpicConfig)
        assert recovered_config.providers.task_source == TaskSource.LOCAL

        # Backup should exist
        backup_file = config_file.with_suffix(".json.backup")
        assert backup_file.exists()

    def test_concurrent_config_access(self, tmp_path):
        """Test concurrent configuration access safety."""
        config_file = tmp_path / "config.json"

        # Create two managers for same file
        manager1 = ConfigManager(config_file)
        manager2 = ConfigManager(config_file)

        # Both should be able to load and save
        config1 = manager1.load_config()
        config2 = manager2.load_config()

        # Modify and save from both
        config1.features.auto_assign = False
        config2.features.auto_transition = False

        manager1.save_config(config1)
        manager2.save_config(config2)

        # Last save should win
        final_config = manager1.load_config()
        assert final_config.features.auto_transition is False
