# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_plan

The complete `ExecutionPlan` has been generated. I will now perform a final holistic review before presenting it for human sign-off.

---
### **Directive: Final Plan Review**

Review the generated `list[Subtask]` against the original `Task` context.

**Review Checklist:**
1. **Coverage:** Is every `acceptance_criterion` from the original task fully addressed by the combination of all Subtasks?
2. **Completeness:** Is the plan comprehensive? Are there any missing steps or logical gaps between Subtasks?
3. **Traceability:** Does the plan clearly and logically derive from the approved `strategy` and `design`?
4. **Delegation:** Have complex tasks been appropriately marked with a `delegation` spec?

---
### **Required Action**

If the `ExecutionPlan` is complete and correct, call `alfred.provide_review` with `is_approved=True` to send it for final human approval.

If the plan is flawed, call `provide_review` with `is_approved=False` and detailed `feedback_notes` explaining the required changes.