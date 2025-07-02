#!/usr/bin/env python3

"""Debug script to test tool recovery."""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.alfred.state.recovery import ToolRecovery
from src.alfred.orchestration.orchestrator import orchestrator

def main():
    print("=== Debug Tool Recovery ===")
    
    task_id = "AL-DRY-RUN-01"
    
    # Try to recover the tool
    print(f"Attempting to recover tool for task {task_id}...")
    
    try:
        tool = ToolRecovery.recover_tool(task_id)
        if tool:
            print(f"✅ Tool recovered: {tool}")
            print(f"  Tool name: {tool.tool_name}")
            print(f"  Current state: {tool.state}")
            print(f"  State type: {type(tool.state)}")
            print(f"  Context store: {tool.context_store}")
            
            # Add to orchestrator
            orchestrator.active_tools[task_id] = tool
            print(f"✅ Tool added to orchestrator")
            
            # Now try the prompt generation
            from src.alfred.core.prompter import generate_prompt
            from src.alfred.lib.task_utils import load_task
            
            task = load_task(task_id)
            if task:
                prompt = generate_prompt(
                    task_id=task.task_id,
                    tool_name=tool.tool_name,
                    state=tool.state,
                    task=task,
                    additional_context=tool.context_store.copy()
                )
                print(f"✅ Prompt generation succeeded, length: {len(prompt)}")
                if "No prompt template was found" in prompt:
                    print("❌ Got error template!")
                    print(prompt[:500])
                else:
                    print("✅ Got correct template")
                    
        else:
            print("❌ Tool recovery returned None")
            
    except Exception as e:
        print(f"❌ Tool recovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()