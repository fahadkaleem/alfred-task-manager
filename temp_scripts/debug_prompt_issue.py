#!/usr/bin/env python3

"""Debug script to investigate the prompt template issue."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.alfred.core.prompter import prompt_library, PromptBuilder

def main():
    print("=== Debug Prompt Template Issue ===")
    
    # Check what prompts are loaded
    prompts = prompt_library.list_prompts()
    print(f"\nLoaded {len(prompts)} prompts:")
    for key, info in sorted(prompts.items()):
        print(f"  {key}: {info['file']}")
    
    # Check specifically for plan_task.contextualize
    key = "plan_task.contextualize"
    print(f"\nChecking for key '{key}':")
    if key in prompts:
        print(f"  ✅ Found: {prompts[key]['file']}")
        print(f"  Required vars: {prompts[key]['required_vars']}")
    else:
        print(f"  ❌ Not found")
    
    # Test get_prompt_key method
    prompt_key = prompt_library.get_prompt_key("plan_task", "contextualize")
    print(f"\nget_prompt_key('plan_task', 'contextualize') = '{prompt_key}'")
    
    # Test if we can get the template
    try:
        template = prompt_library.get(prompt_key)
        print(f"✅ Template found: {type(template)}")
    except Exception as e:
        print(f"❌ Template get failed: {e}")
    
    # Test rendering with minimal context
    context = {
        "task_id": "AL-DRY-RUN-01",
        "tool_name": "plan_task", 
        "current_state": "contextualize",
        "task_title": "Test Task",
        "task_context": "Test context",
        "implementation_details": "Test details",
        "acceptance_criteria": "- Test criteria",
        "feedback_section": ""
    }
    
    try:
        result = prompt_library.render(prompt_key, context)
        print(f"✅ Render successful, length: {len(result)}")
        print(f"Preview: {result[:200]}...")
    except Exception as e:
        print(f"❌ Render failed: {e}")

if __name__ == "__main__":
    main()