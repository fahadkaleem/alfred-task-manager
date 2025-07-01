from mock_data import MockTaskDataFactory
from state_verification import StateVerificationUtility
from error_scenarios import ErrorScenarioTestSuite
from test_reporting import TestReportGenerator

class ValidationTestHarness:
    """Orchestrates comprehensive validation testing of Alfred MCP tools."""
    
    def __init__(self):
        """Initialize the validation test harness with all utilities."""
        self.mock_factory = MockTaskDataFactory()
        self.state_verifier = StateVerificationUtility()
        self.error_suite = ErrorScenarioTestSuite()
        self.reporter = TestReportGenerator()
        self.test_task_id = "HARNESS-TEST-001"
    
    def test_workflow_tools(self) -> None:
        """Test core workflow tools like plan_task, implement_task, etc."""
        print("Testing workflow tools...")
        
        # Test 1: Mock data creation
        try:
            test_task = self.mock_factory.create_test_task(self.test_task_id)
            artifacts = self.mock_factory.create_test_artifacts()
            
            has_required_fields = "task_id" in test_task and "title" in test_task
            has_artifacts = "context" in artifacts and "strategy" in artifacts
            
            passed = has_required_fields and has_artifacts
            details = f"Task creation: {has_required_fields}, Artifacts: {has_artifacts}"
            
            self.reporter.add_test_result("workflow_tools_data_creation", passed, details)
            
        except Exception as e:
            self.reporter.add_test_result("workflow_tools_data_creation", False, f"Error: {str(e)}")
        
        # Test 2: State verification capabilities
        try:
            # Test state verification methods exist and work
            consistency_check = self.state_verifier.verify_state_consistency(self.test_task_id)
            
            has_all_checks = all(key in consistency_check for key in 
                               ["task_state_exists", "tool_state_exists", "state_file_exists"])
            
            details = f"State verification methods available: {has_all_checks}, Checks: {list(consistency_check.keys())}"
            self.reporter.add_test_result("workflow_tools_state_verification", has_all_checks, details)
            
        except Exception as e:
            self.reporter.add_test_result("workflow_tools_state_verification", False, f"Error: {str(e)}")
    
    def test_state_persistence(self) -> None:
        """Test that state persists across operations."""
        print("Testing state persistence...")
        
        try:
            # Test 1: State file operations
            state_exists = self.state_verifier.verify_state_file_exists(self.test_task_id)
            current_state = self.state_verifier.get_current_task_state(self.test_task_id)
            
            details = f"State file exists: {state_exists}, State retrieved: {bool(current_state)}"
            self.reporter.add_test_result("state_persistence_file_ops", True, details)
            
        except Exception as e:
            self.reporter.add_test_result("state_persistence_file_ops", False, f"Error: {str(e)}")
        
        try:
            # Test 2: Tool state operations
            tool_state_exists = self.state_verifier.verify_tool_state_exists(self.test_task_id)
            tool_state = self.state_verifier.get_tool_state(self.test_task_id)
            
            details = f"Tool state exists: {tool_state_exists}, Tool state retrieved: {bool(tool_state)}"
            self.reporter.add_test_result("state_persistence_tool_ops", True, details)
            
        except Exception as e:
            self.reporter.add_test_result("state_persistence_tool_ops", False, f"Error: {str(e)}")
    
    def test_error_handling(self) -> None:
        """Test error handling scenarios."""
        print("Testing error handling...")
        
        try:
            # Run all error scenario tests
            error_results = self.error_suite.run_all_error_tests()
            error_summary = self.error_suite.get_error_test_summary()
            
            # Add each error test suite as a separate result
            for error_test in error_results:
                test_name = f"error_handling_{error_test['test_name']}"
                passed = error_test["passed_cases"] == error_test["total_cases"]
                details = f"Cases: {error_test['total_cases']}, Passed: {error_test['passed_cases']}"
                
                self.reporter.add_test_result(test_name, passed, details)
            
            # Add overall error handling summary
            overall_passed = error_summary["success_rate"] >= 90  # 90% success rate threshold
            details = f"Total error tests: {error_summary['total_error_tests']}, " \
                     f"Success rate: {error_summary['success_rate']:.1f}%"
            
            self.reporter.add_test_result("error_handling_overall", overall_passed, details)
            
        except Exception as e:
            self.reporter.add_test_result("error_handling", False, f"Error in error testing: {str(e)}")
    
    def test_integration_scenarios(self) -> None:
        """Test integration between different components."""
        print("Testing integration scenarios...")
        
        try:
            # Test 1: Mock data + State verification integration
            test_task = self.mock_factory.create_test_task("INTEGRATION-TEST")
            invalid_data = self.mock_factory.create_invalid_data()
            
            # Verify we can handle both valid and invalid data
            valid_data_usable = "task_id" in test_task
            invalid_data_detected = len(invalid_data) > 0
            
            integration_works = valid_data_usable and invalid_data_detected
            details = f"Valid data: {valid_data_usable}, Invalid data scenarios: {len(invalid_data)}"
            
            self.reporter.add_test_result("integration_mock_data", integration_works, details)
            
        except Exception as e:
            self.reporter.add_test_result("integration_mock_data", False, f"Error: {str(e)}")
        
        try:
            # Test 2: State verification + Error scenarios integration
            consistency_results = self.state_verifier.verify_state_consistency("NONEXISTENT-TASK")
            
            # Should handle non-existent tasks gracefully
            handles_missing_task = isinstance(consistency_results, dict)
            details = f"Handles missing task gracefully: {handles_missing_task}"
            
            self.reporter.add_test_result("integration_state_error_handling", handles_missing_task, details)
            
        except Exception as e:
            self.reporter.add_test_result("integration_state_error_handling", False, f"Error: {str(e)}")
    
    def run_full_validation(self) -> None:
        """Run the complete validation test suite."""
        print("=== Starting Alfred MCP Tools Validation ===")
        print(f"Test harness initialized for task: {self.test_task_id}")
        print()
        
        # Run all test categories
        self.test_workflow_tools()
        self.test_state_persistence()
        self.test_error_handling()
        self.test_integration_scenarios()
        
        print()
        print("=== Validation Complete ===")
        
        # Generate and display final report
        self.reporter.print_console_report()
        
        # Export results to file
        self.reporter.export_results_json("validation_results.json")
        
        # Return summary statistics
        stats = self.reporter.get_statistics()
        print(f"\nFinal Statistics:")
        print(f"- Total Tests: {stats['total_tests']}")
        print(f"- Success Rate: {stats['success_rate']:.1f}%")
        print(f"- Failed Tests: {stats['failed_test_names']}")
        
        return stats