# CRITICAL REFACTORING INSTRUCTION: Step 2 - Extract Workflow State Machine Builder

**ATTENTION**: This is the second CRITICAL refactoring task. You must extract the duplicated state machine logic from all workflow tools into a centralized builder. This is complex - triple check that all state transitions remain EXACTLY the same.

## OBJECTIVE
Replace duplicated state machine creation logic in PlanTaskTool, ImplementTaskTool, ReviewTaskTool, TestTaskTool, and FinalizeTaskTool with a single WorkflowStateMachineBuilder.

## CURRENT PROBLEM
Every workflow tool has:
- The same `_create_review_transitions` method (duplicated 5+ times)
- Similar state machine initialization patterns
- Repeated review state generation logic
- Almost identical transition definitions

This results in ~100 lines of duplicated code per tool class.

## STEP-BY-STEP IMPLEMENTATION

### 1. Create the State Machine Builder
**CREATE** a new file: `src/alfred/core/state_machine_builder.py`

```python
"""
Centralized state machine builder for workflow tools.
Eliminates duplication of state machine creation logic.
"""
from enum import Enum
from typing import List, Dict, Any, Type, Optional, Union
from transitions import Machine

from src.alfred.constants import Triggers
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class WorkflowStateMachineBuilder:
    """
    Builder for creating workflow state machines with standardized review cycles.
    
    This builder encapsulates the common pattern used across all workflow tools:
    1. Work states that require review
    2. AI review state
    3. Human review state
    4. Transitions between states
    """
    
    def __init__(self):
        self.states: List[str] = []
        self.transitions: List[Dict[str, Any]] = []
        
    def create_review_transitions(
        self, 
        source_state: str, 
        success_destination_state: str,
        revision_destination_state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Creates a standard review cycle for a work state.
        
        This generates:
        1. work_state -> work_state_awaiting_ai_review (via submit trigger)
        2. ai_review -> human_review (via ai_approve trigger)
        3. ai_review -> work_state (via request_revision trigger)
        4. human_review -> next_state (via human_approve trigger)
        5. human_review -> work_state (via request_revision trigger)
        """
        if revision_destination_state is None:
            revision_destination_state = source_state
            
        # Generate state names
        ai_review_state = f"{source_state}_awaiting_ai_review"
        human_review_state = f"{source_state}_awaiting_human_review"
        
        return [
            # Submit work to enter review cycle
            {
                "trigger": Triggers.submit_trigger(source_state),
                "source": source_state,
                "dest": ai_review_state,
            },
            # AI approves
            {
                "trigger": Triggers.AI_APPROVE,
                "source": ai_review_state,
                "dest": human_review_state,
            },
            # AI requests revision
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": ai_review_state,
                "dest": revision_destination_state,
            },
            # Human approves
            {
                "trigger": Triggers.HUMAN_APPROVE,
                "source": human_review_state,
                "dest": success_destination_state,
            },
            # Human requests revision
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": human_review_state,
                "dest": revision_destination_state,
            },
        ]
    
    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        return [
            f"{state}_awaiting_ai_review",
            f"{state}_awaiting_human_review"
        ]
    
    def build_workflow_with_reviews(
        self,
        work_states: List[Union[str, Enum]],
        terminal_state: Union[str, Enum],
        initial_state: Union[str, Enum]
    ) -> Dict[str, Any]:
        """
        Build a complete workflow with review cycles for each work state.
        
        Args:
            work_states: List of states that require review cycles
            terminal_state: Final state of the workflow
            initial_state: Starting state of the workflow
            
        Returns:
            Dictionary with 'states' and 'transitions' for Machine initialization
        """
        all_states = []
        all_transitions = []
        
        # Convert enums to strings if needed
        work_state_values = [
            s.value if hasattr(s, 'value') else s 
            for s in work_states
        ]
        terminal_value = terminal_state.value if hasattr(terminal_state, 'value') else terminal_state
        initial_value = initial_state.value if hasattr(initial_state, 'value') else initial_state
        
        # Add all work states and their review states
        for i, state in enumerate(work_state_values):
            # Add the work state
            all_states.append(state)
            
            # Add review states
            review_states = self.get_review_states_for_state(state)
            all_states.extend(review_states)
            
            # Determine next state
            if i + 1 < len(work_state_values):
                next_state = work_state_values[i + 1]
            else:
                next_state = terminal_value
                
            # Create transitions for this state
            transitions = self.create_review_transitions(
                source_state=state,
                success_destination_state=next_state
            )
            all_transitions.extend(transitions)
        
        # Add terminal state
        all_states.append(terminal_value)
        
        return {
            "states": all_states,
            "transitions": all_transitions,
            "initial": initial_value
        }
    
    def build_simple_workflow(
        self,
        dispatch_state: Union[str, Enum],
        work_state: Union[str, Enum],
        terminal_state: Union[str, Enum],
        dispatch_trigger: str = "dispatch"
    ) -> Dict[str, Any]:
        """
        Build a simple workflow: dispatch -> work (with review) -> terminal.
        
        This is the pattern used by implement, review, test, and finalize tools.
        """
        dispatch_value = dispatch_state.value if hasattr(dispatch_state, 'value') else dispatch_state
        work_value = work_state.value if hasattr(work_state, 'value') else work_state
        terminal_value = terminal_state.value if hasattr(terminal_state, 'value') else terminal_state
        
        states = [
            dispatch_value,
            work_value,
            f"{work_value}_awaiting_ai_review",
            f"{work_value}_awaiting_human_review",
            terminal_value
        ]
        
        transitions = [
            {
                "trigger": dispatch_trigger,
                "source": dispatch_value,
                "dest": work_value
            }
        ]
        
        # Add review transitions
        transitions.extend(
            self.create_review_transitions(
                source_state=work_value,
                success_destination_state=terminal_value
            )
        )
        
        return {
            "states": states,
            "transitions": transitions,
            "initial": dispatch_value
        }


# Singleton instance for convenience
workflow_builder = WorkflowStateMachineBuilder()
```

### 2. Create Base Workflow Tool Class
**UPDATE** `src/alfred/core/workflow.py` to remove duplication and use the builder:

```python
# At the top of the file, add import
from src.alfred.core.state_machine_builder import workflow_builder

# Update the BaseWorkflowTool class - REMOVE the _create_review_transitions method
class BaseWorkflowTool:
    def __init__(self, task_id: str, tool_name: str):
        self.task_id = task_id
        self.tool_name = tool_name
        self.state: Optional[str] = None
        self.machine: Optional[Machine] = None
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}
        self.context_store: Dict[str, Any] = {}

    @property
    def is_terminal(self) -> bool:
        return self.state == "verified"

    # DELETE the _create_review_transitions method - it's now in the builder

    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        # Delegate to builder
        return workflow_builder.get_review_states_for_state(state)

    def get_final_work_state(self) -> str:
        """Get the final work state that produces the main artifact."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_final_work_state()")
```

### 3. Update PlanTaskTool
**UPDATE** the PlanTaskTool class in `src/alfred/core/workflow.py`:

```python
class PlanTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK)
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SUBTASKS: ExecutionPlanArtifact,
        }

        # Use the builder to create the state machine configuration
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=[
                PlanTaskState.CONTEXTUALIZE,
                PlanTaskState.STRATEGIZE,
                PlanTaskState.DESIGN,
                PlanTaskState.GENERATE_SUBTASKS
            ],
            terminal_state=PlanTaskState.VERIFIED,
            initial_state=PlanTaskState.CONTEXTUALIZE
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return PlanTaskState.GENERATE_SUBTASKS.value
```

### 4. Update StartTaskTool
**UPDATE** the StartTaskTool class:

```python
class StartTaskTool(BaseWorkflowTool):
    """Re-architected StartTaskTool with a streamlined state machine."""

    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.START_TASK)
        self.artifact_map = {
            StartTaskState.AWAITING_GIT_STATUS: GitStatusArtifact,
            StartTaskState.AWAITING_BRANCH_CREATION: BranchCreationArtifact,
        }

        # Use builder for the two-step workflow
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=[
                StartTaskState.AWAITING_GIT_STATUS,
                StartTaskState.AWAITING_BRANCH_CREATION
            ],
            terminal_state=StartTaskState.VERIFIED,
            initial_state=StartTaskState.AWAITING_GIT_STATUS
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return StartTaskState.AWAITING_BRANCH_CREATION.value
```

### 5. Update Simple Workflow Tools
**UPDATE** ImplementTaskTool, ReviewTaskTool, TestTaskTool, and FinalizeTaskTool:

```python
class ImplementTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.IMPLEMENT_TASK)
        self.artifact_map = {
            ImplementTaskState.IMPLEMENTING: ImplementationManifestArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=ImplementTaskState.DISPATCHING,
            work_state=ImplementTaskState.IMPLEMENTING,
            terminal_state=ImplementTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return ImplementTaskState.IMPLEMENTING.value


class ReviewTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.REVIEW_TASK)
        self.artifact_map = {
            ReviewTaskState.REVIEWING: ReviewArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=ReviewTaskState.DISPATCHING,
            work_state=ReviewTaskState.REVIEWING,
            terminal_state=ReviewTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return ReviewTaskState.REVIEWING.value


class TestTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.TEST_TASK)
        self.artifact_map = {
            TestTaskState.TESTING: TestResultArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=TestTaskState.DISPATCHING,
            work_state=TestTaskState.TESTING,
            terminal_state=TestTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return TestTaskState.TESTING.value


class FinalizeTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.FINALIZE_TASK)
        self.artifact_map = {
            FinalizeTaskState.FINALIZING: FinalizeArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=FinalizeTaskState.DISPATCHING,
            work_state=FinalizeTaskState.FINALIZING,
            terminal_state=FinalizeTaskState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return FinalizeTaskState.FINALIZING.value
```

### 6. Update CreateSpecTool and CreateTasksTool
**UPDATE** these tools to use the builder pattern:

```python
class CreateSpecTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_SPEC)
        self.artifact_map = {
            CreateSpecState.DRAFTING_SPEC: EngineeringSpec,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=CreateSpecState.DISPATCHING,
            work_state=CreateSpecState.DRAFTING_SPEC,
            terminal_state=CreateSpecState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return CreateSpecState.DRAFTING_SPEC.value


class CreateTasksTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_TASKS)
        self.artifact_map = {
            CreateTasksState.DRAFTING_TASKS: TaskCreationArtifact,
        }

        # Use builder for simple workflow
        machine_config = workflow_builder.build_simple_workflow(
            dispatch_state=CreateTasksState.DISPATCHING,
            work_state=CreateTasksState.DRAFTING_TASKS,
            terminal_state=CreateTasksState.VERIFIED
        )

        self.machine = Machine(
            model=self,
            states=machine_config["states"],
            transitions=machine_config["transitions"],
            initial=machine_config["initial"],
            auto_transitions=False
        )

    def get_final_work_state(self) -> str:
        return CreateTasksState.DRAFTING_TASKS.value
```

## VERIFICATION CHECKLIST
**CRITICAL**: After making these changes, verify:

1. ✓ All state machines work EXACTLY as before
2. ✓ Review cycles still have correct state names (e.g., "contextualize_awaiting_ai_review")
3. ✓ All triggers work correctly (submit_contextualize, ai_approve, etc.)
4. ✓ State transitions are identical to the original
5. ✓ The `get_review_states_for_state` method still works
6. ✓ All imports are updated correctly
7. ✓ No state machine initialization code is duplicated
8. ✓ The builder handles both Enum and string states correctly

## TESTING REQUIREMENTS
**CRITICAL** - Test these exact scenarios:

1. **PlanTaskTool**: 
   - Start in contextualize
   - Submit work -> should go to contextualize_awaiting_ai_review
   - AI approve -> should go to contextualize_awaiting_human_review
   - Human approve -> should go to strategize
   - Repeat for all 4 work states

2. **Simple Tools** (Implement/Review/Test/Finalize):
   - Start in dispatching state
   - Dispatch -> should go to work state
   - Submit -> should go to work_awaiting_ai_review
   - Full review cycle
   - Should end in verified state

3. **StartTaskTool**:
   - Test both git status and branch creation states
   - Verify review cycles work for both

4. **Edge Cases**:
   - Request revision from AI review -> returns to work state
   - Request revision from human review -> returns to work state
   - Verify all state names are correctly formatted

## METRICS TO VERIFY

Count the following:
- Lines removed from BaseWorkflowTool: ~30-40 lines
- Lines removed from each tool class: ~20-30 lines each
- Total lines removed: ~200-250 lines
- Lines added in state_machine_builder.py: ~150 lines
- **Net reduction: ~50-100 lines**

More importantly:
- State machine logic is now in ONE place
- Adding a new workflow tool is much simpler
- Bug fixes to state machine logic only need to be done once

## FINAL VALIDATION

Run this Python script to verify state machines are identical:

```python
# Test script to verify state machines are equivalent
from src.alfred.core.workflow import (
    PlanTaskTool, ImplementTaskTool, ReviewTaskTool, 
    TestTaskTool, FinalizeTaskTool
)

def print_state_machine_info(tool_class, task_id="test-1"):
    tool = tool_class(task_id)
    print(f"\n{tool_class.__name__}:")
    print(f"  States: {sorted(tool.machine.states)}")
    print(f"  Initial: {tool.machine.initial}")
    print(f"  Triggers: {sorted(set(t['trigger'] for t in tool.machine.transitions))}")

# Run for each tool
for tool_cls in [PlanTaskTool, ImplementTaskTool, ReviewTaskTool, TestTaskTool, FinalizeTaskTool]:
    print_state_machine_info(tool_cls)
```

The output should match EXACTLY with the original implementation.