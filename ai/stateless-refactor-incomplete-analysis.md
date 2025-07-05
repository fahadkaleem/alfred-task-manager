# Stateless Refactor Incomplete Work Analysis

## Executive Summary

The stateless refactor (TS-03) was partially completed, but significant portions of the codebase still contain remnants of the old stateful design. This document provides a comprehensive analysis of what was left incomplete and what needs to be cleaned up.

## 1. PlanTaskTool Still Uses Stateful Pattern

### Current Issues:
- **File**: `src/alfred/core/discovery_workflow.py`
- **Line 63**: Creates a `Machine` instance with `model=self`, which is the old stateful pattern
- **Multiple empty methods** that previously manipulated `context_store`:
  - `_load_preserved_artifacts()` (lines 79-83)
  - `check_complexity_after_clarification()` (lines 128-132)
  - `initiate_replanning()` (lines 159-161) - partially empty

### What Should Be Done:
- Remove the state machine creation from `__init__`
- Remove all empty methods
- Update to use WorkflowEngine for any state transition needs
- Move any remaining logic to context loaders or workflow configuration

## 2. Direct context_store Manipulation

### Files Still Directly Accessing context_store:
1. **`src/alfred/tools/create_tasks_from_spec.py`** (line 78)
   - `tool.context_store["technical_spec"] = tech_spec`
   
2. **`src/alfred/tools/create_spec.py`** (line 47)
   - `tool.context_store["prd_input"] = prd_artifact`

### What Should Be Done:
- These tools should not be directly accessing `tool.context_store`
- Context should be managed through WorkflowState in the stateless pattern

## 3. StateManager Still Assumes Stateful Tools

### Issues in state/manager.py:
1. **`update_tool_state()` method** (lines 107-126)
   - Line 114: `for key, value in tool.context_store.items()`
   - Line 121: References `tool.state`
   - Assumes tools have `context_store` and `state` attributes

### What Should Be Done:
- This method should be removed or rewritten for stateless design
- State persistence should work with WorkflowState directly, not tool instances

## 4. Orchestrator Still Referenced

### Active Orchestrator Usage:
1. **`src/alfred/state/manager.py`** (lines 190-194)
   - `register_tool()` method still uses orchestrator
   
2. **`src/alfred/tools/base_tool_handler.py`** (lines 52-54, 67)
   - Still checking and storing tools in `orchestrator.active_tools`
   
3. **`src/alfred/task_providers/factory.py`** (lines 26-30)
   - Still imports and uses orchestrator for config

### What Should Be Done:
- The orchestrator pattern should be completely removed
- Active tool tracking should be handled through TaskState/WorkflowState
- Config management should be direct, not through orchestrator

## 4. Legacy Patterns Still in Use

### BaseToolHandler Issues:
- **File**: `src/alfred/tools/base_tool_handler.py`
- Still has methods like `_get_or_create_tool()` that assume stateful tools
- References to orchestrator for active tool management

### What Should Be Done:
- Simplify BaseToolHandler to work only with stateless tools
- Remove any methods that assume tools maintain state

## 5. Incomplete Context Loader Migration

### Issues:
- Some tools still try to set context directly on tool instances
- Not all tools have been updated to use context loaders
- Context loading logic is scattered between tools and context loaders

### What Should Be Done:
- Centralize all context management in context loaders
- Ensure no tool directly manipulates context_store
- Update all tools to follow the stateless pattern

## 6. State Machine Builder Complexity

### Current State:
- The state machine builder creates complex configurations
- But tools shouldn't be creating their own machines anymore
- Only WorkflowEngine should handle state machines

### What Should Be Done:
- Ensure only WorkflowEngine creates state machines
- Tools should only define their states and transitions declaratively

## 7. Mixed Patterns in Tool Definitions

### Issues:
- Some tools follow the new pattern perfectly (most workflow tools)
- Others still have remnants of the old pattern (PlanTaskTool)
- Inconsistent implementation across the codebase

## Recommendations

### High Priority:
1. **Fix PlanTaskTool completely** - Remove all stateful code
2. **Remove orchestrator entirely** - It's marked as deprecated but still used
3. **Fix direct context_store access** in create_spec and create_tasks_from_spec

### Medium Priority:
1. **Simplify BaseToolHandler** - Remove stateful assumptions
2. **Standardize context loading** - All context through loaders
3. **Clean up empty methods** - Remove all pass-only methods

### Low Priority:
1. **Document the stateless pattern** - Add clear guidelines
2. **Add validation** - Ensure tools don't create state machines
3. **Refactor tests** - Ensure they test stateless behavior

## Technical Debt Impact

The incomplete refactor creates several issues:
- **Confusion**: Developers see two patterns and don't know which to follow
- **Bugs**: Some code paths may assume stateful behavior
- **Maintenance**: Having to maintain two patterns increases complexity
- **Testing**: Tests may not properly validate stateless behavior

## Conclusion

While the core of the stateless refactor was completed (WorkflowEngine, BaseWorkflowTool, most tools), significant cleanup work remains. The PlanTaskTool is the most glaring example of incomplete migration, but there are systematic issues throughout the codebase where the old patterns persist.

The refactor should be completed to avoid the technical debt of maintaining two architectural patterns simultaneously.