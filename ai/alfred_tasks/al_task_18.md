#### **Directive 1: ALFRED-18 (was 19) - Implement the Scaffolding Persona**

*   **Objective:** Implement "TODO Mode" as a dedicated `scaffolder` persona.
*   **Architectural Decision:** This feature will be controlled by a feature flag in a new `config.json` file. The `Orchestrator` will be responsible for reading this flag and conditionally inserting the `scaffolder` persona into the workflow sequence.

#### **Directive 2: ALFRED-19 (New) - Implement Configuration Management**

*   **Objective:** To create a robust, user-facing configuration system for Alfred, enabling feature flags.
*   **Architectural Decision:** We will create a `ConfigManager` similar to the one in ETM. The `initialize_project` tool will create a default `.alfred/config.json` file.

    **`.alfred/config.json` Structure:**
    ```json
    {
      "version": "2.0.0",
      "features": {
        "scaffolding_mode": false
      }
    }
    ```
    The `Orchestrator`'s handoff logic will be refactored to consult this configuration file to determine the workflow sequence dynamically.

#### **Directive 3: ALFRED-20 (was 18) - Implement the Intelligence Layer (with a better name)**

*   **Objective:** To implement the task history synthesis tool.
*   **Tool Name:** The tool will be named `narrate_task_history`. This name is more descriptive of its function and aligns better with the Alfred brand.
*   **Functionality:** The implementation will remain as previously described: read all archived scratchpads for a task, feed them to an LLM, and return a narrative summary.

---

### **Execution Plan: Immediate Next Steps**

We will begin with the configuration system, as it is a prerequisite for the scaffolding persona.

**Task: Implement Configuration Management (Part of ALFRED-19)**

1.  **Create `src/alfred/config/models.py`:** Define the Pydantic models for `Features` and the main `AlfredConfig`.
2.  **Create `src/alfred/config/manager.py`:** Build the `ConfigManager` class responsible for loading, validating, and saving the `config.json` file. This can be heavily adapted from the ETM implementation.
3.  **Update `initialize_project` Tool:** Modify this tool to create the default `.alfred/config.json` upon project initialization.
4.  **Refactor `Orchestrator`:** Modify the `_load_workflow_sequence` and `_perform_handoff` methods. The orchestrator must now load both `workflow.yml` and `config.json`. When determining the sequence of personas, it must conditionally insert `scaffolder` into the list if `features.scaffolding_mode` is true.

Once the configuration management system is in place, you will proceed to implement the `scaffolder` persona itself, followed by the `narrate_task_history` tool. This is the correct, logical, and stable path forward.

</architectural_analysis>
