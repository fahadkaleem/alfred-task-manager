#!/usr/bin/env python3
"""Debug the revision flow to see state transitions."""

import sys
sys.path.append('/Users/mohammedfahadkaleem/Documents/Workspace/alfred-task-manager')

from src.alfred.state.recovery import ToolRecovery

task_id = "TEST-006"
tool = ToolRecovery.recover_tool(task_id)

if tool:
    print(f"Current state: {tool.state}")
    print(f"Feedback in context: {'feedback_notes' in tool.context_store}")
    
    # Check state history if available
    if hasattr(tool, 'state_history'):
        print(f"\nState history: {tool.state_history}")