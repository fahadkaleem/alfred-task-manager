from typing import Dict, Any
from datetime import datetime


class MockTaskDataFactory:
    """Factory class for generating test data for Alfred MCP tools validation."""

    @staticmethod
    def create_test_task(task_id: str) -> Dict[str, Any]:
        """Create a test task with standard fields."""
        return {
            "task_id": task_id,
            "title": f"Test Task {task_id}",
            "description": f"This is a test task created for validation purposes with ID {task_id}",
            "status": "new",
            "created_at": datetime.now().isoformat(),
            "priority": "medium",
            "tags": ["test", "validation"],
        }

    @staticmethod
    def create_test_artifacts() -> Dict[str, Any]:
        """Create sample artifacts for planning phase testing."""
        return {
            "context": {
                "understanding": "This is a test task for validating MCP tools functionality",
                "constraints": ["Must follow LOST framework", "Must complete all subtasks"],
                "risks": ["Tool integration issues", "State persistence problems"],
            },
            "strategy": {
                "approach": "Create comprehensive test suite",
                "architecture": "Modular utility classes for different test aspects",
                "dependencies": ["Alfred state manager", "MCP tool interfaces"],
            },
            "design": {
                "components": ["MockTaskDataFactory", "StateVerificationUtility", "ErrorScenarioTestSuite"],
                "interfaces": ["Standard Python class interfaces"],
                "data_flow": "Test data -> Validation -> Results -> Reporting",
            },
        }

    @staticmethod
    def create_invalid_data() -> Dict[str, Any]:
        """Create malformed data for error testing."""
        return {
            "missing_required_field": {"title": "Missing task_id"},
            "invalid_types": {"task_id": 12345, "status": ["invalid", "list"]},
            "empty_strings": {"task_id": "", "title": "", "description": ""},
            "none_values": {"task_id": None, "title": None, "status": None},
        }
