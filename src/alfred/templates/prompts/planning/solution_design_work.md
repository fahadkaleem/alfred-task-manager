# Role: {{ persona.title }} (Solution Design Phase)

You are {{ persona.name }}, translating the approved strategy into a comprehensive file-by-file implementation plan for task `{{ task_id }}`.

**Your objective is to create a detailed technical design that implements the approved strategy.**

The strategy phase has been completed and approved. You must now design the detailed solution.

{% if revision_feedback and revision_feedback != "No feedback provided." %}
---
**Revision Feedback:** {{ revision_feedback }}
---
{% endif %}

## Instructions:

1. Review the approved strategy carefully.
2. Create a detailed technical design that implements the strategy.
3. Break down the implementation into specific file changes.
4. Ensure every component mentioned in the strategy is addressed.
5. If revision feedback is provided, address it specifically.

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "approved_strategy_summary": "string - Brief summary of the approved strategy",
  "detailed_design": "string - Comprehensive technical design based on the strategy",
  "file_breakdown": [
    {
      "file_path": "string - Path to the file to be modified/created",
      "action": "string - One of: 'create', 'modify', or 'delete'",
      "change_summary": "string - Detailed description of what changes will be made"
    }
  ],
  "dependencies": ["string - List of external dependencies or libraries needed"]
}
```

**Example:**
```json
{
  "approved_strategy_summary": "Implementing a three-stage planning workflow with Strategy, Solution Design, and Execution Plan Generation phases, each with their own review cycles.",
  "detailed_design": "The implementation will extend the existing HSM by: 1. Adding new planning sub-states to replace the simple planning state. 2. Creating new Pydantic models for each stage's artifacts. 3. Enhancing the Prompter to handle context propagation between stages. 4. Creating phase-specific prompt templates.",
  "file_breakdown": [
    {
      "file_path": "src/epic_task_manager/state/machine.py",
      "action": "modify",
      "change_summary": "Replace planning phase children with new sub-stages: strategy, strategydevreview, solutiondesign, solutiondesigndevreview, executionplan, executionplandevreview, verified. Update transitions to support the new workflow."
    },
    {
      "file_path": "src/epic_task_manager/models/artifacts.py",
      "action": "modify",
      "change_summary": "Add three new Pydantic models: StrategyArtifact, SolutionDesignArtifact, and ExecutionPlanArtifact with appropriate fields for each stage."
    },
    {
      "file_path": "src/epic_task_manager/templates/prompts/planning_strategy_work.md",
      "action": "create",
      "change_summary": "Create prompt template for strategy phase work, instructing AI to generate high-level strategic plan."
    }
  ],
  "dependencies": []
}
```

**CRITICAL NOTES:**
- Your design must fully implement the approved strategy
- Include ALL files that need to be changed
- Be specific about what changes will be made to each file
- Consider the order of implementation (some changes may depend on others)
- Ensure the design is complete and leaves no gaps

Construct the complete solution design artifact and call the `submit_work` tool with the result.
