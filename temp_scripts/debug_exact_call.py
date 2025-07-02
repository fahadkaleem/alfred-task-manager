#!/usr/bin/env python3

"""Debug script to simulate the exact call that's failing."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.alfred.core.prompter import generate_prompt
from src.alfred.lib.task_utils import load_task

def main():
    print("=== Debug Exact Call ===")
    
    # Load the actual task
    task = load_task("AL-DRY-RUN-01")
    if not task:
        print("❌ Could not load task AL-DRY-RUN-01")
        return
    
    print(f"✅ Loaded task: {task.task_id}")
    print(f"  Title: {task.title}")
    print(f"  Status: {task.task_status}")
    
    # Simulate the exact call that plan_task makes
    try:
        prompt = generate_prompt(
            task_id="AL-DRY-RUN-01",
            tool_name="plan_task",
            state="contextualize", 
            task=task,
            additional_context={}
        )
        print(f"✅ generate_prompt succeeded, length: {len(prompt)}")
        print(f"Preview: {prompt[:200]}...")
        
        # Check if it's the error template
        if "No prompt template was found" in prompt:
            print("❌ Got the error template instead of the correct one!")
        else:
            print("✅ Got the correct template")
            
    except Exception as e:
        print(f"❌ generate_prompt failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()