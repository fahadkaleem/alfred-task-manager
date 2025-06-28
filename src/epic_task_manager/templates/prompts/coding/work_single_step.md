# Role: Software Developer

Execute the following atomic step ({step_number} of {total_steps}) for task `{task_id}`.

---
### **Step ID: `{step_id}`**
---

### **Instruction:**
```
{step_instruction}
```
---

### **Implementation Guidance**

**Hint:** A detailed `TODO` comment corresponding to this step may exist in the target file(s). Your task is to implement the instruction above. After your implementation is complete, you **MUST delete the entire `TODO` comment block** for this step to clean the codebase.

## Required Action

Upon successful completion of this single step, you **MUST** immediately call the `mark_step_complete` tool with the exact `step_id` from this prompt to receive your next instruction.

**Tool Call:**
`mcp_epic-task-manager_mark_step_complete(task_id="{task_id}", step_id="{step_id}")`
