# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: generate_slots

The detailed implementation design has been approved. Your final task is to convert this design into a machine-executable `ExecutionPlan` composed of `SLOT`s.

**Approved Design:**
```json
{{ additional_context.design_artifact | tojson(indent=2) }}
```

---
### **Directive: Generate SLOTs**

Mechanically translate each item in the `file_breakdown` into one or more `SLOT` objects.

For each `SLOT`, you must define:
- `slot_id`: A unique, sequential ID (e.g., "slot-1", "slot-2").
- `title`: A concise title.
- `spec`: A detailed specification, derived from the `change_summary`.
- `location`: The `file_path`.
- `operation`: The `operation`.
- `taskflow`: A detailed `procedural_steps` and `verification_steps` (unit tests) for this specific SLOT.

**CRITICAL: Use `delegation` for complex SLOTs.** If a SLOT's `spec` involves complex logic, security considerations, or significant architectural work, you MUST add a `delegation` field to it. The `delegation` spec should instruct a specialist sub-agent on how to approach the task.

---
### **Required Action**

You MUST now call `alfred.submit_work` with the final `ExecutionPlanArtifact` (the list of `SLOT`s).

**Required Artifact Structure:** `List[SLOT]`