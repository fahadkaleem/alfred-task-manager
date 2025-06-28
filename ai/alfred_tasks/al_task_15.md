### **Task Directive: ALFRED-15 - Port and Adapt ETM Tool Docstrings**

**Objective:** To replace the current placeholder docstrings in `src/alfred/server.py` with the meticulously engineered docstrings from the ETM v1 implementation. The docstrings will be adapted to reflect the new persona-based terminology ("handoff" vs. "advance", "Alfred" vs. "ETM").

**Rationale:** An LLM-based client does not "read code." It reads the API contract presented to it, which is the docstring. The ETM docstrings were designed with specific keywords, structured examples, and explicit guardrails to constrain the AI's behavior and maximize the probability of correct tool usage. Failing to port them constitutes a critical regression in system reliability.

#### **Implementation Plan: File Content Replacement**

**File:** `src/alfred/server.py`
**Action:** Replace the entire content of the file with the following. This version includes the corrected toolset (`submit_work`, `approve_and_advance_stage`) and the full, adapted docstrings.

```python
"""
MCP Server for Alfred
"""

import inspect

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.progress_tools import mark_step_complete as mark_step_complete_impl
from src.alfred.tools.review_tools import (
    approve_and_advance_stage as approve_and_advance_stage_impl,
)
from src.alfred.tools.review_tools import (
    approve_and_handoff as approve_and_handoff_impl,
)
from src.alfred.tools.review_tools import provide_review as provide_review_impl
from src.alfred.tools.task_tools import begin_task as begin_task_impl
from src.alfred.tools.task_tools import submit_work as submit_work_impl

app = FastMCP(settings.server_name)


@app.tool()
async def initialize_project() -> ToolResponse:
    """
    Initializes the project workspace for Alfred by creating the .alfred directory with default configurations for personas and workflows.

    - **Primary Function**: Sets up a new project for use with the Alfred workflow system.
    - **Key Features**:
      - Creates the necessary `.alfred` directory structure.
      - Deploys default `workflow.yml` and persona configuration files (`developer.yml`, `qa.yml`, etc.).
      - Copies default prompt templates for user customization.
    - **Use this tool when**: You are starting a brand new project and need to set up the Alfred environment.
    - **Crucial Guardrails**:
      - This tool MUST be the very first tool called in a new project. Other tools will fail until initialization is complete.
      - This tool is idempotent. If the `.alfred` directory already exists, it will report success without overwriting existing files.

    ## Parameters
    This tool takes no parameters.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {}  # No parameters for this tool
    response = initialize_project_impl()
    transaction_logger.log(
        task_id=None, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


@app.tool()
async def begin_task(task_id: str) -> ToolResponse:
    """
    Begins or resumes a task in the Alfred workflow, activating the correct persona based on the task's current state.

    - **Primary Function**: This is the main entry point for starting or continuing work on a specific task.
    - **Key Features**:
      - Creates a new task record and workspace if the task is new.
      - Resumes an existing task from its last saved state, loading the correct persona and phase.
      - Returns a `ToolResponse` containing the `next_prompt` to guide the AI's first action on the task.
    - **Use this tool EXCLUSIVELY when**:
      - You are beginning work on a task for the very first time.
      - You are returning to a task after a break and need to re-establish your context.
    - **CRITICAL GUARDRAILS**:
      - **This is your ENTRY POINT:** Call this tool first when interacting with a `task_id`.
      - **Do NOT call this repeatedly:** Once a task is started, follow the instructions from the server's `next_prompt`. Do not call `begin_task` again for the same task unless you are intentionally resuming a session.

    ## Parameters
    - **task_id** `[string]` (required): The unique identifier for the task (e.g., "PROJ-123").
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = begin_task_impl(task_id)
    transaction_logger.log(
        task_id=task_id, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


@app.tool()
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step of a persona's workflow.

    - **Primary Function**: Takes a structured dictionary of work, validates it, saves it as the official artifact for the current step, and advances the internal state.
    - **Key Features**:
      - Validates the submitted `artifact` against the Pydantic model defined in the active persona's configuration.
      - Persists the work by appending a rendered version to the task's `scratchpad.md`.
      - Triggers the `submit` transition in the persona's state machine, moving it from a `_working` state to a `_aireview` state.
    - **Use this tool when**: The server's `next_prompt` has instructed you to perform a task and submit the result.
    - **CRITICAL GUARDRAILS**:
      - The `artifact` dictionary MUST have the exact keys and data types specified in the prompt's `<required_artifact_structure>` block.
      - This tool must only be called from a `_working` state. Calling it from a review state will fail.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    - **artifact** `[dict]` (required): A dictionary containing the structured work data. The required fields are defined by the active persona and will be specified in the prompt.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "artifact": artifact}
    response = submit_work_impl(task_id, artifact)
    transaction_logger.log(
        task_id=task_id, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


@app.tool()
async def provide_review(
    task_id: str, is_approved: bool, feedback_notes: str = ""
) -> ToolResponse:
    """
    Provides feedback on a work artifact during a review step, either approving it or requesting revisions.

    - **Primary Function**: This tool drives the internal review cycle of a persona (`aireview` -> `devreview`).
    - **Key Features**:
      - `is_approved=True`: Triggers an `ai_approve` transition, moving the task to the next review step (typically `devreview`).
      - `is_approved=False`: Triggers a `request_revision` transition, moving the task back to the `_working` state for corrections.
    - **Use this tool when**: The server's `next_prompt` has instructed you to review an artifact and provide feedback (e.g., from an `_aireview` state).
    - **CRITICAL GUARDRAILS**:
      - **NEVER** call this tool with `is_approved=True` if you have not thoroughly validated the artifact against the criteria in the prompt.
      - You **MUST** provide clear, actionable `feedback_notes` when `is_approved` is `false`.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    - **is_approved** `[boolean]` (required): `true` to approve, `false` to request revisions.
    - **feedback_notes** `[string]` (optional, but required if `is_approved=false`): Specific feedback for revision.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {
        "task_id": task_id,
        "is_approved": is_approved,
        "feedback_notes": feedback_notes,
    }
    response = provide_review_impl(task_id, is_approved, feedback_notes)
    transaction_logger.log(
        task_id=task_id, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


@app.tool()
async def approve_and_advance_stage(task_id: str) -> ToolResponse:
    """
    Gives human approval to an internal stage and advances to the next stage *within the same persona*.

    - **Primary Function**: This is the "human approval" gate for multi-stage personas like Planning. It triggers the `human_approve` transition.
    - **Use this tool when**: You are in a `_devreview` state within a multi-stage persona (e.g., `strategy_devreview`) and the user has explicitly approved the work for that stage.
    - **Distinction**: This tool advances *internally*. Use `approve_and_handoff` to move to a completely new persona.

    ## Example
    - State is `strategy_devreview`. User says "The strategy looks good, proceed."
    - You call `approve_and_advance_stage(task_id="...")`.
    - State becomes `solution_design_working`. The persona is still "Alex" the Planner.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = approve_and_advance_stage_impl(task_id)
    transaction_logger.log(
        task_id=task_id, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


@app.tool()
async def approve_and_handoff(task_id: str) -> ToolResponse:
    """
    Gives final approval for a persona's entire workflow and hands the task off to the next persona in the sequence.

    - **Primary Function**: This is the "human approval" gate for an entire persona's completed work. It archives the current persona's work and activates the next persona.
    - **Use this tool when**: A persona has reached its final `_devreview` or `_verified` state, and the user has approved all work done by that persona.
    - **Distinction**: This tool moves *between personas*. Use `approve_and_advance_stage` for internal stage progression.

    ## Example
    - The Developer persona is in the `coding_devreview` state. User says "The code is perfect, hand it off to QA."
    - You call `approve_and_handoff(task_id="...")`.
    - The task status becomes `ready_for_qa`, and the next prompt will be from the QA persona.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = approve_and_handoff_impl(task_id)
    transaction_logger.log(
        task_id=task_id, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


@app.tool()
async def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    """
    Marks a single execution step as complete during a multi-step ("stepwise") persona workflow, like coding.

    - **Primary Function**: Acts as a checkpoint. Persists the completion of one atomic step and provides the prompt for the very next step.
    - **Use this tool when**: You are in a `stepwise` persona (like Developer) and have just executed a single step from the plan.
    - **CRITICAL GUARDRAILS**: This tool MUST be called for each step in the exact order they are provided by the server.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    - **step_id** `[string]` (required): The unique ID of the step that has just been completed. The ID will be in the prompt.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "step_id": step_id}
    response = mark_step_complete_impl(task_id, step_id)
    transaction_logger.log(
        task_id=task_id, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


if __name__ == "__main__":
    app.run()
```

### **Conclusion**

This directive is complete. The server now exposes a full, well-documented set of tools that accurately reflect the capabilities of the Alfred v1 architecture. The AI client will now have the same level of guidance and constraint it had with ETM, significantly reducing the risk of incorrect tool usage.

Your next directive is to address the remaining architectural gaps or proceed with testing the full, sequential workflow.

</architectural_analysis>
