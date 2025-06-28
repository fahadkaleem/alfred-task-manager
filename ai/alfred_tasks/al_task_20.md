### **Task Directive: ALFRED-20 - Implement the Scaffolding Persona**

**Objective:** To introduce an optional `scaffolder` persona into the workflow. This persona will read the `execution_plan.json` and automatically populate the target files with structured `// TODO: ...` comments, providing a clear roadmap for the developer.

**Rationale:** This feature bridges the gap between planning and coding. It reduces the cognitive load on the developer by transcribing the abstract plan directly into the codebase, turning the implementation phase into a "fill-in-the-blanks" exercise.

#### **1. Implement Configuration Control**

This feature must be controllable via `config.json`.

**File:** `src/alfred/models/alfred_config.py`
**Action:** Add the `scaffolding_mode` feature flag.

```python
# In FeaturesConfig class...
class FeaturesConfig(BaseModel):
    scaffolding_mode: bool = Field(
        default=False,
        description="Enable scaffolding mode to generate TODO placeholders before implementation"
    )
```

**File:** `src/alfred/orchestration/orchestrator.py`
**Action:** Modify `_load_workflow_sequence` to conditionally insert the `scaffolder` persona.

```python
# In Orchestrator class...
    def _load_workflow_sequence(self):
        # ... load base_sequence from workflow.yml ...

        try:
            config = self.config_manager.load()
        except FileNotFoundError:
            self.workflow_sequence = base_sequence
            return

        self.workflow_sequence = base_sequence.copy()

        # --- NEW: Conditionally add scaffolder ---
        if config.features.scaffolding_mode and "scaffolder" not in self.workflow_sequence:
            try:
                # Insert after planning, before developer
                planning_idx = self.workflow_sequence.index("planning")
                self.workflow_sequence.insert(planning_idx + 1, "scaffolder")
                logger.info("Scaffolding mode enabled - inserted scaffolder persona into workflow")
            except ValueError:
                logger.warning("Could not find 'planning' persona to insert scaffolder after.")
        # --- END NEW ---
```

#### **2. Define the `scaffolder` Persona**

Create the persona definition file.

**File:** `src/alfred/personas/scaffolder.yml` (NEW FILE)
**Action:** Create this new file with the following content.

```yaml
name: "Scaffy"
title: "Code Scaffolder"
target_status: "ready_for_scaffolding"
completion_status: "ready_for_dev"
execution_mode: "stepwise" # It will process the plan step-by-step

hsm:
  initial_state: "scaffolding_working"
  states:
    - "scaffolding_working"
    - "scaffolding_submission"
    - "scaffolding_aireview"
    - "scaffolding_devreview"
    - "scaffolding_verified"
  transitions:
    - { trigger: "submit_manifest", source: "scaffolding_submission", dest: "scaffolding_aireview" }
    - { trigger: "ai_approve", source: "scaffolding_aireview", dest: "scaffolding_devreview" }
    - { trigger: "human_approve", source: "scaffolding_devreview", dest: "scaffolding_verified" }
    - { trigger: "request_revision", source: ["scaffolding_aireview", "scaffolding_devreview"], dest: "scaffolding_working" }

prompts:
  scaffolding_working: "prompts/scaffolder/work_step.md"
  scaffolding_submission: "prompts/scaffolder/submission.md"
  scaffolding_aireview: "prompts/scaffolder/ai_review.md"
  scaffolding_devreview: "prompts/scaffolder/dev_review.md"

artifacts:
  - state: "scaffolding_submission"
    model_path: "src.alfred.models.artifacts.ScaffoldingManifest" # You will need to create this model

core_principles:
  - "My sole purpose is to transcribe the execution plan into TODO comments in the codebase."
  - "I do not write implementation code. I only prepare the way for the developer."
  - "I will process one step of the plan at a time."
```

#### **3. Create Supporting Models and Prompts**

*   **Create the Artifact Model:** In `src/alfred/models/artifacts.py`, create a `ScaffoldingManifest(BaseModel)` with a field like `files_scaffolded: list[str]`.
*   **Create the Prompts:** Create the new directory `src/alfred/templates/prompts/scaffolder/` and populate it with the prompts defined in the YAML (`work_step.md`, `submission.md`, etc.). The `work_step.md` prompt will instruct the AI to read a single step from the plan and insert a formatted `TODO` comment into the target file(s).

### **Conclusion**

Executing this directive will add a significant, user-valuable feature to the platform. More importantly, it will serve as the first validation of our new persona-based architecture's primary design goal: **extensibility**. If we can add this complex new phase to the workflow purely through configuration and the addition of a self-contained module, then the architecture is a success.

This is the next logical step in the evolution of Alfred. Proceed.

</architectural_analysis>
