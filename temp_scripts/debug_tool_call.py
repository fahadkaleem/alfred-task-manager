#!/usr/bin/env python3

"""Debug script to examine the exact tool call that's failing."""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.task_utils import load_task

def main():
    print("=== Debug Tool Call ===")
    
    # Check active tools
    print(f"Active tools: {list(orchestrator.active_tools.keys())}")
    
    # Get the active tool for our task
    task_id = "AL-DRY-RUN-01"
    if task_id in orchestrator.active_tools:
        tool = orchestrator.active_tools[task_id]
        print(f"Found active tool: {tool}")
        print(f"  Tool name: {tool.tool_name}")
        print(f"  Current state: {tool.state}")
        print(f"  State type: {type(tool.state)}")
        
        # Load task
        task = load_task(task_id)
        if task:
            print(f"Task loaded: {task.task_id}")
            
            # Try to generate prompt using tool's internal method
            try:
                from src.alfred.core.prompter import generate_prompt
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
                    print("First 500 chars:")
                    print(prompt[:500])
                else:
                    print("✅ Got correct template")
                    print("Preview:")
                    print(prompt[:200] + "...")
                    
            except Exception as e:
                print(f"❌ Prompt generation failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Could not load task")
    else:
        print(f"❌ No active tool found for task {task_id}")

if __name__ == "__main__":
    main()