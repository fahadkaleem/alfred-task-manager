#!/usr/bin/env python3
"""
Main validation test script for Alfred MCP Tools.

This script orchestrates a comprehensive validation test of all Alfred MCP tools
to ensure they work correctly after recent refactoring.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_harness import ValidationTestHarness


def main():
    """Main function to run the complete validation suite."""
    print("Alfred MCP Tools Validation Test")
    print("=" * 50)

    try:
        # Create and run the validation test harness
        harness = ValidationTestHarness()

        print("Initializing validation test harness...")
        stats = harness.run_full_validation()

        # Determine exit code based on results
        success_rate = stats["success_rate"]
        failed_tests = stats["failed_tests"]

        print(f"\nValidation completed with {success_rate:.1f}% success rate")

        if success_rate >= 90:
            print("✅ VALIDATION PASSED: System is working excellently")
            exit_code = 0
        elif success_rate >= 75:
            print("⚠️  VALIDATION WARNING: System is mostly functional but has some issues")
            exit_code = 1
        else:
            print("❌ VALIDATION FAILED: System has significant issues")
            exit_code = 2

        if failed_tests > 0:
            print(f"Failed tests: {stats['failed_test_names']}")

        return exit_code

    except Exception as e:
        print(f"❌ VALIDATION ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
