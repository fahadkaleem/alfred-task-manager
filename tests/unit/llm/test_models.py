"""
Tests for LLM data models and validation.

Tests the data models used across the LLM provider system following Alfred's testing principles.
"""

import pytest
from datetime import datetime, timezone
from typing import List

from alfred.llm.providers.base import (
    ModelCapability,
    ModelResponse,
    ModelInfo,
)


class TestModelCapabilityEnum:
    """Test ModelCapability enum functionality."""

    def test_capability_values(self):
        """Test that capability enum has expected values."""
        assert ModelCapability.TEXT_GENERATION == "text_generation"
        assert ModelCapability.CODE_GENERATION == "code_generation"
        assert ModelCapability.REASONING == "reasoning"
        assert ModelCapability.ANALYSIS == "analysis"

    def test_capability_iteration(self):
        """Test iterating over all capabilities."""
        capabilities = list(ModelCapability)
        assert len(capabilities) == 4

        expected_values = {"text_generation", "code_generation", "reasoning", "analysis"}
        actual_values = {cap.value for cap in capabilities}
        assert actual_values == expected_values

    def test_capability_membership(self):
        """Test capability membership testing."""
        assert "text_generation" in ModelCapability
        assert "invalid_capability" not in ModelCapability

    def test_capability_comparison(self):
        """Test capability comparison operations."""
        cap1 = ModelCapability.TEXT_GENERATION
        cap2 = ModelCapability.TEXT_GENERATION
        cap3 = ModelCapability.CODE_GENERATION

        assert cap1 == cap2
        assert cap1 != cap3
        assert cap1 == "text_generation"
        assert cap1 != "code_generation"


class TestModelResponseValidation:
    """Test ModelResponse data model validation."""

    def test_minimal_valid_response(self):
        """Test creating minimal valid response."""
        response = ModelResponse(content="Hello world", model_name="test-model")

        assert response.content == "Hello world"
        assert response.model_name == "test-model"
        assert response.usage == {}
        assert response.metadata == {}
        assert isinstance(response.timestamp, datetime)

    def test_complete_response(self):
        """Test creating complete response with all fields."""
        timestamp = datetime.now(timezone.utc)
        usage = {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
        metadata = {"provider": "test", "model_version": "1.0"}

        response = ModelResponse(content="Generated content", model_name="advanced-model", usage=usage, metadata=metadata, timestamp=timestamp)

        assert response.content == "Generated content"
        assert response.model_name == "advanced-model"
        assert response.usage == usage
        assert response.metadata == metadata
        assert response.timestamp == timestamp

    def test_empty_content_allowed(self):
        """Test that empty content is allowed."""
        response = ModelResponse(content="", model_name="test-model")

        assert response.content == ""

    def test_usage_data_types(self):
        """Test various usage data types."""
        # Test with integer values
        response1 = ModelResponse(content="test", model_name="test-model", usage={"tokens": 100})
        assert response1.usage["tokens"] == 100

        # Test with mixed data types (should be allowed)
        response2 = ModelResponse(content="test", model_name="test-model", usage={"tokens": 100, "cost": 0.01, "duration": 1.5})
        assert response2.usage["tokens"] == 100
        assert response2.usage["cost"] == 0.01
        assert response2.usage["duration"] == 1.5

    def test_metadata_flexibility(self):
        """Test that metadata accepts various data types."""
        complex_metadata = {"string_field": "value", "number_field": 42, "float_field": 3.14, "bool_field": True, "list_field": [1, 2, 3], "dict_field": {"nested": "value"}, "none_field": None}

        response = ModelResponse(content="test", model_name="test-model", metadata=complex_metadata)

        assert response.metadata == complex_metadata

    def test_response_immutability(self):
        """Test that ModelResponse is immutable after creation."""
        response = ModelResponse(content="original", model_name="test-model")

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            response.content = "modified"

        with pytest.raises(AttributeError):
            response.model_name = "modified-model"

        with pytest.raises(AttributeError):
            response.timestamp = datetime.now(timezone.utc)

    def test_response_serialization(self):
        """Test that ModelResponse can be serialized."""
        response = ModelResponse(content="test content", model_name="test-model", usage={"tokens": 10}, metadata={"provider": "test"})

        # Should be able to convert to dict
        response_dict = response.model_dump()

        assert response_dict["content"] == "test content"
        assert response_dict["model_name"] == "test-model"
        assert response_dict["usage"] == {"tokens": 10}
        assert response_dict["metadata"] == {"provider": "test"}
        assert "timestamp" in response_dict

    def test_required_field_validation(self):
        """Test validation of required fields."""
        # Missing content should fail
        with pytest.raises(ValueError):
            ModelResponse(model_name="test-model")

        # Missing model_name should fail
        with pytest.raises(ValueError):
            ModelResponse(content="test content")

        # Both missing should fail
        with pytest.raises(ValueError):
            ModelResponse()


class TestModelInfoValidation:
    """Test ModelInfo data model validation."""

    def test_minimal_valid_model_info(self):
        """Test creating minimal valid model info."""
        info = ModelInfo(name="test-model", provider="test-provider", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        assert info.name == "test-model"
        assert info.provider == "test-provider"
        assert info.capabilities == [ModelCapability.TEXT_GENERATION]
        assert info.context_window == 4096
        assert info.max_output_tokens is None
        assert info.cost_per_input_token is None
        assert info.cost_per_output_token is None

    def test_complete_model_info(self):
        """Test creating complete model info with all fields."""
        capabilities = [ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING]

        info = ModelInfo(
            name="advanced-model", provider="advanced-provider", capabilities=capabilities, context_window=32768, max_output_tokens=4096, cost_per_input_token=0.01, cost_per_output_token=0.03
        )

        assert info.name == "advanced-model"
        assert info.provider == "advanced-provider"
        assert info.capabilities == capabilities
        assert info.context_window == 32768
        assert info.max_output_tokens == 4096
        assert info.cost_per_input_token == 0.01
        assert info.cost_per_output_token == 0.03

    def test_single_capability(self):
        """Test model with single capability."""
        info = ModelInfo(name="simple-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=2048)

        assert len(info.capabilities) == 1
        assert ModelCapability.TEXT_GENERATION in info.capabilities

    def test_multiple_capabilities(self):
        """Test model with multiple capabilities."""
        capabilities = [ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING, ModelCapability.ANALYSIS]

        info = ModelInfo(name="full-capability-model", provider="test", capabilities=capabilities, context_window=100000)

        assert len(info.capabilities) == 4
        for capability in capabilities:
            assert capability in info.capabilities

    def test_empty_capabilities_list(self):
        """Test that empty capabilities list is allowed."""
        info = ModelInfo(name="no-capability-model", provider="test", capabilities=[], context_window=1024)

        assert len(info.capabilities) == 0

    def test_cost_information_types(self):
        """Test various cost information types."""
        # Test with float costs
        info1 = ModelInfo(name="expensive-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096, cost_per_input_token=0.001, cost_per_output_token=0.002)
        assert info1.cost_per_input_token == 0.001
        assert info1.cost_per_output_token == 0.002

        # Test with integer costs (should be converted to float)
        info2 = ModelInfo(name="simple-cost-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096, cost_per_input_token=1, cost_per_output_token=2)
        assert info2.cost_per_input_token == 1.0
        assert info2.cost_per_output_token == 2.0

    def test_large_context_windows(self):
        """Test models with large context windows."""
        # Test 1M token context window
        info = ModelInfo(
            name="large-context-model",
            provider="test",
            capabilities=[ModelCapability.TEXT_GENERATION],
            context_window=1048576,  # 1M tokens
        )

        assert info.context_window == 1048576

    def test_model_info_immutability(self):
        """Test that ModelInfo is immutable after creation."""
        info = ModelInfo(name="test-model", provider="test-provider", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            info.name = "modified-model"

        with pytest.raises(AttributeError):
            info.provider = "modified-provider"

        with pytest.raises(AttributeError):
            info.context_window = 8192

    def test_model_info_serialization(self):
        """Test that ModelInfo can be serialized."""
        info = ModelInfo(
            name="serializable-model",
            provider="test-provider",
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING],
            context_window=4096,
            max_output_tokens=1024,
            cost_per_input_token=0.001,
            cost_per_output_token=0.002,
        )

        # Should be able to convert to dict
        info_dict = info.model_dump()

        assert info_dict["name"] == "serializable-model"
        assert info_dict["provider"] == "test-provider"
        assert info_dict["context_window"] == 4096
        assert info_dict["max_output_tokens"] == 1024
        assert info_dict["cost_per_input_token"] == 0.001
        assert info_dict["cost_per_output_token"] == 0.002

        # Capabilities should be serialized as strings
        assert len(info_dict["capabilities"]) == 2
        assert "text_generation" in info_dict["capabilities"]
        assert "reasoning" in info_dict["capabilities"]

    def test_required_field_validation(self):
        """Test validation of required fields."""
        # Missing name should fail
        with pytest.raises(ValueError):
            ModelInfo(provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        # Missing provider should fail
        with pytest.raises(ValueError):
            ModelInfo(name="test-model", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        # Missing capabilities should fail
        with pytest.raises(ValueError):
            ModelInfo(name="test-model", provider="test", context_window=4096)

        # Missing context_window should fail
        with pytest.raises(ValueError):
            ModelInfo(name="test-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION])


class TestModelDataIntegration:
    """Test integration between model data structures."""

    def test_model_response_with_model_info(self):
        """Test using ModelInfo data in ModelResponse."""
        # Create model info
        model_info = ModelInfo(name="integration-model", provider="test-provider", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        # Create response using model info data
        response = ModelResponse(
            content="Generated using integration model",
            model_name=model_info.name,
            metadata={"provider": model_info.provider, "context_window": model_info.context_window, "capabilities": [cap.value for cap in model_info.capabilities]},
        )

        assert response.model_name == "integration-model"
        assert response.metadata["provider"] == "test-provider"
        assert response.metadata["context_window"] == 4096
        assert response.metadata["capabilities"] == ["text_generation"]

    def test_capability_consistency(self):
        """Test capability consistency across models."""
        # Create multiple models with different capability combinations
        models = [
            ModelInfo(name="basic-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=2048),
            ModelInfo(name="code-model", provider="test", capabilities=[ModelCapability.CODE_GENERATION], context_window=4096),
            ModelInfo(name="reasoning-model", provider="test", capabilities=[ModelCapability.REASONING, ModelCapability.ANALYSIS], context_window=8192),
            ModelInfo(
                name="full-model",
                provider="test",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING, ModelCapability.ANALYSIS],
                context_window=32768,
            ),
        ]

        # Verify each model has valid capabilities
        for model in models:
            assert len(model.capabilities) > 0
            for capability in model.capabilities:
                assert isinstance(capability, ModelCapability)

        # Verify capability progression makes sense
        assert len(models[0].capabilities) == 1  # Basic
        assert len(models[1].capabilities) == 1  # Code
        assert len(models[2].capabilities) == 2  # Reasoning + Analysis
        assert len(models[3].capabilities) == 4  # All capabilities

    def test_model_comparison_scenarios(self):
        """Test realistic model comparison scenarios."""
        # Fast, cheap model
        fast_model = ModelInfo(
            name="fast-model",
            provider="speed-provider",
            capabilities=[ModelCapability.TEXT_GENERATION],
            context_window=4096,
            max_output_tokens=1024,
            cost_per_input_token=0.0001,
            cost_per_output_token=0.0001,
        )

        # Powerful, expensive model
        powerful_model = ModelInfo(
            name="powerful-model",
            provider="quality-provider",
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING, ModelCapability.ANALYSIS],
            context_window=200000,
            max_output_tokens=8192,
            cost_per_input_token=0.01,
            cost_per_output_token=0.03,
        )

        # Verify cost differences
        assert powerful_model.cost_per_input_token > fast_model.cost_per_input_token
        assert powerful_model.cost_per_output_token > fast_model.cost_per_output_token

        # Verify capability differences
        assert len(powerful_model.capabilities) > len(fast_model.capabilities)
        assert ModelCapability.REASONING in powerful_model.capabilities
        assert ModelCapability.REASONING not in fast_model.capabilities

        # Verify context window differences
        assert powerful_model.context_window > fast_model.context_window
