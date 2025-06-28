#### **Task Directive: ALFRED-10 - Implement the Planning Persona**

**Objective:** To create the `planning` persona, replicating the three-stage, human-gated workflow from ETM. This persona will be responsible for generating the machine-readable `execution_plan.json` that the `developer` persona consumes.

**1. Create `planning.yml`:**
   *   Define a new persona file: `src/alfred/personas/planning.yml`.
   *   Its `target_status` should likely be `ready_for_planning` and its `completion_status` should be `ready_for_setup`.
   *   Its HSM must define the three-stage workflow: `strategy_working` -> `strategy_devreview` -> `solution_design_working` -> `solution_design_devreview` -> `execution_plan_working` -> `execution_plan_devreview` -> `planning_verified`.

**2. Update `workflow.yml`:**
   *   Insert `planning` as the first step in the sequence, before `git_setup`.

**3. Port Artifacts and Prompts:**
   *   Create the Pydantic models for `StrategyArtifact`, `SolutionDesignArtifact`, and `ExecutionPlanArtifact` in `src/alfred/models/artifacts.py`.
   *   Create the corresponding artifact templates (`strategy.md`, `solution_design.md`, `execution_plan.md`) in `src/alfred/templates/artifacts/`.
   *   Port the prompts for each of the three planning sub-stages into `src/alfred/templates/prompts/planning/`.

**4. Implement Append-to-Scratchpad Logic:**
   *   The `planning` phase in ETM used an append-only scratchpad. You will need to enhance the `ArtifactManager` and `Orchestrator` to support this. The output of each planning sub-stage should be appended to a `scratchpad.md` in the task's workspace.

**5. Implement Final Artifact Generation:**
   *   During the final handoff from the `planning` persona, the orchestrator must perform two actions:
      a.  Archive the complete `scratchpad.md`.
      b.  Parse the final `ExecutionPlanArtifact` from the runtime and save it as `execution_plan.json` in the task's archive directory. This is the file the `ArtifactManager.read_execution_plan` method will look for.

**Validation:**
*   When this task is complete, the stubbed logic in `ArtifactManager` will be removed. A task will flow through the new `planning` persona, generating a real `execution_plan.json`. This plan will then be consumed by the `developer` persona, completing the entire ETM logic loop within the new Alfred architecture.

The foundation is laid. Now, we give the system its intelligence. Execute.
