from typing import List, Dict, Any
from datetime import datetime
import json


class TestReportGenerator:
    """Generator for comprehensive test reports and summaries."""

    def __init__(self):
        """Initialize the test report generator."""
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = datetime.now()

    def add_test_result(self, test_name: str, passed: bool, details: str) -> None:
        """Add a test result to the report."""
        result = {"test_name": test_name, "passed": passed, "details": details, "timestamp": datetime.now().isoformat(), "execution_order": len(self.test_results) + 1}
        self.test_results.append(result)

    def add_test_suite_result(self, suite_name: str, suite_results: Dict[str, Any]) -> None:
        """Add results from a complete test suite."""
        passed = suite_results.get("passed_cases", 0) == suite_results.get("total_cases", 0)
        details = f"Suite: {suite_name}, Cases: {suite_results.get('total_cases', 0)}, Passed: {suite_results.get('passed_cases', 0)}"

        if "success_rate" in suite_results:
            details += f", Success Rate: {suite_results['success_rate']:.1f}%"

        self.add_test_result(suite_name, passed, details)

    def generate_summary_report(self) -> str:
        """Create a formatted test summary report."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = f"""
# Alfred MCP Tools Validation Report

## Summary
- **Test Execution Time**: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")} - {end_time.strftime("%H:%M:%S")}
- **Duration**: {duration.total_seconds():.2f} seconds
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {failed_tests}
- **Success Rate**: {success_rate:.1f}%

## Test Results
"""

        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            report += f"### {i}. {result['test_name']} - {status}\n"
            report += f"- **Details**: {result['details']}\n"
            report += f"- **Timestamp**: {result['timestamp']}\n\n"

        if failed_tests > 0:
            report += "## Failed Tests Analysis\n"
            for result in self.test_results:
                if not result["passed"]:
                    report += f"- **{result['test_name']}**: {result['details']}\n"

        report += f"\n## Overall Assessment\n"
        if success_rate >= 90:
            report += "🟢 **EXCELLENT** - System is working very well\n"
        elif success_rate >= 75:
            report += "🟡 **GOOD** - System is mostly functional with minor issues\n"
        elif success_rate >= 50:
            report += "🟠 **FAIR** - System has significant issues that need attention\n"
        else:
            report += "🔴 **POOR** - System has critical issues requiring immediate attention\n"

        return report

    def export_results_json(self, filename: str) -> None:
        """Save test results to a JSON file."""
        export_data = {
            "metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["passed"]),
                "failed_tests": sum(1 for r in self.test_results if not r["passed"]),
                "success_rate": (sum(1 for r in self.test_results if r["passed"]) / len(self.test_results) * 100) if self.test_results else 0,
            },
            "test_results": self.test_results,
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2, sort_keys=True)

        print(f"Test results exported to {filename}")

    def print_console_report(self) -> None:
        """Display test results in the console."""
        report = self.generate_summary_report()
        print(report)

    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the test run."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "test_names": [result["test_name"] for result in self.test_results],
            "failed_test_names": [result["test_name"] for result in self.test_results if not result["passed"]],
        }
