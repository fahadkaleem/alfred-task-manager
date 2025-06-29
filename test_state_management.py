#!/usr/bin/env python3
"""
Test script to verify state management functionality
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import PlanTaskTool
from src.alfred.models.planning_artifacts import ContextAnalysisArtifact, StrategyArtifact

def test_state_persistence():
    """Test that we can save and load tool state with Pydantic models"""
    print("=== Testing State Persistence ===")
    
    # Create a tool
    task_id = "TEST-STATE-01"
    tool = PlanTaskTool(task_id=task_id)
    
    # Add some Pydantic models to context
    context_artifact = ContextAnalysisArtifact(
        context_summary="Test context",
        affected_files=["file1.py", "file2.py"],
        questions_for_developer=["Q1", "Q2"]
    )
    
    strategy_artifact = StrategyArtifact(
        high_level_strategy="Test strategy",
        key_components=["comp1", "comp2"],
        new_dependencies=[],
        risk_analysis="No risks"
    )
    
    # Store in context
    tool.context_store["context"] = context_artifact
    tool.context_store["strategy"] = strategy_artifact
    tool.context_store["plain_data"] = {"key": "value"}
    
    print(f"Original context keys: {list(tool.context_store.keys())}")
    
    # Save state
    try:
        state_manager.save_tool_state(task_id, tool)
        print("✓ State saved successfully")
    except Exception as e:
        print(f"✗ Failed to save state: {e}")
        return False
    
    # Load state back
    loaded_state = state_manager.load_tool_state(task_id)
    if loaded_state:
        print("✓ State loaded successfully")
        print(f"Loaded context keys: {list(loaded_state['context_store'].keys())}")
        
        # Verify data
        assert loaded_state['context_store']['context']['context_summary'] == "Test context"
        assert loaded_state['context_store']['strategy']['high_level_strategy'] == "Test strategy"
        assert loaded_state['context_store']['plain_data']['key'] == "value"
        print("✓ All data verified correctly")
    else:
        print("✗ Failed to load state")
        return False
    
    # Clean up
    state_manager.clear_tool_state(task_id)
    print("✓ State cleaned up")
    
    return True

def test_tool_recovery():
    """Test that we can recover a tool from persisted state"""
    print("\n=== Testing Tool Recovery ===")
    
    # Create and save a tool
    task_id = "TEST-RECOVERY-01"
    tool = PlanTaskTool(task_id=task_id)
    tool.state = "strategize"
    tool.context_store["data"] = {"test": "value"}
    
    state_manager.save_tool_state(task_id, tool)
    print("✓ Tool state saved")
    
    # Try to recover
    recovered_tool = ToolRecovery.recover_tool(task_id)
    if recovered_tool:
        print("✓ Tool recovered successfully")
        print(f"  State: {recovered_tool.state}")
        print(f"  Context: {recovered_tool.context_store}")
        
        assert recovered_tool.state == "strategize"
        assert recovered_tool.context_store["data"]["test"] == "value"
        print("✓ Tool state verified")
    else:
        print("✗ Failed to recover tool")
        return False
    
    # Clean up
    state_manager.clear_tool_state(task_id)
    
    return True

def test_state_file_format():
    """Test the actual state file format"""
    print("\n=== Testing State File Format ===")
    
    task_id = "TEST-FORMAT-01"
    tool = PlanTaskTool(task_id=task_id)
    
    # Add a Pydantic model
    artifact = ContextAnalysisArtifact(
        context_summary="Format test",
        affected_files=["test.py"],
        questions_for_developer=[]
    )
    tool.context_store["artifact"] = artifact
    
    # Save
    state_manager.save_tool_state(task_id, tool)
    
    # Read the raw file
    state_file = state_manager.get_task_state_file(task_id)
    raw_content = state_file.read_text()
    
    print("State file content:")
    print(raw_content)
    
    # Verify it's valid JSON
    try:
        data = json.loads(raw_content)
        print("\n✓ Valid JSON format")
        
        # Check that artifact was converted to dict
        assert isinstance(data['context_store']['artifact'], dict)
        print("✓ Pydantic model converted to dict")
    except Exception as e:
        print(f"\n✗ Invalid JSON: {e}")
        return False
    
    # Clean up
    state_manager.clear_tool_state(task_id)
    
    return True

if __name__ == "__main__":
    print("Testing Alfred State Management System\n")
    
    tests = [
        test_state_persistence,
        test_tool_recovery,
        test_state_file_format
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)