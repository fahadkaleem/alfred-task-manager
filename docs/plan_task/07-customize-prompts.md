### **AI Self-Review Prompts for `plan_task`**

#### **1. Context Review**

*   **Triggered After:** The `contextualize` state, where the AI has performed its initial analysis of the task and codebase.
*   **Prompt File to Create/Modify:**
    *   `src/alfred_new/templates/prompts/plan_task/review_context.md`
*   **Core Directive for the AI:**
    *   "Review the `ContextAnalysisArtifact` you just created. Have you thoroughly analyzed all relevant files? Are your `questions_for_developer` specific, insightful, and sufficient to unblock all ambiguities? Is your `context_summary` a fair and accurate representation? You must confirm this before I present your questions to the human."
*   **Purpose of this Gate:** To prevent the AI from starting a conversational loop with the human based on a shallow or incomplete initial analysis. It forces the AI to double-check its own homework first.

#### **2. Strategy Review**

*   **Triggered After:** The `strategize` state, where the AI has created the high-level technical strategy.
*   **Prompt File to Create/Modify:**
    *   `src/alfred_new/templates/prompts/plan_task/review_strategy.md`
*   **Core Directive for the AI:**
    *   "Review the `StrategyArtifact`. Does the `high_level_strategy` directly address all points from the initial task and the developer's clarifications? Is it technically sound and feasible? Have all key components and risks been identified? You must ensure this strategy is robust before it is presented for human approval."
*   **Purpose of this Gate:** To catch flawed or incomplete strategic thinking early. It's cheaper to fix a bad strategy now than after a detailed design has been based on it.

#### **3. Design Review**

*   **Triggered After:** The `design` state, where the AI has created the detailed file-by-file breakdown.
*   **Prompt File to Create/Modify:**
    *   `src/alfred_new/templates/prompts/plan_task/review_design.md`
*   **Core Directive for the AI:**
    *   "Review the `DesignArtifact`. Does the `file_breakdown` fully and accurately implement every `key_component` from the approved strategy? Is the `change_summary` for each file clear and specific? Are there any logical gaps or missing files? You must verify that this design is a complete and faithful translation of the strategy."
*   **Purpose of this Gate:** To ensure the detailed design doesn't deviate from the approved high-level strategy and is complete enough for the final SLOT generation.

#### **4. Final Plan Review**

*   **Triggered After:** The `generate_slots` state, where the AI has created the final `ExecutionPlan` artifact (the list of `Subtask`s).
*   **Prompt File to Create/Modify:**
    *   `src/alfred_new/templates/prompts/plan_task/review_plan.md`
*   **Core Directive for the AI:**
    *   "This is the final quality gate. Review the entire `ExecutionPlanArtifact`. Is every `acceptance_criterion` from the original `Task` fully covered by one or more `Subtask`s? Is the plan holistic and complete? Is the sequence of `Subtask`s logical? Have you embedded the `mark_subtask_complete` directive in every `Subtask`? You must sign off on this as a production-ready plan."
*   **Purpose of this Gate:** The final, holistic check to ensure the generated plan is not just technically sound but also functionally complete and ready for execution.

---
### **Workflow Summary**

To be explicit, your workflow for this task will be:

1.  Focus on **`review_context.md`**.
2.  Then, **`review_strategy.md`**.
3.  Then, **`review_design.md`**.
4.  Finally, **`review_plan.md`**.

Each of these four prompts represents a critical quality gate. By engineering them to be rigorous and demanding, you are building the automated quality assurance system directly into the core of Alfred's planning process.