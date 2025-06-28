"""
Tests for ETM-14 Testing Phase Validation Module

This test file validates the functionality of the validation_etm14 module
and demonstrates the testing phase workflow for ETM-14.
"""

from src.epic_task_manager.validation_etm14 import get_validation_message, validate_testing_phase


def test_validate_testing_phase():
    """Test that validate_testing_phase returns True."""
    result = validate_testing_phase()
    assert result is True, "validate_testing_phase should return True"


def test_get_validation_message():
    """Test that get_validation_message returns a string."""
    message = get_validation_message()
    assert isinstance(message, str), "get_validation_message should return a string"
    assert len(message) > 0, "validation message should not be empty"
    assert "ETM-14" in message, "validation message should mention ETM-14"
