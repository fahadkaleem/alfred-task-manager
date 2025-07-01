#!/usr/bin/env python3
"""Validation helper functions for MCP tool responses."""

import json
import sys


def validate_tool_response(response: dict, expected_status: str = "success") -> bool:
    """Verifies response has 'status', 'message' fields and matches expected status."""
    if not isinstance(response, dict):
        return False

    if "status" not in response or "message" not in response:
        return False

    return response["status"] == expected_status


def assert_response_structure(response: dict, required_fields: list) -> None:
    """Raises assertion error if required fields are missing from response."""
    if not isinstance(response, dict):
        raise AssertionError(f"Response is not a dict: {type(response)}")

    missing_fields = [field for field in required_fields if field not in response]
    if missing_fields:
        raise AssertionError(f"Missing required fields: {missing_fields}")


def extract_next_prompt(response: dict) -> str:
    """Safely extracts next_prompt field from response."""
    if not isinstance(response, dict):
        return ""

    return response.get("next_prompt", "")


def log_test_result(test_name: str, passed: bool, details: str = "") -> None:
    """Prints formatted test results."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
