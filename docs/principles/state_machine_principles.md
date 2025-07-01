# **ALFRED STATE MACHINE PRINCIPLES**

## **CORE PHILOSOPHY**
State machines are **PATTERNS, not PUZZLES**. Use the builder. Trust the builder. The builder is complete.

## **THE GOLDEN RULES**

### **1. THE BUILDER IS COMPLETE**
- `WorkflowStateMachineBuilder` handles ALL workflow patterns
- It has TWO methods: `build_workflow_with_reviews` and `build_simple_workflow`
- These two methods cover EVERY use case
- Do NOT add new builder methods

### **2. STATE MACHINES ARE DECLARATIVE**
- You declare states and the builder creates the machine
- You do NOT manually create transitions
- You do NOT manually create review states
- The builder handles ALL of this

### **3. REVIEW PATTERNS ARE SACRED**
```
Every review cycle follows this EXACT pattern:
1. work_state → work_state_awaiting_ai_review
2. ai_review → work_state_awaiting_human_review
3. human_review → next_work_state
Plus revision paths back to work_state
```
This pattern is FROZEN. Do not modify it.

### **4. TWO PATTERNS ONLY**

**Pattern 1: Multi-step with reviews** (PlanTaskTool)
```python
workflow_builder.build_workflow_with_reviews(
    work_states=[state1, state2, state3],
    terminal_state=StateEnum.VERIFIED,
    initial_state=state1
)
```

**Pattern 2: Simple dispatch-work-done** (Most tools)
```python
workflow_builder.build_simple_workflow(
    dispatch_state=StateEnum.DISPATCHING,
    work_state=StateEnum.WORKING,
    terminal_state=StateEnum.VERIFIED
)
```

THERE ARE NO OTHER PATTERNS.

### **5. STATE NAMING IS AUTOMATIC**
- Work states: As defined in your enum
- AI review: `{work_state}_awaiting_ai_review`
- Human review: `{work_state}_awaiting_human_review`
- The builder creates these names. You do NOT.

### **6. NO CUSTOM TRANSITIONS**
- The builder creates ALL transitions
- You do NOT add custom transitions
- You do NOT modify transition logic
- If you think you need a custom transition, redesign your states

## **WHEN CREATING A NEW WORKFLOW TOOL**

### **DO:**
- ✅ Define your state enum
- ✅ Choose Pattern 1 or Pattern 2
- ✅ Call the appropriate builder method
- ✅ Define your artifact_map
- ✅ Trust the builder completely

### **DON'T:**
- ❌ Create transitions manually
- ❌ Add custom state machine logic
- ❌ Modify the builder
- ❌ Create "special" patterns
- ❌ Think your workflow is unique

## **CHOOSING YOUR PATTERN**

### **Use Pattern 1 when:**
- Multiple sequential work states
- Each state needs review
- Example: plan_task (contextualize → strategize → design → subtasks)

### **Use Pattern 2 when:**
- Single work state
- Dispatch → Work → Done
- Example: implement_task, review_task, test_task

### **"But my workflow is different!"**
No, it's not. Pick Pattern 1 or Pattern 2.

## **STATE MACHINE EXAMPLES**

### **GOOD Example - Using the builder:**
```python
class MyWorkflowTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, "my_tool")
        
        # Just use the builder
        config = workflow_builder.build_simple_workflow(
            dispatch_state=MyState.DISPATCHING,
            work_state=MyState.WORKING,
            terminal_state=MyState.VERIFIED
        )
        
        self.machine = Machine(
            model=self,
            **config,
            auto_transitions=False
        )
```

### **BAD Example - Manual construction:**
```python
# NEVER DO THIS
states = ["dispatching", "working", "working_awaiting_ai_review", ...]
transitions = [
    {"trigger": "dispatch", "source": "dispatching", ...},
    # NO! Use the builder!
]
```

## **TESTING STATE MACHINES**

Test ONLY the outcomes, not the implementation:

```python
def test_state_machine():
    tool = MyWorkflowTool("test-1")
    
    # Test the behavior, not the structure
    assert tool.state == "initial_state"
    tool.submit_work()  # or whatever trigger
    assert tool.state == "expected_next_state"
```

## **THE STATE MACHINE PLEDGE**

*"I will not create custom state machines. I will not add special transitions. The builder provides all I need. When I think my workflow is special, I will remember: It is not. It fits Pattern 1 or Pattern 2. Complexity is the path to madness. The builder is the way."*

## **ENFORCEMENT**

Any PR that:
- Adds a new handler class → REJECTED
- Modifies GenericWorkflowHandler → REJECTED  
- Adds custom state machine logic → REJECTED
- Creates transitions manually → REJECTED
- Adds "special case" handling → REJECTED

The patterns are complete. Trust them.