<file_map>
/Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager
├── config
│   ├── __init__.py
│   ├── config_manager.py
│   └── settings.py
├── execution
│   ├── __init__.py
│   ├── artifact_behavior.py
│   ├── artifact_manager.py
│   ├── constants.py
│   ├── exceptions.py
│   └── prompter.py
├── models
│   ├── __init__.py
│   ├── artifacts.py
│   ├── config.py
│   ├── core.py
│   ├── enums.py
│   └── schemas.py
├── prompts
│   ├── __init__.py
│   └── implement_next_task.py
├── resources
│   ├── __init__.py
│   └── workflow_docs.py
├── state
│   ├── __init__.py
│   ├── machine.py
│   └── manager.py
├── task_sources
│   ├── jira
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   └── sync.py
│   ├── local
│   │   ├── __init__.py
│   │   └── provider.py
│   ├── __init__.py
│   ├── base.py
│   └── constants.py
├── templates
│   ├── artifacts
│   │   ├── coding_artifact.md
│   │   ├── finalize_artifact.md
│   │   ├── gatherrequirements_artifact.md
│   │   ├── git_setup_artifact.md
│   │   ├── planning_execution_plan_artifact.md
│   │   ├── planning_solution_design_artifact.md
│   │   ├── planning_strategy_artifact.md
│   │   ├── scaffolding_artifact.md
│   │   └── testing_artifact.md
│   ├── guidelines
│   │   ├── coding_guidelines.md
│   │   ├── formatting_guidelines.md
│   │   ├── git_guidelines.md
│   │   └── testing_guidelines.md
│   ├── prompts
│   │   ├── client
│   │   │   └── implement_next_task.md
│   │   ├── coding
│   │   │   ├── ai_review.md
│   │   │   └── work_single_step.md
│   │   ├── finalize
│   │   │   ├── ai_review.md
│   │   │   └── work.md
│   │   ├── gatherrequirements
│   │   │   ├── atlassian_work.md
│   │   │   ├── generic_work.md
│   │   │   ├── linear_work.md
│   │   │   └── local_work.md
│   │   ├── gitsetup
│   │   │   ├── ai_review.md
│   │   │   └── work.md
│   │   ├── planning
│   │   │   ├── execution_plan_work.md
│   │   │   ├── solution_design_work.md
│   │   │   └── strategy_work.md
│   │   ├── scaffolding
│   │   │   ├── ai_review.md
│   │   │   └── work.md
│   │   ├── testing
│   │   │   ├── ai_review.md
│   │   │   └── work.md
│   │   └── utils
│   │       ├── clean_slate.md
│   │       ├── formatting_section.md
│   │       └── yolo_auto_approve.md
│   ├── responses
│   │   ├── generic_error.md
│   │   └── invalid_state_error.md
│   └── __init__.py
├── tools
│   ├── __init__.py
│   ├── get_active_task.py
│   ├── get_task_summary.py
│   ├── initialize.py
│   ├── inspect_archived_artifact.py
│   ├── management_tools.py
│   ├── progress_tools.py
│   ├── review_tools.py
│   └── task_tools.py
├── utils
│   ├── __init__.py
│   └── hello_world.py
├── __init__.py
├── constants.py
├── exceptions.py
├── server.py
└── validation_etm14.py

</file_map>

<file_contents>
File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/server.py
```python
"""
MCP Server for Epic Task Manager using FastMCP 2.0
"""

from fastmcp import FastMCP

from .config.settings import settings
from .models.schemas import ToolResponse
from .prompts.implement_next_task import implement_next_task
from .tools import initialize, management_tools, progress_tools, review_tools, task_tools
from .tools.get_active_task import get_active_task as get_active_task_impl
from .tools.get_task_summary import get_task_summary as get_summary_impl
from .tools.inspect_archived_artifact import (
    inspect_archived_artifact as inspect_archived_artifact_impl,
)

# Create FastMCP 2.0 server instance
app = FastMCP(settings.server_name)


@app.tool()
async def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initializes the project workspace and configures the definitive source for tasks (Jira, Linear, or Local) by creating the .epictaskmanager directory with provider-specific configuration.

    - **Primary Function**: Initializes the project workspace and configures the definitive source for tasks (Jira, Linear, or Local)
    - **Key Features**:
      - Interactive provider selection when no provider is specified
      - Automatic MCP server connectivity validation for Jira and Linear providers
      - Safe initialization that won't overwrite existing configurations
      - Creates necessary directory structure and configuration files
    - **Use this tool when**: You need to initialize a new Epic Task Manager project or set up task source integration
    - **Crucial Guardrails**:
      - This tool MUST be the very first tool called in a new project. Other tools like begin_or_resume_task will fail until initialization is complete
      - Do NOT use this tool if the project is already initialized (it will return success but make no changes)
      - For Jira/Linear providers, ensure the respective MCP servers are running before initialization

    ## Usage

    **Before using this tool:**
    - Ensure you're in the correct project directory where you want to initialize Epic Task Manager
    - For Jira provider: Verify the Atlassian MCP server is running and accessible
    - For Linear provider: Verify the Linear MCP server is running and accessible

    **IMPORTANT**: This tool creates a `.epictaskmanager` directory in the current workspace. If this directory already exists with a valid configuration, the tool will return success without making changes.

    **Setup Approaches:**

    **Interactive Setup**: To guide the user through setup, call the tool first with no parameters. The server will return a `ToolResponse` with a status of `choices_needed` and the available providers in the `data` field. Then, call the tool a second time with the user's chosen provider (e.g., `initialize_project(provider='jira')`).

    **Direct Setup**: If the provider is already known, you can skip the interactive step by calling the tool directly with the provider parameter from the start.

    **Provider-Specific Behavior:**
    - **Jira**: Validates MCP server connectivity and creates MCP-based configuration
    - **Linear**: Validates MCP server connectivity and creates MCP-based configuration
    - **Local**: Creates a tasks inbox directory with README and example task format

    **WARNING**: For Jira and Linear providers, if MCP server validation fails, the tool will return an error with installation instructions. You must resolve MCP connectivity before successful initialization.

    **CRITICAL REQUIREMENTS:**
    1. This tool MUST be called before any other Epic Task Manager tools
    2. MCP servers MUST be running and accessible before selecting Jira or Linear providers
    3. The workspace directory must have write permissions for directory creation

    ## Examples

    <example>
    User: "Let's get this project set up with the Epic Task Manager."
    Assistant:
    Initial discovery call to get options.
    ```
    mcp_epic-task-manager_initialize_project()
    ```
    Assistant receives a response listing 'jira', 'linear', and 'local' as options.
    "I've checked the available task sources. We can connect to Jira, Linear, or use a local directory of markdown files. Which would you prefer?"
    User: "Let's use Jira."
    Assistant:
    Final initialization call with the chosen provider.
    ```
    mcp_epic-task-manager_initialize_project(provider="jira")
    ```
    </example>

    <reasoning>
    1. The assistant correctly performed a discovery call first by omitting the provider parameter. This is the standard interactive pattern.
    2. It then used the user's selection to make a second, specific call to complete the configuration.
    3. This two-step process ensures the user is always aware of their options and confirms the connection before proceeding.
    </reasoning>

    <example>
    User: "Set up Epic Task Manager with local file support"
    Assistant:
    Direct initialization call since the provider is already specified.
    ```
    mcp_epic-task-manager_initialize_project(provider="local")
    ```
    </example>

    <reasoning>
    1. The assistant skipped the discovery phase since the user explicitly requested local file support
    2. This demonstrates the direct setup approach when the provider choice is already clear
    3. This is more efficient when the user has already made their preference known
    </reasoning>

    ## Parameters

    **provider** [string] (optional) - The task source provider to configure.
    - **Valid values**: `"jira"`, `"linear"`, `"local"` (case-insensitive)
    - **Default behavior**: When this parameter is omitted, the tool enters discovery mode. It will not initialize the project but will instead return a list of available provider choices. This is the first step in the interactive setup flow.
    - **Provider descriptions**:
      - `"jira"`: Connects to Jira via Atlassian MCP server for task management
      - `"linear"`: Connects to Linear MCP server for task management
      - `"local"`: Uses local markdown files in a tasks inbox directory
    - **Common mistakes**: Providing an invalid provider name will result in an error. The tool performs case-insensitive validation but only accepts the three specified values.

    ## Returns
    A `ToolResponse` object. On successful final initialization, the `message` field confirms setup. In interactive mode, the `status` will be `choices_needed` and the `data` field will contain the list of providers.
    """
    return await initialize.initialize_project(provider)


@app.tool()
async def begin_or_resume_task(task_id: str) -> ToolResponse:
    """
    Initializes a new task in the Epic Task Manager workflow or resumes an existing task from its current state.

    **Core Features:**
    - Creates a new task record and workspace structure for first-time tasks
    - Resumes existing tasks from their last saved state without data loss
    - Validates project initialization before proceeding
    - Returns a `ToolResponse` containing the `next_prompt` to guide the AI's first action on the task

    **Use this tool EXCLUSIVELY when:**
    - You are beginning work on a task for the very first time
    - You are returning to a task after a break and need to re-establish your context

    **CRITICAL GUARDRAILS:**
    - **This is your ENTRY POINT:** This tool should be the **first** tool you call when interacting with a specific `task_id`
    - **Do NOT call this repeatedly:** Once you have started a task, you should follow the instructions from the server's `next_prompt`. Do not call `begin_or_resume_task` again for the same task unless you are intentionally resuming a session
    - **Use `get_task_summary` for status checks:** If you only need to know the current phase without changing anything, use `get_task_summary` instead

    ## Usage

    **Before using this tool:**
    - Ensure the Epic Task Manager project is initialized (`.epictaskmanager` directory exists)
    - Have a valid task ID ready (e.g., "IS-1234", "TEST-456")

    **IMPORTANT:** This tool performs different actions based on task existence:
    - **New tasks**: Creates the task record and workspace structure, starting it in the first phase
    - **Existing tasks**: Loads the current state and provides a continuation prompt for the current phase

    **WARNING:** The tool will fail if:
    - Project is not initialized (missing `.epictaskmanager` directory)
    - Task ID format is invalid
    - State files are corrupted or inaccessible

    ## Examples

    <example>
    User: "I want to start working on ticket EP-456"
    Assistant: I'll start the task EP-456 for you using the Epic Task Manager workflow.
    ```
    mcp_epic-task-manager_begin_or_resume_task(task_id="EP-456")
    ```
    The tool creates a new task and returns a `ToolResponse`. The assistant will now execute the `next_prompt` from that response, which will contain instructions for the `gatherrequirements` phase.
    </example>

    <reasoning>
    1. The assistant correctly identified that it needed to start a task workflow.
    2. The tool successfully created the task record and workspace.
    3. The assistant's next action is determined entirely by the `next_prompt` field in the `ToolResponse` it received from the server. This is the correct entry point for the server-driven workflow.
    </reasoning>

    <example>
    User: "Continue working on my current task, TEST-789"
    Assistant: I'll resume work on task TEST-789.
    ```
    mcp_epic-task-manager_begin_or_resume_task(task_id="TEST-789")
    ```
    The tool detects that TEST-789 already exists. It loads its state and returns a `ToolResponse` where the `next_prompt` contains instructions to continue from the last known phase.
    </example>

    <reasoning>
    1. The assistant correctly used `begin_or_resume_task` to resume an existing task.
    2. The tool properly detected the existing task and its current phase.
    3. The response provided a context-appropriate `next_prompt` for continuing work, ensuring a seamless resumption of the workflow.
    </reasoning>

    ## Parameters

    **task_id** [string] (required) - The task identifier.
    - **Format**: Must follow the convention of your task provider (e.g., Jira's PROJECT-NUMBER format, or a local filename).
    - **Validation**: The system validates format and will return an error for invalid formats if applicable.

    ## Returns
    A `ToolResponse` object. The `next_prompt` field will contain the complete, self-contained prompt for the AI's very next action.
    """
    return await task_tools.begin_or_resume_task(task_id)


@app.tool()
async def submit_for_review(task_id: str, work_artifact: dict) -> ToolResponse:
    """
    Submits a completed work artifact for the current phase of a task.

    - **Core Function**: Takes a structured dictionary of work, saves it as the official artifact for the current phase, and advances the internal review process.
    - **Key Features**:
      - Validates project initialization and task existence
      - Uses phase-specific templates to generate a markdown artifact
      - Automatically adds metadata (task_id, phase, status, etc.) to the artifact
    - **Use this tool when**: You have completed the work for a phase as instructed by a server prompt and are ready to submit it.

    ## Usage

    **Before using this tool:**
    1. Ensure the Epic Task Manager project is initialized
    2. Verify the task exists and you are in a working state (the server prompt will have guided you here)
    3. Structure your work data into the `work_artifact` dictionary according to the exact field requirements specified in the server's prompt

    **IMPORTANT:** Each phase has specific required fields in the `work_artifact`. These fields will be explicitly requested in the prompt you receive from the server. You MUST provide a dictionary with the exact keys requested.

    **WARNING:** The tool will fail if:
    - Project is not initialized
    - Task does not exist
    - The tool is called from an invalid state (e.g., a review state)
    - The `work_artifact` is missing required fields for the current phase

    ## Examples

    <example>
    Assistant: (After being prompted to claim task IS-1234 and fetching the details)
    I'll submit the completed claim task work for IS-1234.
    ```
    mcp_epic-task-manager_submit_for_review(
        task_id="IS-1234",
        work_artifact={
            "task_summary": "Implement user authentication",
            "task_description": "Add OAuth2 login functionality...",
            "acceptance_criteria": ["Users can log in with Google"]
        }
    )
    ```
    The tool saves the artifact and returns a `ToolResponse`. The `next_prompt` will contain instructions for the AI to perform a self-review of the artifact it just submitted.
    </example>

    <reasoning>
    1. The assistant correctly followed the server's prompt to perform the claim task work.
    2. It constructed the `work_artifact` with the exact keys required by the server for the `gatherrequirements` phase.
    3. After calling `submit_for_review`, the assistant's next step is dictated by the new `next_prompt` returned by the server.
    </reasoning>

    ## Parameters

    **task_id** [string] (required) - The task ID (e.g., TEST-123, EP-456). Must be an existing task.

    **work_artifact** [dict] (required) - A dictionary containing the structured work data for the current phase. The required fields and their structure will be explicitly defined in the server prompt that instructs you to perform the work. Common mistakes include using incorrect field names, providing strings where arrays are expected, or omitting required fields.

    ## Returns
    A `ToolResponse` object. The `next_prompt` field will contain the instructions for the next step, which is typically to start the review process for the submitted artifact.
    """
    return await task_tools.submit_for_review(task_id, work_artifact)


@app.tool()
async def approve_and_advance(task_id: str) -> ToolResponse:
    """
    Advances a task to the next major phase in the workflow, signifying human approval of the current phase's work.

    - **Core Function**: Marks the current phase as verified, archives its artifact, and transitions the task to the beginning of the next phase.
    - **Primary Use**: This tool acts as the "human approval" gate. It should typically be invoked based on a direct request from the human user.
    - **Crucial Guardrails**:
      - This tool is for moving between major phases (e.g., `planning` to `coding`). It is not used for the internal review steps within a phase.
      - Do not call this tool unless the user has explicitly approved the work of the current phase and instructed you to proceed.

    ## Usage Requirements

    **Before using this tool:**
    1. The current phase's work must be complete and have passed all its internal review steps.
    2. The human user must have given explicit approval to move to the next phase.

    **When this tool executes successfully:**
    1. Marks the current phase as verified.
    2. Archives the completed work artifact for historical reference.
    3. Transitions the task to the working step of the next phase in the sequence.

    **Workflow Progression:**
    This tool moves tasks along the main sequence:
    `gatherrequirements` → `gitsetup` → `planning` → `coding` → `testing` → `finalize` → `done`

    **WARNING**:
    - This tool will fail if called when a phase is still in a `working` or `aireview` state.
    - This tool cannot be used to skip phases or go backwards in the workflow.

    ## Examples

    <example>
    User: "The plan for IS-1234 looks great. Please approve it and move on to the coding phase."
    Assistant: "Excellent. I will now approve the planning phase and advance the task to coding."
    ```
    mcp_epic-task-manager_approve_and_advance(task_id="IS-1234")
    ```
    The tool marks `planning` as verified, archives the planning artifact, and transitions the task to the `coding_working` state. The returned `ToolResponse` will contain a `next_prompt` with instructions for starting the coding work.
    </example>

    <reasoning>
    1. The assistant correctly identified a direct user command to approve and advance the phase.
    2. It used the appropriate tool for this high-level, human-gated transition.
    3. The assistant's next action (starting to code) will be guided by the `next_prompt` it receives from the server.
    </reasoning>

    ## Parameters

    **task_id** [string] (required) - The Jira task ID (e.g., TEST-123, EP-456).

    ## Returns
    A `ToolResponse` object. If the task is not yet complete, the `next_prompt` will contain instructions for beginning work on the new, current phase. If the final phase is advanced, the message will indicate the task is 'done'.
    """
    return await task_tools.approve_and_advance(task_id)


@app.tool()
async def approve_or_request_changes(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Provides feedback on a submitted artifact during a review step, either approving it or requesting revisions.

    - **Key Features**:
      - Handles the approval/rejection logic for the internal review cycle of a phase.
      - Represents the "AI Self-Review" step or a human-gated sub-stage review (e.g., in planning).
    - **Primary Use Case**: Use this tool when the server's `next_prompt` has instructed you to review an artifact and provide feedback.

    ## Usage

    **Workflow Context:**
    This tool is used when a task is in a review state. The server's prompt will have presented you with an artifact and asked you to assess it against certain criteria. Your call to this tool is the result of that assessment.

    **When providing feedback:**
    - Set `is_approved` to `true` for approval or `false` for revision requests.
    - **MUST** provide `feedback_notes` when `is_approved` is `false` to guide the revision.

    **WARNING:**
    - The tool will fail if the task is not in a valid review state.
    - **NEVER call this tool with `is_approved=True` if you have not thoroughly validated the artifact against the requirements specified in the prompt. A premature approval sends incomplete work to the next step.**

    ## Examples

    <example>
    Assistant: (After being prompted to review its own planning artifact for IS-1234)
    "I'll approve the planning phase work for IS-1234 since the implementation plan meets all requirements."
    ```
    mcp_epic-task-manager_approve_or_request_changes(task_id="IS-1234", is_approved=True)
    ```
    The tool processes the approval. The returned `ToolResponse` contains a `next_prompt` that now informs the user that the artifact is ready for their final review.
    </example>

    <reasoning>
    1. The assistant correctly followed the server's prompt, which instructed it to perform a self-review.
    2. It used `is_approved=true` to signify the work meets the quality criteria.
    3. The server handled the internal state transition, and the assistant's next action is guided by the new `next_prompt`.
    </reasoning>

    <example>
    Assistant: (After reviewing a coding artifact)
    "I'll request revisions for the coding phase, noting the missing error handling and tests."
    ```
    mcp_epic-task-manager_approve_or_request_changes(
        task_id="IS-1234",
        is_approved=False,
        feedback_notes="The implementation is missing error handling for edge cases and lacks unit tests."
    )
    ```
    The tool processes the rejection. The returned `ToolResponse` contains a `next_prompt` that instructs the AI to go back and fix the code, using the `feedback_notes` as guidance.
    </example>

    <reasoning>
    1. The assistant identified a flaw during its self-review.
    2. It correctly used `is_approved=false` and provided specific, actionable `feedback_notes`.
    3. The server routes the task back for rework, and the new `next_prompt` includes the feedback, creating a tight revision loop.
    </reasoning>

    ## Parameters

    **task_id** [string] (required) - The task ID (e.g., "IS-1234", "TEST-456"). Must be an existing task in a review state.

    **is_approved** [boolean] (required) - Whether to approve the artifact. `true` to approve, `false` to request revisions.

    **feedback_notes** [string] (optional, but required when is_approved=false) - Detailed feedback explaining what needs to be revised.

    ## Returns
    A `ToolResponse` object. The `next_prompt` will contain the instructions for the next action, which will differ based on whether the work was approved or rejected.
    """
    return await review_tools.approve_or_request_changes(task_id, is_approved, feedback_notes)


@app.tool()
async def get_task_summary(task_id: str) -> ToolResponse:
    """
    Retrieves a lightweight summary of a task's current status.

    - **Key features**: Provides a quick status check including the task's current workflow state and the status of its live work-in-progress artifact.
    - **Use this tool when**:
      - You need a quick status check of a task.
      - You want to verify a task exists and see its current workflow phase.
    - **Crucial Guardrails**:
      - Use `inspect_archived_artifact` when you need to view the content of a *completed*, archived phase artifact. This tool only shows the status of the current, live `scratchpad.md`.

    ## Usage

    **Before using this tool:**
    - The Epic Task Manager project MUST be initialized.
    - The task must exist in the system.

    **IMPORTANT**: This tool is informational and does not change the state of the task.

    **WARNING**: The tool will fail if the project is not initialized or the `task_id` does not exist.

    ## Examples

    <example>
    User: "What's the current status of task IS-1234?"
    Assistant: "I'll check the current status of task IS-1234 for you."
    ```
    mcp_epic-task-manager_get_task_summary(task_id="IS-1234")
    ```
    The tool returns a `ToolResponse`. The assistant inspects the `data` field of the response and can report to the user: "The task IS-1234 is currently in the 'planning_working' state."
    </example>

    <reasoning>
    1. The assistant chose the correct tool for a simple status request.
    2. The tool provides the necessary information in the `data` field of the `ToolResponse` without affecting the task's state.
    3. The `next_prompt` field in the response will be `None`, so the AI knows no further action is prescribed.
    </reasoning>

    ## Parameters
    **task_id** [string] (required) - The unique identifier for the task.

    ## Returns
    A `ToolResponse` object where the `data` field contains a dictionary with `task_id`, `current_state`, and `artifact_status`. The `next_prompt` field will be `None`.
    """
    return await get_summary_impl(task_id)


@app.tool()
async def inspect_archived_artifact(task_id: str, phase_name: str) -> ToolResponse:
    """
    Retrieves the complete content of an archived artifact for a specific completed phase of a task.

    - **Key Features**: Direct artifact content retrieval for historical review.
    - **Primary Use Case**: Use this tool when you need to review, reference, or analyze the detailed work output from a *previously completed* task phase.
    - **Crucial Guardrails**: Only works for completed phases that have been archived. Use `get_task_summary` to check task status first.

    ## Usage

    **Before using this tool:**
    - Ensure the project has been initialized.
    - Verify the task exists and the specified phase has been completed.

    **IMPORTANT**: This tool is informational and does not change the state of the task.

    **WARNING**: The tool will fail if:
    - The project hasn't been initialized.
    - The `task_id` doesn't exist.
    - The `phase_name` is invalid.
    - The specified phase has not yet been completed and archived.

    ## Parameters
    **task_id** [string] (required) - The task ID (e.g., IS-1234, TEST-456).

    **phase_name** [string] (required) - The phase name to inspect. Must be one of: "gatherrequirements", "planning", "coding", "testing", "finalize".

    ## Returns
    A `ToolResponse` object where the `data` field contains a dictionary with the `task_id`, `phase_name`, and the full `artifact_content`. The `next_prompt` field will be `None`.
    """
    return await inspect_archived_artifact_impl(task_id, phase_name)


@app.tool()
async def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    """
    Marks a single execution step as complete during a multi-step phase like 'coding'.

    - **Core Function**: Acts as a checkpoint. Persists the completion of one atomic step and provides the prompt for the very next step.
    - **Primary Use**: This is the primary tool to be used inside the `coding` phase loop. Call this after successfully executing each step from the execution plan.
    - **Crucial Guardrails**: This tool MUST be called for each step in the exact order they are provided.

    ## Parameters
    - **task_id** [string] (required) - The task identifier.
    - **step_id** [string] (required) - The unique ID of the step that has just been completed.

    ## Returns
    A `ToolResponse` object. The `next_prompt` will contain the instructions for the next step in the sequence.
    """
    return await progress_tools.mark_step_complete(task_id, step_id)


@app.tool()
async def get_active_task() -> ToolResponse:
    """
    Get the currently active task and orchestrate the next workflow action based on its state.

    This tool retrieves the currently active task and intelligently guides the workflow by providing specific next actions through the `next_prompt` field. It acts as a state-aware orchestrator that eliminates guesswork for the AI client.

    - **Key Features**:
      - Returns the active task ID with intelligent workflow orchestration
      - Automatically detects when active tasks are complete and redirects to task discovery
      - Provides seamless workflow resumption through targeted `next_prompt` instructions
      - Handles edge cases like missing active tasks or completed active tasks
    - **Use this tool when**: You need to continue working and want the system to intelligently determine the next action based on current state
    - **Crucial Guardrails**:
      - This tool actively orchestrates workflow decisions - it is NOT purely informational
      - Always follow the `next_prompt` instructions returned by this tool
      - Do NOT make assumptions about what to do next - let the server guide you

    ## Usage

    **Before using this tool:**
    - The Epic Task Manager project MUST be initialized

    **IMPORTANT**: This tool provides intelligent workflow orchestration through the `next_prompt` field. The server determines the correct next action based on the current state.

    **WARNING**: The tool will fail if the project is not initialized.

    ## Examples

    <example>
    User: "Let me continue working on my current task"
    Assistant: "I'll check what task is currently active and determine the next action."
    ```
    mcp_epic-task-manager_get_active_task()
    ```
    The tool returns that EP-123 is active and provides a `next_prompt` instructing the assistant to call `begin_or_resume_task` on EP-123.
    </example>

    <reasoning>
    1. The assistant correctly used this tool when the user wanted to continue work.
    2. The tool provided intelligent orchestration by returning specific instructions in `next_prompt`.
    3. This eliminates the need for the assistant to guess what action to take next.
    </reasoning>

    <example>
    User: "What should I work on next?"
    Assistant: "I'll check the current active task status to determine the next action."
    ```
    mcp_epic-task-manager_get_active_task()
    ```
    The tool detects no active task and returns a `next_prompt` instructing the assistant to call `list_available_tasks`.
    </example>

    <reasoning>
    1. The assistant used this tool when unsure about what to work on next.
    2. The server intelligently detected that no active task exists and provided guidance to discover available work.
    3. The workflow continues seamlessly without requiring the user to manually specify task discovery.
    </reasoning>

    <example>
    User: "Continue with my work"
    Assistant: "I'll check the active task status to guide the next action."
    ```
    mcp_epic-task-manager_get_active_task()
    ```
    The tool finds that the active task EM-456 is already complete and provides a `next_prompt` instructing the assistant to report completion and find the next available task.
    </example>

    <reasoning>
    1. The assistant used this tool for workflow continuation.
    2. The server detected that the active task was already complete and cleaned up the invalid state.
    3. The `next_prompt` provided clear instructions to handle the completion and find new work.
    </reasoning>

    ## Returns
    A `ToolResponse` object where the `data` field contains a dictionary with `active_task_id` and the `next_prompt` field contains specific instructions for the next workflow action.
    """
    return await get_active_task_impl()


@app.tool()
async def get_task_details(task_id: str) -> ToolResponse:
    """
    Retrieves the full details for a single task from the configured provider.

    - **Core Function**: Fetches comprehensive task information including summary, description, and acceptance criteria from the configured task source.
    - **Key Features**:
      - Returns structured task data with all available fields
      - Works with all configured providers (Jira, Linear, Local)
      - Provides rich, user-friendly information for task review
      - Handles file system access internally (no client-side path guessing)
    - **Use this tool when**: You need detailed information about a specific task, typically after discovering it through `list_available_tasks`.
    - **Crucial Guardrails**:
      - This tool MUST be used instead of manual file reading when users ask for task details
      - Do NOT attempt to read task files directly from the `.epictaskmanager/tasks` directory
      - Always use this tool's structured output rather than parsing files yourself

    ## Usage

    **Before using this tool:**
    - Ensure the Epic Task Manager project is initialized
    - Have a valid task ID (typically obtained from `list_available_tasks`)

    **IMPORTANT**: This tool centralizes all task file access within the server, eliminating the need for client-side file system operations.

    **WARNING**: The tool will fail if the project is not initialized or if the task ID doesn't correspond to an existing task.

    ## Examples

    <example>
    User: "Tell me more about task EM-2"
    Assistant: "I'll get the detailed information for task EM-2."
    ```
    mcp_epic-task-manager_get_task_details(task_id="EM-2")
    ```
    The tool returns comprehensive task details including description and acceptance criteria.
    </example>

    <reasoning>
    1. The assistant correctly identified a request for detailed task information.
    2. It used the dedicated tool rather than attempting file system access.
    3. The server handles all parsing and returns structured data.
    </reasoning>

    <example>
    User: "What are the acceptance criteria for the XML structuring task?"
    Assistant: "I'll retrieve the details for that task to show you the acceptance criteria."
    ```
    mcp_epic-task-manager_get_task_details(task_id="EM-2")
    ```
    The tool returns the task details, and the assistant can extract and present the acceptance criteria.
    </example>

    <reasoning>
    1. The assistant recognized that specific task details were needed.
    2. It used the proper tool to get structured data rather than guessing file paths.
    3. The returned data can be used to answer the specific question about acceptance criteria.
    </reasoning>

    ## Parameters

    **task_id** [string] (required) - The unique identifier for the task. This should match the ID returned by `list_available_tasks`. For local provider, this is typically the filename without the .md extension.

    ## Returns
    A `ToolResponse` object where the `data` field contains a dictionary with complete task information including `summary`, `description`, `acceptance_criteria`, `status`, and other provider-specific fields.
    """
    return await task_tools.get_task_details(task_id)


@app.tool()
async def list_available_tasks() -> ToolResponse:
    """
    Lists available tasks from the configured provider that are not yet complete.

    - **Core Function**: Discovers tasks that are available for work from the configured task source (Jira, Linear, or Local).
    - **Key Features**:
      - Filters out tasks that are already in a 'done' state in the Epic Task Manager
      - For local provider: scans the tasks inbox directory for markdown files
      - Returns task summaries with ID, title, and status information
    - **Use this tool when**: You need to find the next available task to work on, or want to see what tasks are pending.
    - **Crucial Guardrails**:
      - This tool MUST be called when no active task exists and the user wants to continue working
      - Do NOT use this tool if you already have a specific task ID to work on
      - For empty results, guide the user to check their task source or create new tasks

    ## Usage

    **Before using this tool:**
    - Ensure the Epic Task Manager project is initialized
    - Verify that the task source is properly configured (local, Jira, or Linear)

    **IMPORTANT**: This tool is informational and does not change any task states. It only discovers available work.

    **WARNING**: The tool will fail if the project is not initialized or the task source is not configured.

    ## Examples

    <example>
    User: "What tasks are available for me to work on?"
    Assistant: "I'll check what tasks are available in your configured task source."
    ```
    mcp_epic-task-manager_list_available_tasks()
    ```
    The tool returns a list of available tasks. The assistant then presents the options to the user.
    </example>

    <reasoning>
    1. The assistant correctly used this tool when the user asked about available work.
    2. The tool provides discovery capability without changing any state.
    3. The returned data helps the user make an informed choice about which task to start.
    </reasoning>

    <example>
    User: "I finished EM-1, what should I work on next?"
    Assistant: "Great! Let me find the next available task for you."
    ```
    mcp_epic-task-manager_list_available_tasks()
    ```
    The tool discovers EM-2 is available and presents it to the user for confirmation.
    </example>

    <reasoning>
    1. The assistant correctly identified that task discovery was needed after completion.
    2. This tool enables seamless workflow continuation without requiring the user to manually specify task IDs.
    3. The workflow becomes more automated and user-friendly.
    </reasoning>

    ## Returns
    A `ToolResponse` object where the `data` field contains an `available_tasks` array with task information. The `next_prompt` will guide the assistant on how to present the options to the user.
    """
    return await task_tools.list_available_tasks()


@app.tool()
async def inspect_and_manage_task(task_id: str, force_transition: str | None = None) -> ToolResponse:
    """
    Inspects a task's current state or forces a manual state transition. This is the primary recovery tool for stuck tasks.

    - **Core Function**: Operates in two modes: Inspection (read-only) and Management (write-state).
    - **Use this tool when**:
        - You need to know the exact internal state of a task.
        - You need to see all valid actions (triggers) available from the current state.
        - A task is stuck and must be manually advanced or reverted by a human operator.

    ## Modes of Operation

    ### 1. Inspection Mode (Default)
    Call the tool with only the `task_id` to get a safe, read-only report.

    - **Action**: `inspect_and_manage_task(task_id="TASK-123")`
    - **Response**: The `data` field will contain the `current_state` and a list of `valid_triggers` (e.g., `['submit_for_ai_review', 'request_revision']`). This tells you exactly what the system can do next.

    ### 2. Management Mode (Use with Caution)
    Call the tool with a `force_transition` string to manually trigger a state change.

    - **Action**: `inspect_and_manage_task(task_id="TASK-123", force_transition="human_approves")`
    - **Response**: If the transition is valid, the task's state will be updated, and the `next_prompt` will guide the next action from the new state.

    ## CRITICAL GUARDRAILS AND WARNINGS
    - **RISK OF CORRUPTION**: Forcing a transition bypasses normal application logic. Forcing a task to `coding_verified` without a valid coding artifact may break subsequent phases. This is an expert-level tool.
    - **ALWAYS INSPECT FIRST**: Before forcing a transition, always run in inspection mode first to see the list of valid triggers.
    - **USE FOR RECOVERY ONLY**: This tool should not be part of the normal workflow. It is for un-sticking tasks after an unexpected error.

    ## Examples

    <example>
    User: "I think task EP-456 is stuck. Can you check its status?"
    Assistant: "I'll inspect the internal state of EP-456."
    ```
    mcp_epic-task-manager_inspect_and_manage_task(task_id="EP-456")
    ```
    The tool returns a `ToolResponse` with `data: {"current_state": "coding_devreview", "valid_triggers": ["request_revision", "human_approves"]}`.
    Assistant: "Task EP-456 is in the 'coding_devreview' state. The valid next actions are to request a revision or to approve the work."
    </example>

    <reasoning>
    1. The assistant correctly used the tool in its safe, read-only inspection mode.
    2. It retrieved the exact state and the valid actions, providing the user with the precise information needed to make a decision.
    3. The `next_prompt` is `None`, so no further action is taken.
    </reasoning>

    <example>
    User: "The AI review for EP-456 seems to have failed, but the code is good. Please manually approve it to the dev review stage."
    Assistant: "Understood. I will force the 'ai_approves' transition to move the task to dev review."
    ```
    mcp_epic-task-manager_inspect_and_manage_task(task_id="EP-456", force_transition="ai_approves")
    ```
    The tool forcefully transitions the state and returns a `ToolResponse` with a `next_prompt` suitable for the new `coding_devreview` state.
    </example>

    <reasoning>
    1. The assistant received an explicit command from a human operator to perform a manual override.
    2. It used the `force_transition` parameter to execute the specific, requested state change.
    3. The system is now "unstuck," and the new `next_prompt` guides the workflow forward.
    </reasoning>

    ## Parameters

    **task_id** [string] (required) - The unique identifier for the task.

    **force_transition** [string] (optional) - The name of the state machine trigger to fire. If omitted, the tool runs in read-only inspection mode. If provided, the tool attempts to force the state change.
    """
    return await management_tools.inspect_and_manage_task(task_id, force_transition)


# ============================================================================
# PROMPTS - Client-facing prompts for guided workflows
# ============================================================================


@app.prompt()
async def implement_next_task_prompt(task_id: str | None = None) -> str:
    """Implements the next task using Epic Task Manager workflow"""
    return await implement_next_task(task_id)


# Main server execution
if __name__ == "__main__":
    app.run()

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/execution/prompter.py
```python
# Standard library imports
from pathlib import Path
import re

from pydantic import ValidationError

# Local application imports
from epic_task_manager.config.config_manager import config_manager
from epic_task_manager.config.settings import settings
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.execution.constants import (
    ERROR_SECTION_NOT_FOUND,
    ERROR_VERIFIED_ARTIFACT_NOT_FOUND,
    PHASE_CODING,
    PHASE_GITSETUP,
    PHASE_REQUIREMENTS,
    PHASE_TESTING,
    SECTION_PLANNING_STRATEGY,
    SECTION_SOLUTION_DESIGN,
    TASK_SOURCE_GENERIC,
    TEMPLATE_SUFFIX_AI_REVIEW,
    TEMPLATE_SUFFIX_EXECUTION_PLAN,
    TEMPLATE_SUFFIX_SOLUTION_DESIGN,
    TEMPLATE_SUFFIX_STRATEGY,
    TEMPLATE_SUFFIX_WORK,
    TEMPLATE_TYPE_PROMPTS,
    WORKFLOW_STAGE_AI_REVIEW,
    WORKFLOW_STAGE_DEV_REVIEW,
    WORKFLOW_STAGE_EXECUTION_PLAN,
    WORKFLOW_STAGE_SOLUTION_DESIGN,
    WORKFLOW_STAGE_STRATEGY,
    WORKFLOW_STAGE_VERIFIED,
    WORKFLOW_STAGE_WORKING,
)
from epic_task_manager.execution.exceptions import ArtifactNotFoundError, InvalidArtifactError
from epic_task_manager.models.artifacts import ExecutionPlanArtifact


class Prompter:
    """Generates dynamic, state-aware prompts for the AI."""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.artifact_manager = ArtifactManager()
        # --- CENTRALIZED CONTEXT MAP ---
        # This map is the single source of truth for context dependencies.
        # Key: The state that needs context.
        # Value: A list of tuples (source_phase_of_artifact, key_for_prompt_context)
        self._CONTEXT_REQUIREMENTS = {
            "planning_strategy": [("gatherrequirements", "verified_gatherrequirements_artifact")],
            "planning_solutiondesign": [
                ("gatherrequirements", "verified_gatherrequirements_artifact"),
                ("planning", "approved_strategy_artifact"),  # Special case: from scratchpad
            ],
            "planning_executionplan": [("planning", "approved_solution_design_artifact")],  # Special case: from scratchpad
            "finalize": [("testing", "verified_testing_artifact")],
            # Phases like gitsetup, coding, testing operate on the repository state
            # and do not require prior artifact context to be injected into their main work prompt.
        }

    def _safe_format_template(self, template: str, context: dict) -> str:
        """Safely format template by only replacing placeholders that exist in context."""
        pattern = re.compile(r"\{([^}]+)\}")

        def safe_replace(match):
            placeholder = match.group(1)
            return str(context.get(placeholder, match.group(0)))

        return pattern.sub(safe_replace, template)

    def _extract_section_from_scratchpad(self, scratchpad_content: str, section_title: str) -> str:
        """Extract a specific section from the scratchpad content or raise ArtifactNotFoundError."""
        pattern = rf"# {section_title}:.*?\n(.*?)(?=\n# |\Z)"
        match = re.search(pattern, scratchpad_content, re.DOTALL)

        if match:
            return match.group(0).strip()

        raise ArtifactNotFoundError(ERROR_SECTION_NOT_FOUND.format(section_title=section_title))

    def _get_local_template_path(self, template_type: str, name: str) -> Path:
        """Get the path to a template in the local user workspace."""
        return settings.prompts_dir / template_type / f"{name}.md"

    def _get_package_template_path(self, template_type: str, name: str) -> Path:
        """Get the path to a template in the package templates directory."""
        return self.template_dir / template_type / f"{name}.md"

    def _load_template(self, template_type: str, name: str) -> str:
        """Loads a template file with local-first resolution strategy."""
        if template_type == TEMPLATE_TYPE_PROMPTS:
            return self._load_prompt_template(name)

        # Check local template first
        local_path = self._get_local_template_path(template_type, name)
        if local_path.exists():
            return local_path.read_text(encoding="utf-8")

        # Fallback to package template
        package_path = self._get_package_template_path(template_type, name)
        if package_path.exists():
            return package_path.read_text(encoding="utf-8")

        raise FileNotFoundError(f"Template not found: {template_type}/{name}.md")

    def _load_prompt_template(self, name: str) -> str:
        """Loads a prompt template with local-first resolution and phase-specific logic."""
        # Check local template first
        local_root_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / f"{name}.md"
        if local_root_path.exists():
            return local_root_path.read_text(encoding="utf-8")

        # Check package template
        package_root_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / f"{name}.md"
        if package_root_path.exists():
            return package_root_path.read_text(encoding="utf-8")

        phase_name, suffix = self._parse_template_name(name)

        if phase_name == PHASE_REQUIREMENTS:
            return self._load_requirements_template(suffix)

        return self._load_phase_template(phase_name, suffix)

    def _parse_template_name(self, name: str) -> tuple[str, str]:
        """Parses template name into phase and suffix."""
        if "_" in name:
            parts = name.split("_", 1)
            return parts[0], parts[1]
        return name, TEMPLATE_SUFFIX_WORK

    def _load_requirements_template(self, suffix: str) -> str:
        """Loads requirements template with local-first resolution and task source fallback."""
        config = config_manager.load_config()
        task_source = config.get_task_source()

        # Check local templates first
        local_task_source_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{task_source.value}_{suffix}.md"
        if local_task_source_path.exists():
            return local_task_source_path.read_text(encoding="utf-8")

        local_generic_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{TASK_SOURCE_GENERIC}_{suffix}.md"
        if local_generic_path.exists():
            return local_generic_path.read_text(encoding="utf-8")

        # Fallback to package templates
        task_source_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{task_source.value}_{suffix}.md"
        if task_source_path.exists():
            return task_source_path.read_text(encoding="utf-8")

        generic_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{TASK_SOURCE_GENERIC}_{suffix}.md"
        if generic_path.exists():
            return generic_path.read_text(encoding="utf-8")

        return self._generate_dynamic_template(PHASE_REQUIREMENTS, suffix)

    def _load_phase_template(self, phase_name: str, suffix: str) -> str:
        """Loads template for a specific phase with local-first resolution."""
        # Check local template first
        local_phase_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / phase_name / f"{suffix}.md"
        if local_phase_path.exists():
            return local_phase_path.read_text(encoding="utf-8")

        # Fallback to package template
        phase_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / phase_name / f"{suffix}.md"
        if phase_path.exists():
            return phase_path.read_text(encoding="utf-8")

        return self._generate_dynamic_template(phase_name, suffix)

    def _generate_dynamic_template(self, phase_name: str, suffix: str) -> str:
        """Generates a dynamic template when file not found."""
        if suffix == TEMPLATE_SUFFIX_WORK:
            return (
                f"# Role: AI Assistant\n\n"
                f"Please work on task {{task_id}} for the {phase_name} phase.\n\n"
                f"**Revision Feedback:** {{revision_feedback}}\n\n"
                f"Please complete the work and call the `submit_for_review` tool with your artifact."
            )

        if suffix == TEMPLATE_SUFFIX_AI_REVIEW:
            return (
                f"# Role: QA Reviewer\n\n"
                f"Please review the artifact for task {{task_id}} in the {phase_name} phase.\n\n"
                f"**Artifact to Review:**\n```markdown\n{{artifact_content}}\n```\n\n"
                f"Call the `approve_or_request_changes` tool with your assessment."
            )

        raise FileNotFoundError(f"Template not found: {phase_name}_{suffix}")

    def generate_prompt(self, task_id: str, machine_state: str, revision_feedback: str | None = None) -> str:
        """The main method to generate a prompt based on the current state."""
        if revision_feedback is None:
            revision_feedback = self._get_stored_revision_feedback(task_id)

        phase_name, sub_state = self._parse_machine_state(machine_state)

        # Handle new phase starts with 'Clean Slate' instruction
        if sub_state == WORKFLOW_STAGE_WORKING:
            prompt = self._generate_coding_step_prompt(task_id) if phase_name == PHASE_CODING else self._generate_working_prompt(task_id, phase_name, revision_feedback)

            # Append formatting guidelines to work prompts
            prompt = self._append_formatting_guidelines(prompt)

            # Prepend clean slate instruction if it's not the very first state
            if machine_state != "gatherrequirements_working":
                return self._prepend_clean_slate_instruction(task_id, prompt)
            return prompt

        # Handle planning sub-stages
        if sub_state in [WORKFLOW_STAGE_STRATEGY, WORKFLOW_STAGE_SOLUTION_DESIGN, WORKFLOW_STAGE_EXECUTION_PLAN]:
            prompt = self._generate_planning_substage_prompt(task_id, sub_state, revision_feedback)
            # Append formatting guidelines to work prompts
            prompt = self._append_formatting_guidelines(prompt)
            # Add clean slate for the first planning sub-stage (strategy)
            if sub_state == WORKFLOW_STAGE_STRATEGY:
                return self._prepend_clean_slate_instruction(task_id, prompt)
            return prompt

        # Handle AI review states
        if sub_state == WORKFLOW_STAGE_AI_REVIEW:
            return self._generate_ai_review_prompt(task_id, phase_name)

        # Handle human/YOLO review states
        if sub_state.endswith(WORKFLOW_STAGE_DEV_REVIEW):
            config = config_manager.load_config()
            if config.features.yolo_mode:
                # YOLO mode is active, generate auto-approval prompt
                template = self._load_template(TEMPLATE_TYPE_PROMPTS, "utils/yolo_auto_approve")
                context = {"task_id": task_id, "current_state": machine_state}
                return self._safe_format_template(template, context)
            # YOLO mode is off, generate standard human review message
            return self._generate_dev_review_message(task_id, phase_name, sub_state)

        # NEW: Handle verified states to bridge the gap to the next phase
        if sub_state == WORKFLOW_STAGE_VERIFIED:
            return self._generate_verified_message(task_id, phase_name)

        return f"Task is in state '{machine_state}'. No further AI action is required."

    def _parse_machine_state(self, machine_state: str) -> tuple[str, str]:
        """Parses machine state into phase and sub-state."""
        if "_" not in machine_state:
            raise ValueError(f"Invalid machine state format: {machine_state}")

        parts = machine_state.split("_", 1)
        return parts[0], parts[1]

    def _generate_planning_substage_prompt(self, task_id: str, sub_state: str, revision_feedback: str | None) -> str:
        """Generates prompt for planning sub-stages."""
        template_suffix = self._get_planning_template_suffix(sub_state)
        template_name = f"planning_{template_suffix}"
        template = self._load_template(TEMPLATE_TYPE_PROMPTS, template_name)

        context = self._build_base_context(task_id, revision_feedback)
        # --- MODIFICATION: SINGLE CALL TO NEW METHOD ---
        machine_state = f"planning_{sub_state}"
        self._inject_context(context, task_id, machine_state)

        return self._safe_format_template(template, context)

    def _get_planning_template_suffix(self, sub_state: str) -> str:
        """Maps planning sub-state to template suffix."""
        mapping = {
            WORKFLOW_STAGE_SOLUTION_DESIGN: TEMPLATE_SUFFIX_SOLUTION_DESIGN,
            WORKFLOW_STAGE_EXECUTION_PLAN: TEMPLATE_SUFFIX_EXECUTION_PLAN,
            WORKFLOW_STAGE_STRATEGY: TEMPLATE_SUFFIX_STRATEGY,
        }
        return mapping.get(sub_state, f"{sub_state}_work")

    def _build_base_context(self, task_id: str, revision_feedback: str | None) -> dict:
        """Builds base context for prompts."""
        # Always load formatting guidelines for all phases
        formatting_guidelines = self._load_guidelines("formatting_guidelines")

        return {
            "task_id": task_id,
            "revision_feedback": revision_feedback or "No feedback provided. Please generate the initial artifact.",
            "formatting_guidelines": formatting_guidelines,
        }

    # --- UNIFIED CONTEXT INJECTION METHOD ---
    def _inject_context(self, context: dict, task_id: str, machine_state: str) -> None:
        """Injects required context into the prompt based on the current state."""
        # Normalize state to match the keys in our context map
        state_key = machine_state.replace("_working", "").replace("devreview", "")

        if state_key not in self._CONTEXT_REQUIREMENTS:
            return

        for source_phase, context_key in self._CONTEXT_REQUIREMENTS[state_key]:
            try:
                # Special handling for planning sub-stages that read from the live scratchpad
                if "approved_" in context_key:
                    scratchpad = self._load_scratchpad(task_id)
                    section_title = ""
                    if "strategy" in context_key:
                        section_title = SECTION_PLANNING_STRATEGY
                    elif "solution_design" in context_key:
                        section_title = SECTION_SOLUTION_DESIGN

                    if scratchpad and section_title:
                        context[context_key] = self._extract_section_from_scratchpad(scratchpad, section_title)
                    else:
                        context[context_key] = f"Error: Could not load required scratchpad section '{section_title}'."
                else:
                    # Standard loading from archived artifacts
                    # We assume for now this loads the .md file. This could be enhanced
                    # to specify .json or .md in the future.
                    context[context_key] = self._load_archived_artifact(task_id, source_phase)

            except ArtifactNotFoundError as e:
                context[context_key] = str(e)

    def _generate_working_prompt(self, task_id: str, phase_name: str, revision_feedback: str | None) -> str:
        """Generates prompt for working states."""
        template_name = f"{phase_name}_{TEMPLATE_SUFFIX_WORK}"
        template = self._load_template(TEMPLATE_TYPE_PROMPTS, template_name)

        context = self._build_base_context(task_id, revision_feedback)
        # --- MODIFICATION: SINGLE CALL TO NEW METHOD ---
        machine_state = f"{phase_name}_working"
        self._inject_context(context, task_id, machine_state)

        # Add guidelines based on phase
        guideline_mapping = {
            PHASE_GITSETUP: "git_guidelines",
            PHASE_CODING: "coding_guidelines",
            PHASE_TESTING: "testing_guidelines",
        }

        if phase_name in guideline_mapping:
            context["guidelines"] = self._load_guidelines(guideline_mapping[phase_name])
        else:
            context["guidelines"] = "No specific guidelines for this phase."

        return self._safe_format_template(template, context)

    def _generate_coding_step_prompt(self, task_id: str) -> str:
        """Generates a prompt for a single coding step."""
        try:
            # --- START REFACTOR ---
            # REMOVE all old regex and parsing logic here.
            # REPLACE with direct JSON loading.
            from epic_task_manager.state.manager import StateManager

            state_manager = StateManager()
            state_file = state_manager._load_state_file()
            task_state = state_file.tasks[task_id]
            current_step_index = task_state.current_step

            # Load the execution plan DIRECTLY from the JSON artifact
            plan_data = self.artifact_manager.read_json_artifact(task_id, "planning")
            plan = ExecutionPlanArtifact(**plan_data)
            # --- END REFACTOR ---

            if not plan.execution_steps:
                return "Error: The execution plan contains no steps."

            total_steps = len(plan.execution_steps)
            if current_step_index >= total_steps:
                return (
                    "# All Execution Steps Complete\n\n"
                    "You have successfully executed all steps in the plan. The final action is to submit a lightweight completion manifest.\n\n"
                    "Please call the `submit_for_review` tool now."
                )

            current_step_obj = plan.execution_steps[current_step_index]

            template = self._load_template(TEMPLATE_TYPE_PROMPTS, "coding_work_single_step")

            context = {
                "task_id": task_id,
                "step_number": current_step_index + 1,
                "total_steps": total_steps,
                "step_id": current_step_obj.prompt_id,
                "step_instruction": current_step_obj.prompt_text,
            }
            return self._safe_format_template(template, context)

        except (ArtifactNotFoundError, InvalidArtifactError, KeyError, IndexError, ValidationError) as e:
            return f"Error generating coding step prompt: {e}"

    def _generate_ai_review_prompt(self, task_id: str, phase_name: str) -> str:
        """Generates prompt for AI review states."""
        template_name = f"{phase_name}_{TEMPLATE_SUFFIX_AI_REVIEW}"
        template = self._load_template(TEMPLATE_TYPE_PROMPTS, template_name)

        artifact_content = self.artifact_manager.read_artifact(task_id)
        context = {
            "task_id": task_id,
            "artifact_content": artifact_content or "Artifact is empty.",
        }

        return self._safe_format_template(template, context)

    def _generate_dev_review_message(self, task_id: str, phase_name: str, sub_state: str) -> str:
        """Generates developer review messages."""
        artifact_path = self.artifact_manager.get_artifact_path(task_id)

        review_messages = {
            "strategydevreview": (
                f"Planning strategy is ready for your review. Please review '{artifact_path}' "
                "and then use the 'approve_or_request_changes' tool with is_approved=true to advance "
                "to solution design, or request revisions."
            ),
            "solutiondesigndevreview": (
                f"Solution design is ready for your review. Please review '{artifact_path}' "
                "and then use the 'approve_or_request_changes' tool with is_approved=true to advance "
                "to execution plan generation, or request revisions."
            ),
            "executionplandevreview": (
                f"Execution plan is ready for your review. Please review '{artifact_path}' "
                "and then use the 'approve_or_request_changes' tool with is_approved=true to complete "
                "planning and advance to coding, or request revisions."
            ),
        }

        return review_messages.get(sub_state, f"Artifact for {phase_name} is ready for your review. Please review '{artifact_path}' and then use the appropriate review tool.")

    def _generate_verified_message(self, task_id: str, phase_name: str) -> str:
        """Generates the prompt for a _verified state, prompting for advancement."""
        config = config_manager.load_config()
        if config.features.yolo_mode:
            return f"# Role: Autonomous Agent (YOLO Mode)\n\nPhase '{phase_name}' for task {task_id} is verified. Automatically advancing to the next phase.\n\nCall the `approve_and_advance` tool to proceed."
        return (
            f"Phase '{phase_name}' is complete and verified. "
            f"The final artifact for this phase is located at `.epictaskmanager/workspace/{task_id}/archive/`. "
            f"Please call `approve_and_advance` to proceed."
        )

    def _prepend_clean_slate_instruction(self, task_id: str, prompt: str) -> str:
        """Prepends the 'Clean Slate' instruction to a prompt."""
        try:
            # Load the XML-based clean_slate template
            clean_slate_template = self._load_template(TEMPLATE_TYPE_PROMPTS, "utils/clean_slate")
            clean_slate_instruction = self._safe_format_template(clean_slate_template, {"task_id": task_id})
            # Combine the two XML-structured prompts.
            # The client AI will see two distinct command blocks.
            return f"{clean_slate_instruction}\n\n---\n\n{prompt}"
        except FileNotFoundError:
            # If the template is missing, don't block the main prompt.
            # This is a non-critical enhancement.
            return prompt

    def _append_formatting_guidelines(self, prompt: str) -> str:
        """Appends formatting guidelines to work prompts."""
        # Load formatting guidelines
        formatting_guidelines = self._load_guidelines("formatting_guidelines")

        if formatting_guidelines:
            # Find the position before "## Required Work Artifact Structure" or at the end
            import re

            artifact_pattern = r"(## Required Work Artifact Structure)"
            match = re.search(artifact_pattern, prompt)

            if match:
                # Insert before the artifact structure section
                position = match.start()
                return prompt[:position] + f"## Formatting Guidelines\n\n{formatting_guidelines}\n\n" + prompt[position:]
            # Append at the end
            return prompt + f"\n\n## Formatting Guidelines\n\n{formatting_guidelines}"

        return prompt

    def _load_archived_artifact(self, task_id: str, phase_name: str) -> str:
        """Loads an archived artifact or raises ArtifactNotFoundError."""
        archived_path = self.artifact_manager.get_archive_path(task_id, phase_name, 1)

        if archived_path.exists():
            return archived_path.read_text()

        raise ArtifactNotFoundError(ERROR_VERIFIED_ARTIFACT_NOT_FOUND.format(phase=phase_name))

    def _load_scratchpad(self, task_id: str) -> str | None:
        """Loads the current scratchpad content."""
        scratchpad_path = self.artifact_manager.get_artifact_path(task_id)

        if scratchpad_path.exists():
            return scratchpad_path.read_text()

        return None

    def _load_guidelines(self, guideline_name: str) -> str:
        """Loads a guideline file or returns an empty string if not found."""
        guideline_path = self.template_dir / "guidelines" / f"{guideline_name}.md"
        if guideline_path.exists():
            return guideline_path.read_text(encoding="utf-8")
        return ""

    def _get_stored_revision_feedback(self, task_id: str) -> str | None:
        """Retrieves stored revision feedback for a task."""
        try:
            from epic_task_manager.state.manager import StateManager

            state_manager = StateManager()
            state_file = state_manager._load_state_file()
            task_state = state_file.tasks.get(task_id)
            if task_state:
                return task_state.revision_feedback
        except Exception:
            # If we can't load the state for any reason, just return None
            pass
        return None

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/task_tools.py
```python
# File: src/epic_task_manager/tools/task_tools.py

from pydantic import ValidationError

from epic_task_manager.config.config_manager import config_manager
from epic_task_manager.config.settings import settings
from epic_task_manager.constants import (
    ADVANCE_TRIGGERS,
    DEFAULT_AI_MODEL,
    DEFAULT_ARTIFACT_VERSION,
    STATUS_ERROR,
    STATUS_SUCCESS,
)
from epic_task_manager.exceptions import TaskNotFoundError
from epic_task_manager.execution.artifact_behavior import ArtifactBehaviorConfig
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models import artifacts
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.machine import STATE_VERIFIED
from epic_task_manager.state.manager import StateManager
from epic_task_manager.task_sources.local.provider import LocalProvider

state_manager = StateManager()
artifact_manager = ArtifactManager()
prompter = Prompter()


def _is_project_initialized() -> bool:
    """Check if project has been initialized."""
    return settings.config_file.exists()


def _error_response(message: str) -> ToolResponse:
    """Create standardized error response."""
    return ToolResponse(status=STATUS_ERROR, message=message)


def _get_pydantic_model_for_state(state: str) -> type[artifacts.BaseModel] | None:
    """Maps a state string to its corresponding Pydantic artifact model."""
    pydantic_model_map = {
        "requirements_working": artifacts.RequirementsArtifact,
        "gitsetup_working": artifacts.GitSetupArtifact,
        "planning_strategy": artifacts.StrategyArtifact,
        "planning_solutiondesign": artifacts.SolutionDesignArtifact,
        "planning_executionplan": artifacts.ExecutionPlanArtifact,
        "scaffolding_working": artifacts.ScaffoldingArtifact,
        "coding_working": artifacts.CodingArtifact,
        "testing_working": artifacts.TestingArtifact,
        "finalize_working": artifacts.FinalizeArtifact,
    }
    # Normalize state for lookup (e.g., 'planning_strategy' from 'planning_strategy_devreview')
    base_state = state.split("_")[0] + "_" + state.split("_")[1] if "_" in state else state
    if base_state in pydantic_model_map:
        return pydantic_model_map[base_state]

    planning_substage_state = state.replace("devreview", "")
    if planning_substage_state in pydantic_model_map:
        return pydantic_model_map[planning_substage_state]

    return None


async def begin_or_resume_task(task_id: str) -> ToolResponse:
    """Initializes a new task or returns the status of an existing one."""
    if not _is_project_initialized():
        return _error_response("Project not initialized. Please run the 'initialize_project' tool first.")

    try:
        model = state_manager.get_machine(task_id)

        # Handle completed tasks gracefully
        if model and model.state == "done":
            state_manager.deactivate_all_tasks()  # Ensure it's not active
            return ToolResponse(
                status=STATUS_SUCCESS,
                message=f"Task {task_id} is already complete.",
                next_prompt=(
                    "<objective>Inform the user that the task is complete and find the next available task.</objective>\n"
                    "<instructions>\n"
                    f"1. Report to the user that task `{task_id}` is already done.\n"
                    "2. Call the `list_available_tasks` tool to discover what to work on next.\n"
                    "</instructions>"
                ),
            )

        if not model:
            model = state_manager.create_machine(task_id)
            artifact_manager.create_task_structure(task_id)
            message = f"Task {task_id} created. Current state: {model.state}"
        else:
            message = f"Resuming task {task_id}. Current state: {model.state}"

        state_manager.set_active_task(task_id)
        prompt = prompter.generate_prompt(task_id, model.state)
        return ToolResponse(status=STATUS_SUCCESS, message=message, next_prompt=prompt)
    except TaskNotFoundError as e:
        return _error_response(str(e))


async def submit_for_review(task_id: str, work_artifact: dict) -> ToolResponse:
    """Validates submitted work, saves machine/human artifacts, and transitions state."""
    if not _is_project_initialized():
        return _error_response("Project not initialized.")
    model = state_manager.get_machine(task_id)
    if not model:
        return _error_response(f"Task {task_id} not found.")

    current_state_before_submit = model.state
    phase_name = current_state_before_submit.split("_")[0]

    try:
        # 1. Validate incoming data against the Pydantic model for the current state.
        pydantic_model = _get_pydantic_model_for_state(current_state_before_submit)
        validated_data = None
        if pydantic_model:
            try:
                full_artifact_data = {"metadata": {"task_id": task_id, "phase": phase_name, "status": "working"}, **work_artifact}
                validated_data = pydantic_model(**full_artifact_data)
            except ValidationError as e:
                return _error_response(f"Work artifact validation failed: {e}")

        # 2. If this is the final planning step, save the validated, machine-readable JSON object.
        #    This is the only data the 'coding' phase will read.
        if current_state_before_submit == "planning_executionplan" and validated_data:
            json_path = artifact_manager.get_task_dir(task_id) / "execution_plan.json"
            json_path.write_text(validated_data.model_dump_json(indent=2), encoding="utf-8")

        # 3. Build and write the human-readable markdown artifact to the scratchpad.
        template_name = _get_artifact_template_name(phase_name, current_state_before_submit.split("_", 1)[1])
        template = prompter._load_template("artifacts", template_name)

        # Add metadata and task_id to work_artifact for template building
        enriched_work_artifact = {
            "metadata": {"task_id": task_id, "phase": phase_name, "status": "working", "version": DEFAULT_ARTIFACT_VERSION, "ai_model": DEFAULT_AI_MODEL},
            "task_id": task_id,
            **work_artifact,
        }

        final_markdown = artifact_manager.build_structured_artifact(template, enriched_work_artifact)

        behavior_config = ArtifactBehaviorConfig()
        if behavior_config.should_append(current_state_before_submit):
            artifact_manager.append_to_artifact(task_id, final_markdown)
        else:
            artifact_manager.write_artifact(task_id, final_markdown)

        # 4. Transition the state and save.
        model.submit_for_ai_review()
        state_manager.save_machine_state(task_id, model)

        # 5. Generate the next prompt for the new state.
        prompt = prompter.generate_prompt(task_id, model.state)
        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Work submitted for {task_id}. State is now '{model.state}'.",
            next_prompt=prompt,
        )
    except Exception as e:
        return _error_response(f"Could not submit work from state '{current_state_before_submit}'. Error: {e}")


async def approve_and_advance(task_id: str) -> ToolResponse:
    """Advances a task to the next major phase, signifying human approval."""
    if not _is_project_initialized():
        return _error_response("Project not initialized.")
    machine = state_manager.get_machine(task_id)
    if not machine:
        return _error_response(f"Task {task_id} not found.")

    current_state = machine.state
    if not (current_state.endswith(("_devreview", "_verified"))):
        return _error_response(f"Cannot advance. Task must be in a review or verified state. Current: {current_state}")

    try:
        current_phase = current_state.split("_")[0]

        if current_state.endswith("_devreview"):
            machine.human_approves()
            state_manager.save_machine_state(task_id, machine)

        # --- THIS IS THE CORRECTED LOGIC ---
        # There is no parsing. We simply move the pre-validated files.
        json_data_to_archive = None
        if current_phase == "planning":
            try:
                live_json_path = artifact_manager.get_task_dir(task_id) / "execution_plan.json"
                if not live_json_path.exists():
                    raise FileNotFoundError("Critical Error: execution_plan.json was not created during the planning phase.")

                # Load the raw text and re-validate into a Pydantic object for the archiver.
                json_content = live_json_path.read_text(encoding="utf-8")
                json_data_to_archive = artifacts.ExecutionPlanArtifact.model_validate_json(json_content)
                live_json_path.unlink()  # Clean up the temporary file.

            except (FileNotFoundError, ValidationError) as e:
                return _error_response(f"Could not finalize and archive planning data. Error: {e}")

        # Archive the human-readable scratchpad and, if applicable, the machine-readable JSON.
        artifact_manager.archive_artifact(task_id, current_phase, json_data=json_data_to_archive)
        # --- END CORRECTION ---

        # Conditional routing logic for scaffolding feature
        if machine.state == f"planning_{STATE_VERIFIED}":
            config = config_manager.load_config()
            if config.features.scaffolding_mode:
                machine.advance_to_scaffold()
            else:
                machine.advance_to_code()
        elif machine.state == f"scaffolding_{STATE_VERIFIED}":
            machine.advance_from_scaffold()
        else:
            # Fallback to existing generic advance logic
            advance_trigger = ADVANCE_TRIGGERS.get(machine.state)
            if not advance_trigger:
                return _error_response(f"No advance trigger found for state: {machine.state}")
            getattr(machine, advance_trigger)()

        if machine.state == "coding_working":
            state_file = state_manager._load_state_file()
            if task_id in state_file.tasks:
                task_state = state_file.tasks[task_id]
                task_state.current_step = 0
                task_state.completed_steps = []
                state_manager._save_state_file(state_file)

        state_manager.save_machine_state(task_id, machine)

        if machine.state == "done":
            state_manager.deactivate_all_tasks()  # Deactivate on completion
            return ToolResponse(
                status=STATUS_SUCCESS,
                message=f"Phase '{current_phase}' approved. Task completed!",
                next_prompt=(
                    "<objective>Inform the user the task is complete and look for the next one.</objective>\n"
                    "<instructions>\n"
                    f"1. Report to the user that task `{task_id}` is now complete.\n"
                    "2. Call `list_available_tasks` to discover what to work on next.\n"
                    "</instructions>"
                ),
            )

        artifact_manager.write_artifact(task_id, f"# {machine.state.split('_')[0].title()} Artifact\n\nWaiting for AI to generate content...")
        prompt = prompter.generate_prompt(task_id, machine.state)
        return ToolResponse(status=STATUS_SUCCESS, message=f"Phase approved. Advanced to '{machine.state}'.", next_prompt=prompt)

    except Exception as e:
        return _error_response(f"Failed to advance phase. Error: {e}")


def _get_artifact_template_name(phase_name: str, sub_state: str) -> str:
    """Get the appropriate artifact template name for a phase and sub-state."""
    _TEMPLATE_NAME_MAP = {
        "planning": {
            "strategy": "planning_strategy_artifact",
            "solutiondesign": "planning_solution_design_artifact",
            "executionplan": "planning_execution_plan_artifact",
        },
    }
    if phase_name == "planning" and sub_state in _TEMPLATE_NAME_MAP["planning"]:
        return _TEMPLATE_NAME_MAP["planning"][sub_state]
    if phase_name == "gitsetup":
        return "git_setup_artifact"
    if phase_name == "scaffolding":
        return "scaffolding_artifact"
    return f"{phase_name}_artifact"


async def list_available_tasks() -> ToolResponse:
    """
    Lists available tasks from the configured provider that are not yet complete.
    For the 'local' provider, this means any task file in the inbox that isn't 'done'.
    """
    if not _is_project_initialized():
        return _error_response("Project not initialized.")

    config = config_manager.load_config()
    state_file = state_manager._load_state_file()
    completed_task_ids = {tid for tid, tstate in state_file.tasks.items() if tstate.current_state == "done"}

    available_tasks = []
    if config.get_task_source() == "local":
        provider = LocalProvider({"tasks_inbox_directory": settings.tasks_inbox_dir})
        all_local_tasks = provider.list_available_tasks()
        available_tasks = [task for task in all_local_tasks if task["id"] not in completed_task_ids]
    # Add logic for Jira/Linear providers here in the future
    # else:
    #     # Call remote provider
    #     pass

    if not available_tasks:
        return ToolResponse(
            status=STATUS_SUCCESS, message="No available tasks found.", data={"available_tasks": []}, next_prompt="<objective>Inform the user that there are no new tasks in the inbox.</objective>"
        )

    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Found {len(available_tasks)} available tasks.",
        data={"available_tasks": available_tasks},
        next_prompt=(
            "<objective>Present the available tasks to the user and await instruction.</objective>\n"
            "<instructions>\n"
            "1. Present the `available_tasks` from the `data` field to the user. The `summary` field should be used for display.\n"
            "2. If the user asks for more details about a specific task, you MUST use the `get_task_details` tool with the corresponding `task_id`.\n"
            "3. If the user confirms they want to start a task, call `begin_or_resume_task` with their chosen task ID.\n"
            "</instructions>"
        ),
    )


async def get_task_details(task_id: str) -> ToolResponse:
    """
    Retrieves the full details for a single task from the configured provider.
    """
    if not _is_project_initialized():
        return _error_response("Project not initialized.")

    config = config_manager.load_config()
    provider_type = config.get_task_source()

    try:
        details = {}
        if provider_type == "local":
            provider = LocalProvider({"tasks_inbox_directory": settings.tasks_inbox_dir})
            details = provider.get_task_details(task_id)
        # Add logic for Jira/Linear here in the future

        if not details:
            return _error_response(f"Could not retrieve details for task '{task_id}'.")

        return ToolResponse(
            status=STATUS_SUCCESS,
            message="Task details retrieved successfully.",
            data=details,
            next_prompt=None,  # This is an informational tool, no next action prescribed.
        )
    except FileNotFoundError:
        return _error_response(f"Task file for '{task_id}' not found in the tasks inbox.")
    except Exception as e:
        return _error_response(f"An error occurred while getting task details: {e}")

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/execution/artifact_manager.py
```python
# Standard library imports
import json
import logging
from pathlib import Path
import re
from typing import Any

from jinja2 import Environment
from pydantic import BaseModel
from tabulate import tabulate

# Third-party imports
import yaml

# Local application imports
from epic_task_manager.config.settings import settings
from epic_task_manager.constants import (
    ARCHIVE_DIR_NAME,
    ARTIFACT_FILENAME,
    PHASE_NUMBERS,
)
from epic_task_manager.execution.constants import (
    ARCHIVE_FILENAME_FORMAT,
)
from epic_task_manager.execution.exceptions import ArtifactNotFoundError, InvalidArtifactError


class ArtifactManager:
    """Handles reading and writing the structured markdown artifacts."""

    def get_task_dir(self, task_id: str) -> Path:
        """Get task directory in the workspace."""
        return settings.workspace_dir / task_id

    def get_artifact_path(self, task_id: str) -> Path:
        return self.get_task_dir(task_id) / ARTIFACT_FILENAME

    def get_archive_path(self, task_id: str, phase_name: str, version: int) -> Path:
        archive_dir = self.get_task_dir(task_id) / ARCHIVE_DIR_NAME
        phase_number = PHASE_NUMBERS.get(phase_name, version)
        return archive_dir / ARCHIVE_FILENAME_FORMAT.format(phase_number=phase_number, phase_name=phase_name)

    def get_json_archive_path(self, task_id: str, phase_name: str) -> Path:
        """Gets the path for a JSON artifact in the archive."""
        archive_dir = self.get_task_dir(task_id) / ARCHIVE_DIR_NAME
        phase_number = PHASE_NUMBERS.get(phase_name, 1)
        # Use the same base name as the markdown artifact, but with a .json extension
        filename = ARCHIVE_FILENAME_FORMAT.format(phase_number=phase_number, phase_name=phase_name).replace(".md", ".json")
        return archive_dir / filename

    def create_task_structure(self, task_id: str) -> None:
        """Creates the necessary directories for a new task."""
        task_dir = self.get_task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / ARCHIVE_DIR_NAME).mkdir(exist_ok=True)

    def write_artifact(self, task_id: str, artifact_content: str) -> None:
        """Writes content to the live task artifact file."""
        artifact_path = self.get_artifact_path(task_id)
        artifact_path.write_text(artifact_content, encoding="utf-8")

    def read_artifact(self, task_id: str) -> str | None:
        """Reads the content of the live task artifact file."""
        artifact_path = self.get_artifact_path(task_id)
        if artifact_path.exists():
            return artifact_path.read_text(encoding="utf-8")
        return None

    def append_to_artifact(self, task_id: str, content: str) -> None:
        """
        Appends content to the live task artifact file with proper separation.

        Creates the file if it doesn't exist. Uses markdown horizontal rule (---)
        as separator between existing and new content.

        Args:
            task_id: Task identifier
            content: Content to append

        Raises:
            ValueError: If task_id or content is empty
        """
        # Validate inputs
        if not task_id or not task_id.strip():
            raise ValueError("Task ID cannot be empty")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        # Ensure task directory exists
        task_dir = self.get_task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = self.get_artifact_path(task_id)

        # Read existing content if file exists
        existing_content = ""
        if artifact_path.exists():
            existing_content = artifact_path.read_text(encoding="utf-8")

        # Determine if separator is needed
        separator = ""
        if existing_content.strip():
            separator = "\n\n---\n"

        # Combine content
        new_content = existing_content + separator + content

        # Write atomically
        artifact_path.write_text(new_content, encoding="utf-8")

    def archive_artifact(self, task_id: str, phase_name: str, json_data: BaseModel | None = None) -> None:
        """Copies the live artifact to the archive and optionally saves a JSON version."""
        live_artifact = self.get_artifact_path(task_id)
        if not live_artifact.exists():
            # If there's no scratchpad but we have JSON, we should still proceed
            if json_data is None:
                return

        archive_dir = self.get_task_dir(task_id) / ARCHIVE_DIR_NAME
        archive_dir.mkdir(exist_ok=True)

        # 1. Archive the human-readable markdown artifact as before
        if live_artifact.exists():
            phase_number = PHASE_NUMBERS.get(phase_name, 1)
            archive_path = archive_dir / ARCHIVE_FILENAME_FORMAT.format(phase_number=phase_number, phase_name=phase_name)
            archive_path.write_text(live_artifact.read_text(encoding="utf-8"))

        # 2. Archive the machine-readable JSON data if provided
        if json_data:
            json_archive_path = self.get_json_archive_path(task_id, phase_name)
            # Use model_dump_json for direct serialization from a Pydantic model
            json_archive_path.write_text(json_data.model_dump_json(indent=2), encoding="utf-8")

    def read_json_artifact(self, task_id: str, phase_name: str) -> dict:
        """Reads and parses a JSON artifact from the archive."""
        json_path = self.get_json_archive_path(task_id, phase_name)
        if not json_path.exists():
            raise ArtifactNotFoundError(f"JSON artifact for phase '{phase_name}' not found.")
        try:
            with json_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidArtifactError(f"Failed to parse JSON artifact for phase '{phase_name}': {e}")

    def build_structured_artifact(self, template: str, data: dict[str, Any]) -> str:
        """Builds a complete markdown artifact from a template and data."""
        self._prepare_metadata(data)
        self._format_structured_fields(data)

        jinja_env = Environment(autoescape=False)

        # Add custom filter for markdown escaping
        def markdown_escape(text):
            """Escapes markdown special characters that can break preview."""
            if not isinstance(text, str):
                text = str(text)
            # Escape backslash sequences that can break markdown
            text = text.replace("\\n", "\n")  # Convert literal \n to actual newlines
            return text.replace("\\t", "\t")  # Convert literal \t to actual tabs

        jinja_env.filters["markdown_escape"] = markdown_escape
        jinja_template = jinja_env.from_string(template)
        return jinja_template.render(**data)

    def _prepare_metadata(self, data: dict[str, Any]) -> None:
        """Prepares metadata for the artifact."""
        metadata_dict = data.get("metadata", {})

        for key, value in metadata_dict.items():
            if key not in data:
                data[key] = value

        metadata_str = yaml.dump(metadata_dict, default_flow_style=False, sort_keys=False).rstrip("\n")
        data["metadata"] = metadata_str

    # --- New Formatting Helpers ---
    def _format_list_as_numbered_list(self, items: list) -> str:
        """Formats a simple list into a markdown numbered list."""
        if not items:
            return "N/A"
        return "\n".join([f"{i + 1}. {item}" for i, item in enumerate(items)])

    def _format_list_as_table(self, items: list[dict], headers: dict) -> str:
        """Formats a list of dictionaries into a markdown table using tabulate."""
        if not items:
            return "N/A"

        if not all(isinstance(i, dict) for i in items):
            return yaml.dump(items, default_flow_style=False, sort_keys=False)

        # Check if any cell content is very long (more than 100 chars)
        has_long_content = any(len(str(item.get(key_map, ""))) > 100 for item in items for key_map in headers.values())

        # For tables with long content, use a more readable format
        if has_long_content:
            formatted_items = []
            for idx, item in enumerate(items, 1):
                item_parts = [f"**{idx}. Entry**"]
                for header, key_map in headers.items():
                    value = item.get(key_map, "N/A")
                    # Wrap long values
                    if isinstance(value, str) and len(value) > 80:
                        # Add proper indentation for multi-line values
                        value = value.replace("\n", "\n   ")
                    item_parts.append(f"- **{header}:** {value}")
                formatted_items.append("\n".join(item_parts))
            return "\n".join(formatted_items)

        # For regular tables, use tabulate
        rows = [[item.get(key_map) for key_map in headers.values()] for item in items]
        return tabulate(rows, headers=headers.keys(), tablefmt="github")

    def _format_execution_steps(self, items: list[dict]) -> str:
        """Formats execution steps into subheadings and code blocks."""
        if not items:
            return "N/A"
        formatted_items = []
        for item in items:
            prompt_id = item.get("prompt_id", "N/A")
            prompt_text = item.get("prompt_text", "No prompt text.")
            formatted_items.append(f"#### {prompt_id}\n```\n{prompt_text}\n```")
        return "\n".join(formatted_items)

    def _format_code_modifications(self, items: list[dict]) -> str:
        """Formats code modifications into file sections and code blocks."""
        if not items:
            return "N/A"
        formatted_items = []
        for item in items:
            file_path = item.get("file_path", "N/A")
            code_block = item.get("code_block", "No code provided.")
            description = item.get("description", "No description provided.")
            formatted_items.append(f"### File: `{file_path}`\n- **Description:** {description}\n- **Code:**\n```\n{code_block}\n```")
        return "\n".join(formatted_items)

    def _format_numbered_text(self, text: str) -> str:
        """Formats text containing numbered patterns (e.g. '1. Item 2. Item') into proper numbered lists."""
        if not text or not isinstance(text, str):
            return text

        import re

        # First, normalize all numbered list formats to use "1." instead of "1)"
        text = re.sub(r"(\d+)\)", r"\1.", text)

        # Pattern to detect numbered lists in text: "1. Something 2. Something else"
        # Use a more robust approach: split by numbered patterns and reconstruct
        numbered_pattern = r"\s*(\d+)\.\s+"

        # Split the text by numbered patterns but keep the numbers
        parts = re.split(numbered_pattern, text.strip())

        if len(parts) >= 5:  # At least intro + num1 + content1 + num2 + content2
            formatted_items = []
            # Skip the intro text (parts[0]) and process pairs (number, content)
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    num = parts[i]
                    content = parts[i + 1].strip()
                    # Clean up content by removing trailing punctuation before next number
                    content = re.sub(r"\s+$", "", content)
                    if content:
                        formatted_items.append(f"{num}. {content}")

            if len(formatted_items) >= 2:  # Only format if we have at least 2 valid items
                # If there's intro text, include it with a line break
                if parts[0].strip():
                    return parts[0].strip() + "\n\n" + "\n".join(formatted_items)
                # Use single line breaks between items for proper markdown formatting
                return "\n".join(formatted_items)

        return text

    def _format_structured_fields(self, data: dict[str, Any]) -> None:
        """Formats various structured fields into human-readable markdown using a dispatch table."""
        # Configuration for list fields
        list_formatter_config = {
            # Simple Lists -> Numbered List
            "acceptance_criteria": (self._format_list_as_numbered_list, None),
            "acceptance_criteria_met": (self._format_list_as_numbered_list, None),
            "key_components": (self._format_list_as_numbered_list, None),
            "dependencies": (self._format_list_as_numbered_list, None),
            # List of Dicts -> Markdown Table
            "files_modified": (self._format_list_as_table, {"File": "file", "Changes": "changes"}),
            "file_breakdown": (self._format_list_as_table, {"File Path": "file_path", "Action": "action", "Change Summary": "change_summary"}),
            # Custom Formatters for Complex Structures
            "execution_prompts": (self._format_execution_steps, None),
            "execution_steps": (self._format_execution_steps, None),  # Same format as execution_prompts
            "code_modifications": (self._format_code_modifications, None),
        }

        # Configuration for string fields that may contain numbered content
        string_formatter_config = {
            "detailed_design": self._format_numbered_text,
            "architectural_decisions": self._format_numbered_text,
            "risk_analysis": self._format_numbered_text,
        }

        # Process list fields
        for field, (formatter, config) in list_formatter_config.items():
            if field in data and isinstance(data[field], list):
                if config:
                    data[field] = formatter(data[field], config)
                else:
                    data[field] = formatter(data[field])

        # Process string fields that may contain numbered content
        for field, formatter in string_formatter_config.items():
            if field in data and isinstance(data[field], str):
                data[field] = formatter(data[field])

    def parse_artifact(self, artifact_content: str) -> tuple[dict[str, Any], str]:
        """Parses a markdown artifact into metadata and main content."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", artifact_content, re.DOTALL)
        if not match:
            return {}, artifact_content

        metadata_str, main_content = match.groups()

        try:
            metadata = yaml.safe_load(metadata_str)
            return metadata or {}, main_content.strip()
        except yaml.YAMLError as e:
            logging.warning(f"Failed to parse YAML metadata in artifact: {e}")
            return {}, artifact_content

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/state/machine.py
```python
# State constants
STATE_WORKING = "working"
STATE_AI_REVIEW = "aireview"
STATE_DEV_REVIEW = "devreview"
STATE_VERIFIED = "verified"
STATE_STRATEGY = "strategy"
STATE_SOLUTION_DESIGN = "solutiondesign"
STATE_EXECUTION_PLAN = "executionplan"
STATE_STRATEGY_DEV_REVIEW = "strategydevreview"
STATE_SOLUTION_DESIGN_DEV_REVIEW = "solutiondesigndevreview"
STATE_EXECUTION_PLAN_DEV_REVIEW = "executionplandevreview"

# Trigger constants
TRIGGER_SUBMIT_FOR_AI_REVIEW = "submit_for_ai_review"
TRIGGER_AI_APPROVES = "ai_approves"
TRIGGER_REQUEST_REVISION = "request_revision"
TRIGGER_HUMAN_APPROVES = "human_approves"
TRIGGER_ADVANCE = "advance"
TRIGGER_ADVANCE_TO_SCAFFOLD = "advance_to_scaffold"
TRIGGER_ADVANCE_TO_CODE = "advance_to_code"
TRIGGER_ADVANCE_FROM_SCAFFOLD = "advance_from_scaffold"

# Phase constants
PHASE_REQUIREMENTS = "gatherrequirements"
PHASE_GITSETUP = "gitsetup"
PHASE_PLANNING = "planning"
PHASE_SCAFFOLDING = "scaffolding"
PHASE_CODING = "coding"
PHASE_TESTING = "testing"
PHASE_FINALIZE = "finalize"
PHASE_DONE = "done"


def create_review_transitions(phase_name: str, revision_dest: str | None = None) -> list[dict]:
    """Generates standard review cycle transitions for a given phase."""
    if revision_dest is None:
        revision_dest = f"{phase_name}_{STATE_WORKING}"

    return [
        {
            "trigger": TRIGGER_SUBMIT_FOR_AI_REVIEW,
            "source": f"{phase_name}_{STATE_WORKING}",
            "dest": f"{phase_name}_{STATE_AI_REVIEW}",
        },
        {
            "trigger": TRIGGER_AI_APPROVES,
            "source": f"{phase_name}_{STATE_AI_REVIEW}",
            "dest": f"{phase_name}_{STATE_DEV_REVIEW}",
        },
        {
            "trigger": TRIGGER_REQUEST_REVISION,
            "source": f"{phase_name}_{STATE_AI_REVIEW}",
            "dest": revision_dest,
        },
        {
            "trigger": TRIGGER_REQUEST_REVISION,
            "source": f"{phase_name}_{STATE_DEV_REVIEW}",
            "dest": revision_dest,
        },
        {
            "trigger": TRIGGER_HUMAN_APPROVES,
            "source": f"{phase_name}_{STATE_DEV_REVIEW}",
            "dest": f"{phase_name}_{STATE_VERIFIED}",
        },
    ]


review_lifecycle_children = [
    {"name": STATE_WORKING},
    {"name": STATE_AI_REVIEW},
    {"name": STATE_DEV_REVIEW},
    {"name": STATE_VERIFIED},
]

planning_substage_children = [
    {"name": STATE_STRATEGY},
    {"name": STATE_STRATEGY_DEV_REVIEW},
    {"name": STATE_SOLUTION_DESIGN},
    {"name": STATE_SOLUTION_DESIGN_DEV_REVIEW},
    {"name": STATE_EXECUTION_PLAN},
    {"name": STATE_EXECUTION_PLAN_DEV_REVIEW},
    {"name": STATE_VERIFIED},
]

states = [
    {
        "name": PHASE_REQUIREMENTS,
        "children": [{"name": STATE_WORKING}, {"name": STATE_VERIFIED}],
        "initial": STATE_WORKING,
    },
    {
        "name": PHASE_GITSETUP,
        "children": review_lifecycle_children,
        "initial": STATE_WORKING,
    },
    {"name": PHASE_PLANNING, "children": planning_substage_children, "initial": STATE_STRATEGY},
    {
        "name": PHASE_SCAFFOLDING,
        "children": review_lifecycle_children,
        "initial": STATE_WORKING,
    },
    {"name": PHASE_CODING, "children": review_lifecycle_children, "initial": STATE_WORKING},
    {"name": PHASE_TESTING, "children": review_lifecycle_children, "initial": STATE_WORKING},
    {"name": PHASE_FINALIZE, "children": review_lifecycle_children, "initial": STATE_WORKING},
    PHASE_DONE,
]

transitions = [
    # Simplified single-step submission for requirements and gitsetup
    {
        "trigger": TRIGGER_SUBMIT_FOR_AI_REVIEW,
        "source": f"{PHASE_REQUIREMENTS}_{STATE_WORKING}",
        "dest": f"{PHASE_REQUIREMENTS}_{STATE_VERIFIED}",
    },
    *create_review_transitions(PHASE_GITSETUP),
    {
        "trigger": TRIGGER_SUBMIT_FOR_AI_REVIEW,
        "source": f"{PHASE_PLANNING}_{STATE_STRATEGY}",
        "dest": f"{PHASE_PLANNING}_{STATE_STRATEGY_DEV_REVIEW}",
    },
    {
        "trigger": TRIGGER_HUMAN_APPROVES,
        "source": f"{PHASE_PLANNING}_{STATE_STRATEGY_DEV_REVIEW}",
        "dest": f"{PHASE_PLANNING}_{STATE_SOLUTION_DESIGN}",
    },
    {
        "trigger": TRIGGER_REQUEST_REVISION,
        "source": f"{PHASE_PLANNING}_{STATE_STRATEGY_DEV_REVIEW}",
        "dest": f"{PHASE_PLANNING}_{STATE_STRATEGY}",
    },
    {
        "trigger": TRIGGER_SUBMIT_FOR_AI_REVIEW,
        "source": f"{PHASE_PLANNING}_{STATE_SOLUTION_DESIGN}",
        "dest": f"{PHASE_PLANNING}_{STATE_SOLUTION_DESIGN_DEV_REVIEW}",
    },
    {
        "trigger": TRIGGER_HUMAN_APPROVES,
        "source": f"{PHASE_PLANNING}_{STATE_SOLUTION_DESIGN_DEV_REVIEW}",
        "dest": f"{PHASE_PLANNING}_{STATE_EXECUTION_PLAN}",
    },
    {
        "trigger": TRIGGER_REQUEST_REVISION,
        "source": f"{PHASE_PLANNING}_{STATE_SOLUTION_DESIGN_DEV_REVIEW}",
        "dest": f"{PHASE_PLANNING}_{STATE_SOLUTION_DESIGN}",
    },
    {
        "trigger": TRIGGER_SUBMIT_FOR_AI_REVIEW,
        "source": f"{PHASE_PLANNING}_{STATE_EXECUTION_PLAN}",
        "dest": f"{PHASE_PLANNING}_{STATE_EXECUTION_PLAN_DEV_REVIEW}",
    },
    {
        "trigger": TRIGGER_HUMAN_APPROVES,
        "source": f"{PHASE_PLANNING}_{STATE_EXECUTION_PLAN_DEV_REVIEW}",
        "dest": f"{PHASE_PLANNING}_{STATE_VERIFIED}",
    },
    {
        "trigger": TRIGGER_REQUEST_REVISION,
        "source": f"{PHASE_PLANNING}_{STATE_EXECUTION_PLAN_DEV_REVIEW}",
        "dest": f"{PHASE_PLANNING}_{STATE_EXECUTION_PLAN}",
    },
    # Standard review cycle for scaffolding phase
    *create_review_transitions(PHASE_SCAFFOLDING),
    # Standard review cycle for coding phase
    *create_review_transitions(PHASE_CODING),
    # Testing phase transitions with special revision destination
    *create_review_transitions(PHASE_TESTING, f"{PHASE_CODING}_{STATE_WORKING}"),
    # Standard review cycle for finalize phase
    *create_review_transitions(PHASE_FINALIZE),
    {"trigger": TRIGGER_ADVANCE, "source": f"{PHASE_REQUIREMENTS}_{STATE_VERIFIED}", "dest": f"{PHASE_GITSETUP}_{STATE_WORKING}"},
    {"trigger": TRIGGER_ADVANCE, "source": f"{PHASE_GITSETUP}_{STATE_VERIFIED}", "dest": f"{PHASE_PLANNING}_{STATE_STRATEGY}"},
    {"trigger": TRIGGER_ADVANCE_TO_SCAFFOLD, "source": f"{PHASE_PLANNING}_{STATE_VERIFIED}", "dest": f"{PHASE_SCAFFOLDING}_{STATE_WORKING}"},
    {"trigger": TRIGGER_ADVANCE_TO_CODE, "source": f"{PHASE_PLANNING}_{STATE_VERIFIED}", "dest": f"{PHASE_CODING}_{STATE_WORKING}"},
    {"trigger": TRIGGER_ADVANCE_FROM_SCAFFOLD, "source": f"{PHASE_SCAFFOLDING}_{STATE_VERIFIED}", "dest": f"{PHASE_CODING}_{STATE_WORKING}"},
    {"trigger": TRIGGER_ADVANCE, "source": f"{PHASE_CODING}_{STATE_VERIFIED}", "dest": f"{PHASE_TESTING}_{STATE_WORKING}"},
    {"trigger": TRIGGER_ADVANCE, "source": f"{PHASE_TESTING}_{STATE_VERIFIED}", "dest": f"{PHASE_FINALIZE}_{STATE_WORKING}"},
    {"trigger": TRIGGER_ADVANCE, "source": f"{PHASE_FINALIZE}_{STATE_VERIFIED}", "dest": PHASE_DONE},
]

# Initial state for new tasks
INITIAL_STATE = f"{PHASE_REQUIREMENTS}_{STATE_WORKING}"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/initialize.py
```python
"""
Initialization tool for Epic Task Manager.

This module provides the interactive initialize_project tool that sets up the
.epictaskmanager directory with provider-specific configuration.
"""

from pathlib import Path
import shutil

from epic_task_manager.config.config_manager import ConfigManager
from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.exceptions import InitializationError
from epic_task_manager.models.config import TaskSource
from epic_task_manager.models.core import StateFile
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
config_manager = ConfigManager()


async def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initialize Epic Task Manager with provider selection.

    Args:
        provider: Provider choice ('atlassian', 'linear', or 'local'). If None, returns available choices.

    Returns:
        ToolResponse: Standardized response object.
    """
    # Check if already initialized
    if _is_already_initialized():
        return _create_already_initialized_response()

    # Return choices if no provider specified
    if provider is None:
        return _get_provider_choices_response()

    try:
        # Validate and perform initialization
        provider_choice = _validate_provider_choice(provider)
        return await _perform_initialization(provider_choice)

    except KeyboardInterrupt:
        return ToolResponse(status=STATUS_ERROR, message="Initialization cancelled by user.")
    except (InitializationError, FileNotFoundError, PermissionError, OSError) as e:
        return ToolResponse(
            status=STATUS_ERROR,
            message=f"Failed to initialize project. Error: {e}",
        )


def _is_already_initialized() -> bool:
    """Check if project is already initialized."""
    etm_dir = settings.epic_task_manager_dir
    return etm_dir.exists() and settings.config_file.exists()


def _create_already_initialized_response() -> ToolResponse:
    """Create response for already initialized project."""
    etm_dir = settings.epic_task_manager_dir
    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Project already initialized at '{etm_dir}'. No changes were made.",
    )


def _get_provider_choices_response() -> ToolResponse:
    """Return provider choices for client to prompt user."""
    choices_data = {
        "choices": [
            {
                "value": "atlassian",
                "label": "Jira (requires Atlassian MCP server)",
                "description": "Connect to Jira for task management via MCP",
            },
            {
                "value": "linear",
                "label": "Linear (requires Linear MCP server)",
                "description": "Connect to Linear for task management via MCP",
            },
            {
                "value": "local",
                "label": "Local markdown files",
                "description": "Use local .md files for task definitions",
            },
        ],
        "prompt": "How will you be sourcing your tasks?",
    }
    return ToolResponse(
        status="choices_needed",
        message="Please select a task source provider.",
        data=choices_data,
    )


def _validate_provider_choice(provider: str) -> str:
    """Validate and normalize provider choice."""
    provider_choice = provider.lower()
    if provider_choice not in ["atlassian", "linear", "local"]:
        raise InitializationError(f"Invalid provider '{provider}'. Must be 'atlassian', 'linear', or 'local'.")
    return provider_choice


async def _perform_initialization(provider_choice: str) -> ToolResponse:
    """Perform the actual initialization setup."""
    # Create directories
    _create_project_directories()

    # Copy default templates to user workspace
    _copy_default_templates()

    # Setup provider-specific configuration
    if provider_choice == "atlassian":
        result = _setup_jira_provider()
        if not result["success"]:
            return ToolResponse(status=STATUS_ERROR, message=result["message"])
    elif provider_choice == "linear":
        result = _setup_linear_provider()
        if not result["success"]:
            return ToolResponse(status=STATUS_ERROR, message=result["message"])
    elif provider_choice == "local":
        _setup_local_provider()

    # Create initial state
    state_manager._save_state_file(StateFile())

    etm_dir = settings.epic_task_manager_dir
    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Successfully initialized Epic Task Manager project in '{etm_dir}' with {provider_choice} provider.",
    )


def _create_project_directories() -> None:
    """Create the necessary project directories."""
    etm_dir = settings.epic_task_manager_dir
    etm_dir.mkdir(exist_ok=True)
    settings.workspace_dir.mkdir(exist_ok=True)

    # Create the architectural documentation README
    _create_workspace_readme(etm_dir)


def _copy_default_templates() -> None:
    """Copy default templates to user workspace for customization."""
    source_dir = settings.templates_dir
    dest_dir = settings.prompts_dir

    try:
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
    except (OSError, shutil.Error) as e:
        raise InitializationError(f"Failed to copy templates: {e}")


def _setup_jira_provider() -> dict:
    """Setup Jira provider with MCP connectivity check"""
    if config_manager.validate_mcp_availability(TaskSource.ATLASSIAN):
        config_manager.setup_provider_config(TaskSource.ATLASSIAN, {"connection_method": "mcp"})
        return {"success": True}
    return {
        "success": False,
        "message": "Could not connect to the Atlassian MCP server. Please ensure it is running and accessible.",
    }


def _setup_linear_provider() -> dict:
    """Setup Linear provider with MCP connectivity check"""
    if config_manager.validate_mcp_availability(TaskSource.LINEAR):
        config_manager.setup_provider_config(TaskSource.LINEAR, {"connection_method": "mcp"})
        return {"success": True}
    return {
        "success": False,
        "message": "Could not connect to the Linear MCP server. Please ensure it is running and accessible.",
    }


def _setup_local_provider() -> None:
    """Setup local provider with tasks inbox and README"""
    settings.tasks_inbox_dir.mkdir(exist_ok=True)
    readme_path = settings.tasks_inbox_dir / "README.md"
    readme_content = "# Local Task Files\n\nThis directory is your task inbox for Epic Task Manager."
    readme_path.write_text(readme_content, encoding="utf-8")
    config_manager.setup_provider_config(TaskSource.LOCAL)


def _create_workspace_readme(etm_dir: Path) -> None:
    """Create architectural documentation README in the workspace root."""
    readme_path = etm_dir / "README.md"
    readme_content = """# Epic Task Manager Workspace

This directory contains all data for the Epic Task Manager.

## Directory Structure

- **`workspace/`**: Contains the live, work-in-progress data for each active task.
  - **`{task_id}/`**: A dedicated directory for each task.
  - **`{task_id}/scratchpad.md`**: The live "whiteboard" for the current phase. All work is appended here.
  - **`{task_id}/archive/`**: The immutable, historical record of a task. Once a phase is completed, its final artifact is stored here.

- **`tasks/`**: (For "local" mode only) The inbox for new task definitions written in Markdown.

- **`prompts/`**: Contains local overrides for the AI's prompt templates. You can customize these files to change the AI's behavior and personality.

- **`config.json`**: The main configuration file for the project.

- **`state.json`**: The internal state file for all tasks. **Do not edit this file manually unless you are recovering from a critical error.**

## The `03-planning.json` Artifact

You may notice a `03-planning.json` file in the `archive` directory alongside the standard `.md` files. This is intentional and critical for system stability.

-   The `03-planning.md` file is the **human-readable** log of the planning process.
-   The `03-planning.json` file is the **machine-readable** final execution plan.

The `coding` phase reads this `.json` file directly to ensure that it executes the approved plan with perfect fidelity. This prevents errors that could arise from misinterpreting the markdown file.
"""
    readme_path.write_text(readme_content, encoding="utf-8")

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/local/provider.py
```python
"""
Local file-based task provider implementation for Epic Task Manager.

This provider reads task definitions from markdown files in the
.epictaskmanager/tasks/ inbox directory.
"""

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from epic_task_manager.task_sources.base import LocalTaskProvider
from epic_task_manager.task_sources.constants import (
    COMMENT_SECTION_HEADER,
    COMMENT_TEMPLATE,
    COMMENT_TIMESTAMP_FORMAT,
    DEFAULT_LOCAL_TASK_STATUS,
    IGNORED_TASK_FILES,
    STATUS_UPDATE_TEMPLATE,
    TASK_FILE_EXTENSION,
)


class LocalProvider(LocalTaskProvider):
    """Local markdown file-based task provider"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.tasks_inbox = Path(config.get("tasks_inbox_directory", ".epictaskmanager/tasks"))

    def get_task_details(self, task_id: str) -> dict[str, Any]:
        """
        Retrieve task details from local markdown file

        Args:
            task_id: Filename (with or without .md extension)

        Returns:
            Dict containing parsed task details

        Raises:
            ValueError: If task_id is empty or invalid
            FileNotFoundError: If task file doesn't exist
            PermissionError: If file cannot be read due to permissions
            UnicodeDecodeError: If file encoding is invalid
        """
        if not task_id or not task_id.strip():
            raise ValueError("task_id cannot be empty")

        # Ensure task_id has .md extension
        if not task_id.endswith(TASK_FILE_EXTENSION):
            task_id = f"{task_id}{TASK_FILE_EXTENSION}"

        task_file = self.tasks_inbox / task_id

        if not task_file.exists():
            raise FileNotFoundError(f"Task file not found: {task_file}")

        try:
            content = task_file.read_text(encoding="utf-8")
        except PermissionError as e:
            raise PermissionError(f"Cannot read task file {task_file}: Permission denied") from e
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, f"Invalid encoding in task file {task_file}: {e.reason}") from e

        return self._parse_markdown_task(content, task_id)

    def _parse_markdown_task(self, content: str, filename: str) -> dict[str, Any]:
        """Parse markdown task file into structured data"""
        lines = content.split("\n")

        # Extract title (first heading)
        title = filename.replace(".md", "")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract description
        description_lines = []
        in_description = False
        for line in lines:
            if line.startswith("## Description"):
                in_description = True
                continue
            if line.startswith("## ") and in_description:
                break
            if in_description:
                description_lines.append(line)

        description = "\n".join(description_lines).strip()

        # Extract acceptance criteria
        acceptance_criteria = []
        in_criteria = False
        for line in lines:
            if line.startswith("## Acceptance Criteria"):
                in_criteria = True
                continue
            if line.startswith("## ") and in_criteria:
                break
            if in_criteria and (line.startswith(("- [ ]", "- [x]", "-"))):
                # Clean up checkbox format
                criteria = re.sub(r"^-\s*\[.\]\s*", "", line.strip())
                criteria = re.sub(r"^-\s*", "", criteria)
                if criteria:
                    acceptance_criteria.append(criteria)

        return {
            "summary": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "status": DEFAULT_LOCAL_TASK_STATUS,
            "assignee": None,
            "labels": [],
            "source_file": filename,
        }

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status in local file (adds status comment)

        Args:
            task_id: Task filename
            status: New status

        Returns:
            bool: True if update successful, False otherwise
        """
        if not task_id or not task_id.strip():
            return False

        if not status or not status.strip():
            return False

        try:
            if not task_id.endswith(TASK_FILE_EXTENSION):
                task_id = f"{task_id}{TASK_FILE_EXTENSION}"

            task_file = self.tasks_inbox / task_id
            if not task_file.exists():
                return False

            content = task_file.read_text(encoding="utf-8")

            # Add status update as comment at the end
            status_comment = STATUS_UPDATE_TEMPLATE.format(status)
            if status_comment not in content:
                content += status_comment
                task_file.write_text(content, encoding="utf-8")

            return True
        except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError):
            return False

    def add_task_comment(self, task_id: str, comment: str) -> bool:
        """
        Add comment to local task file

        Args:
            task_id: Task filename
            comment: Comment to add

        Returns:
            bool: True if comment added successfully, False otherwise
        """
        if not task_id or not task_id.strip():
            return False

        if not comment or not comment.strip():
            return False

        try:
            if not task_id.endswith(TASK_FILE_EXTENSION):
                task_id = f"{task_id}{TASK_FILE_EXTENSION}"

            task_file = self.tasks_inbox / task_id
            if not task_file.exists():
                return False

            content = task_file.read_text(encoding="utf-8")

            # Add comment section if it doesn't exist
            if "## Comments" not in content:
                content += COMMENT_SECTION_HEADER

            # Add the new comment
            timestamp = datetime.now().strftime(COMMENT_TIMESTAMP_FORMAT)
            new_comment = COMMENT_TEMPLATE.format(timestamp, comment)
            content += new_comment

            task_file.write_text(content, encoding="utf-8")
            return True
        except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError):
            return False

    def list_available_tasks(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        List all markdown task files in the inbox directory

        Args:
            filters: Optional filters (not implemented for local provider)

        Returns:
            List of task summaries
        """
        tasks: list[dict[str, Any]] = []

        if not self.tasks_inbox.exists():
            return tasks

        for task_file in self.tasks_inbox.glob(f"*{TASK_FILE_EXTENSION}"):
            if task_file.name in IGNORED_TASK_FILES:
                continue  # Skip ignored files

            try:
                task_details = self.get_task_details(task_file.name)
                tasks.append(
                    {
                        "id": task_file.stem,
                        "summary": task_details["summary"],
                        "status": task_details["status"],
                        "file": task_file.name,
                    }
                )
            except (ValueError, FileNotFoundError, PermissionError, UnicodeDecodeError):
                # Skip files that can't be parsed
                continue

        return tasks

    def get_provider_capabilities(self) -> dict[str, bool]:
        """Return capabilities of the local provider"""
        return {
            "status_updates": True,  # Can add status comments
            "comments": True,  # Can add comments
            "task_creation": True,  # Can create new markdown files
            "task_deletion": True,  # Can delete markdown files
            "file_attachments": False,  # No attachment support
        }

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/models/artifacts.py
```python
# File: src/epic_task_manager/models/artifacts.py

# Standard library imports
from datetime import datetime

# Third-party imports
from pydantic import BaseModel, Field, field_validator

# Local application imports
from epic_task_manager.constants import DEFAULT_AI_MODEL, DEFAULT_ARTIFACT_VERSION

from .enums import ArtifactStatus, FileAction, TaskPhase


class ArtifactMetadata(BaseModel):
    """Represents the YAML front matter in an artifact file"""

    task_id: str = Field(..., pattern=r"^[A-Z]+-\d+$", description="Jira task ID format")
    phase: TaskPhase
    status: ArtifactStatus
    version: str = Field(default=DEFAULT_ARTIFACT_VERSION, pattern=r"^\d+\.\d+$")
    ai_model: str = Field(default=DEFAULT_AI_MODEL)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("task_id")
    @classmethod
    def validate_task_id_format(cls, v: str) -> str:
        """Ensure task ID follows Jira format"""
        if not v or not v.strip():
            raise ValueError("Task ID cannot be empty")
        return v.upper()

    class Config:
        use_enum_values = True


class FileChange(BaseModel):
    """Details a single file to be changed"""

    file_path: str = Field(..., min_length=1, description="Path to file")
    action: FileAction
    change_summary: str = Field(..., min_length=10, max_length=500)

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Ensure file path is not empty or just whitespace"""
        if not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()

    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, v) -> str:
        """Accept case-insensitive action values and normalize to uppercase"""
        if isinstance(v, str):
            # Handle common lowercase variations
            upper_v = v.upper()
            if upper_v in ["CREATE", "MODIFY", "DELETE"]:
                return upper_v
        return v  # Let pydantic handle invalid values


class RequirementsArtifact(BaseModel):
    """Structured data for the requirements phase."""

    metadata: ArtifactMetadata
    task_summary: str
    task_description: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class GitSetupArtifact(BaseModel):
    """Structured data for the git_setup phase."""

    metadata: ArtifactMetadata
    branch_name: str = Field(..., description="The name of the git branch")
    branch_created: bool = Field(..., description="Whether a new branch was created")
    branch_status: str = Field(..., description="Current git status of the branch")
    ready_for_work: bool = Field(..., description="Confirmation that branch is ready for development")


class PlanningArtifact(BaseModel):
    """Structured data for the planning phase artifact."""

    metadata: ArtifactMetadata
    scope_verification: str
    technical_approach: str
    file_breakdown: list[FileChange] = Field(default_factory=list)


class StrategyArtifact(BaseModel):
    """Structured data for the planning strategy phase."""

    metadata: ArtifactMetadata
    high_level_strategy: str = Field(..., description="Overall approach and strategic decisions")
    key_components: list[str] = Field(..., description="Major components or modules to be implemented")
    architectural_decisions: str = Field(..., description="Key architectural choices and rationale")
    risk_analysis: str = Field(..., description="Potential risks and mitigation strategies")


class SolutionDesignArtifact(BaseModel):
    """Structured data for the planning solution design phase."""

    metadata: ArtifactMetadata
    approved_strategy_summary: str = Field(..., description="Brief summary of approved strategy")
    detailed_design: str = Field(..., description="Detailed technical design based on strategy")
    file_breakdown: list[FileChange] = Field(..., description="Comprehensive file-by-file breakdown")
    dependencies: list[str] = Field(default_factory=list, description="External dependencies or libraries needed")


class ExecutionStep(BaseModel):
    """A single execution step in the implementation plan."""

    prompt_id: str = Field(..., pattern=r"^STEP-\d{3,}$", description="Unique ID for this execution step")
    prompt_text: str = Field(..., description="The specific task instruction")
    target_files: list[str] = Field(..., description="Files this step will affect")
    depends_on: list[str] = Field(default_factory=list, description="IDs of execution steps this depends on")


class ExecutionPlanArtifact(BaseModel):
    """Structured data for the planning execution plan generation phase."""

    metadata: ArtifactMetadata
    approved_design_summary: str = Field(..., description="Brief summary of approved solution design")
    execution_steps: list[ExecutionStep] = Field(..., description="Machine-executable list of execution steps")
    execution_order_notes: str = Field(..., description="Notes on optimal execution order")


class ScaffoldingArtifact(BaseModel):
    """Structured data for the scaffolding phase artifact."""

    metadata: ArtifactMetadata
    files_scaffolded: list[str] = Field(default_factory=list, description="List of file paths that have been scaffolded with TODO comments.")


class CodingArtifact(BaseModel):
    """Lightweight completion manifest for the coding phase."""

    metadata: ArtifactMetadata
    implementation_summary: str
    execution_steps_completed: list[str] = Field(default_factory=list, description="List of execution step IDs that were completed during implementation")
    testing_notes: str
    acceptance_criteria_met: list[str] = Field(
        default_factory=list,
        description="List of how each acceptance criterion was satisfied",
    )


class TestResults(BaseModel):
    """Structured test execution results."""

    command_run: str = Field(..., description="The test command that was executed")
    exit_code: int = Field(..., description="Exit code from test execution (0 = success)")
    full_output: str = Field(..., description="Complete output from test execution")


class TestingArtifact(BaseModel):
    """Structured data for the testing phase artifact."""

    metadata: ArtifactMetadata
    test_results: TestResults


class FinalizeArtifact(BaseModel):
    """Structured data for the finalize phase artifact."""

    metadata: ArtifactMetadata
    commit_hash: str = Field(..., description="Git commit hash from the final commit")
    pull_request_url: str = Field(..., description="URL of the created pull request")


class TaskSummaryResponse(BaseModel):
    """Response model for the get_task_summary tool."""

    task_id: str
    current_state: str
    artifact_status: str


class InspectArchivedArtifactResponse(BaseModel):
    """Response model for the inspect_archived_artifact tool."""

    task_id: str
    phase_name: str
    artifact_content: str

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/config/config_manager.py
```python
"""
Configuration management utilities for Epic Task Manager
"""

from __future__ import annotations

from datetime import datetime

# Standard library imports
import json
import logging
from pathlib import Path

# Third-party imports
from pydantic import ValidationError

# Local application imports
from epic_task_manager.models.config import (
    EpicConfig,
    JiraConfig,
    LinearConfig,
    TaskSource,
)

from .settings import settings

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration persistence and validation"""

    def __init__(self, config_file: Path | None = None):
        self.config_file = config_file or settings.config_file

    def load_config(self) -> EpicConfig:
        """
        Load configuration from config.json with validation and migration support

        Returns:
            EpicConfig: Loaded and validated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        if not self.config_file.exists():
            logger.info(f"Config file {self.config_file} not found, creating default")
            return self._create_default_config()

        try:
            config_data = self._load_raw_config_data()
            config = self.validate_config(config_data)
        except (json.JSONDecodeError, ValidationError) as e:
            return self._handle_config_load_error(e)
        else:
            logger.info(f"Loaded configuration from {self.config_file}")
            return config

    def _load_raw_config_data(self) -> dict:
        """Load raw configuration data from file"""
        with self.config_file.open(encoding="utf-8") as f:
            return json.load(f)

    def _handle_config_load_error(self, error: Exception) -> EpicConfig:
        """Handle configuration load errors by backing up and creating default"""
        logger.exception(f"Failed to load config from {self.config_file}: {error}")
        logger.info("Creating backup and using default configuration")
        self._backup_invalid_config()
        return self._create_default_config()

    def save_config(self, config: EpicConfig) -> None:
        """
        Save configuration to config.json

        Args:
            config: Configuration to save
        """
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        config.updated_at = datetime.now()

        # Serialize to JSON (exclude sensitive fields)
        config_data = config.model_dump(mode="json")

        with self.config_file.open("w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved configuration to {self.config_file}")

    def validate_config(self, config_data: dict) -> EpicConfig:
        """
        Validate configuration data

        Args:
            config_data: Raw configuration dictionary

        Returns:
            EpicConfig: Validated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        return EpicConfig(**config_data)

    def _create_default_config(self) -> EpicConfig:
        """Create default configuration"""
        config = EpicConfig()
        self.save_config(config)
        return config

    def _backup_invalid_config(self) -> None:
        """Create backup of invalid configuration file"""
        if self.config_file.exists():
            backup_file = self.config_file.with_suffix(".json.backup")
            self.config_file.rename(backup_file)
            logger.info(f"Backed up invalid config to {backup_file}")

    def setup_provider_config(self, task_source: TaskSource, provider_config: dict | None = None) -> EpicConfig:
        """Set up provider-specific configuration"""
        config = self.load_config()
        config.providers.task_source = task_source

        if task_source == TaskSource.ATLASSIAN and provider_config:
            config.providers.task_source_config.jira = JiraConfig(**provider_config)
        elif task_source == TaskSource.LINEAR and provider_config:
            config.providers.task_source_config.linear = LinearConfig(**provider_config)

        self.save_config(config)
        return config

    def validate_mcp_availability(self, task_source: TaskSource) -> bool:
        """Check if required MCP tools are available for the given task source"""
        if task_source == TaskSource.LOCAL:
            return True  # Local doesn't need MCP tools

        try:
            if task_source == TaskSource.ATLASSIAN:
                # Try to import and test Atlassian MCP tools
                import mcp  # noqa: F401

                # This would be replaced with actual MCP tool availability check
                # For now, we'll assume it's available if imported successfully
                return True
            if task_source == TaskSource.LINEAR:
                # Similar check for Linear MCP tools
                return True
        except ImportError:
            return False
        else:
            return True


# Global config manager instance
config_manager = ConfigManager()


def load_config() -> EpicConfig:
    """Load the current configuration"""
    return config_manager.load_config()


def save_config(config: EpicConfig) -> None:
    """Save the configuration"""
    config_manager.save_config(config)


def get_config_file_path() -> Path:
    """Get the configuration file path"""
    return config_manager.config_file

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/execution/artifact_behavior.py
```python
"""
Configuration system for artifact behavior management in Epic Task Manager.

This module provides phase-specific behavior configuration for artifact generation,
supporting both REPLACE and APPEND_ONLY modes based on phase requirements.
"""

from enum import Enum


class ArtifactBehavior(Enum):
    """Defines artifact generation behaviors for different phases."""

    REPLACE = "replace"
    APPEND_ONLY = "append_only"


class ArtifactBehaviorConfig:
    """
    Configuration class for managing phase-specific artifact behaviors.

    Provides configuration-driven behavior determination for artifact generation,
    supporting extensible phase configuration while maintaining default behaviors.
    """

    def __init__(self):
        """Initialize configuration with default phase behaviors."""
        # Phases that use append-only behavior
        self._append_only_phases: set[str] = {"planning"}

        # First sub-stage for each append-only phase
        self._first_sub_stages: dict[str, str] = {"planning": "strategy"}

        # Valid sub-stages for each append-only phase
        self._phase_sub_stages: dict[str, set[str]] = {"planning": {"strategy", "solutiondesign", "executionplan"}}

    def get_behavior(self, state: str) -> ArtifactBehavior:
        """
        Determine artifact behavior for a given state.

        Args:
            state: State string (e.g., "planning_strategy", "coding_working")

        Returns:
            ArtifactBehavior enum value (REPLACE or APPEND_ONLY)
        """
        phase_name = self._extract_phase_name(state)

        if phase_name in self._append_only_phases:
            return ArtifactBehavior.APPEND_ONLY

        return ArtifactBehavior.REPLACE

    def should_append(self, state: str) -> bool:
        """
        Determine if content should be appended to existing artifact.

        For APPEND_ONLY phases:
        - First sub-stage: False (write new file)
        - Subsequent sub-stages: True (append to existing)

        For REPLACE phases: Always False

        Args:
            state: State string (e.g., "planning_strategy", "coding_working")

        Returns:
            True if content should be appended, False if it should replace
        """
        behavior = self.get_behavior(state)

        if behavior == ArtifactBehavior.REPLACE:
            return False

        # For APPEND_ONLY phases, check if this is the first sub-stage
        return not self.is_first_sub_stage(state)

    def is_first_sub_stage(self, state: str) -> bool:
        """
        Check if the given state represents the first sub-stage of a phase.

        Args:
            state: State string (e.g., "planning_strategy", "coding_working")

        Returns:
            True if this is the first sub-stage, False otherwise
        """
        phase_name, sub_stage = self._parse_state(state)

        if phase_name not in self._append_only_phases:
            return False

        first_sub_stage = self._first_sub_stages.get(phase_name)
        return sub_stage == first_sub_stage

    def add_append_only_phase(self, phase_name: str, first_sub_stage: str, sub_stages: set[str]) -> None:
        """
        Add a new phase with append-only behavior.

        This method enables extensibility for future phases that need append-only behavior.

        Args:
            phase_name: Name of the phase (e.g., "coding")
            first_sub_stage: Name of the first sub-stage (e.g., "implementation")
            sub_stages: Set of all valid sub-stages for this phase
        """
        self._append_only_phases.add(phase_name)
        self._first_sub_stages[phase_name] = first_sub_stage
        self._phase_sub_stages[phase_name] = sub_stages

    def _extract_phase_name(self, state: str) -> str:
        """
        Extract phase name from state string.

        Args:
            state: State string (e.g., "planning_strategy", "coding_working")

        Returns:
            Phase name (e.g., "planning", "coding")
        """
        if not state or "_" not in state:
            return state

        return state.split("_")[0]

    def _parse_state(self, state: str) -> tuple[str, str]:
        """
        Parse state string into phase and sub-stage components.

        Args:
            state: State string (e.g., "planning_strategy", "coding_working")

        Returns:
            Tuple of (phase_name, sub_stage)
        """
        if not state:
            return "", "working"

        if "_" not in state:
            return state, "working"

        parts = state.split("_", 1)
        return parts[0], parts[1]

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/base.py
```python
"""
Base provider interface for Epic Task Manager task sources.

This module defines the abstract interface that all task source providers must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from epic_task_manager.models.config import TaskSource


class TaskProvider(ABC):
    """Abstract base class for task source providers"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the provider with configuration

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config

    @property
    @abstractmethod
    def provider_type(self) -> TaskSource:
        """Return the task source type this provider handles"""

    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that the provider configuration is correct

        Returns:
            bool: True if configuration is valid, False otherwise
        """

    @abstractmethod
    def test_connectivity(self) -> bool:
        """
        Test connectivity to the task source

        Returns:
            bool: True if connection successful, False otherwise
        """

    @abstractmethod
    def get_task_details(self, task_id: str) -> dict[str, Any]:
        """
        Retrieve task details from the task source

        Args:
            task_id: Unique identifier for the task

        Returns:
            Dict containing task details with keys:
            - summary: Task title/summary
            - description: Detailed task description
            - acceptance_criteria: List of acceptance criteria
            - status: Current task status
            - assignee: Task assignee (if any)
            - labels: List of task labels/tags
        """

    @abstractmethod
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update the status of a task in the task source

        Args:
            task_id: Unique identifier for the task
            status: New status to set

        Returns:
            bool: True if update successful, False otherwise
        """

    @abstractmethod
    def add_task_comment(self, task_id: str, comment: str) -> bool:
        """
        Add a comment to a task

        Args:
            task_id: Unique identifier for the task
            comment: Comment text to add

        Returns:
            bool: True if comment added successfully, False otherwise
        """

    @abstractmethod
    def list_available_tasks(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        List available tasks from the task source

        Args:
            filters: Optional filters to apply to task listing

        Returns:
            List of task dictionaries with basic task information
        """

    @abstractmethod
    def get_provider_capabilities(self) -> dict[str, bool]:
        """
        Return capabilities supported by this provider

        Returns:
            Dictionary of capability names and whether they're supported:
            - status_updates: Can update task status
            - comments: Can add comments to tasks
            - task_creation: Can create new tasks
            - task_deletion: Can delete tasks
            - file_attachments: Can attach files to tasks
        """


class LocalTaskProvider(TaskProvider):
    """Base class for local file-based task providers"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.tasks_dir = Path(config.get("tasks_directory", ".epictaskmanager/tasks"))

    @property
    def provider_type(self) -> TaskSource:
        return TaskSource.LOCAL

    def validate_configuration(self) -> bool:
        """Validate local provider configuration"""
        return self.tasks_dir.exists() or self.tasks_dir.parent.exists()

    def test_connectivity(self) -> bool:
        """Test local file system access"""
        try:
            self.tasks_dir.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False


class RemoteTaskProvider(TaskProvider):
    """Base class for remote API-based task providers"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url")
        self.connection_method = config.get("connection_method", "api")

    def validate_configuration(self) -> bool:
        """Validate remote provider configuration"""
        return bool(self.base_url) or self.connection_method == "mcp"

    @abstractmethod
    def test_connectivity(self) -> bool:
        """Test connectivity to remote service"""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/state/manager.py
```python
# Standard library imports
import json

# Third-party imports
from transitions.extensions.factory import HierarchicalMachine

# Local application imports
from epic_task_manager.config.settings import settings
from epic_task_manager.models.core import StateFile, TaskState

from .machine import INITIAL_STATE, states, transitions


class TaskAlreadyExistsError(ValueError):
    """Raised when attempting to create a task that already exists."""


class TaskNotFoundError(ValueError):
    """Raised when attempting to access a non-existent task."""


class TaskModel:
    """A simple model class for the state machine to bind to."""


class StateManager:
    """Manages loading, saving, and interacting with the Task HSM."""

    def __init__(self):
        self.state_file_path = settings.state_file

    def _load_state_file(self) -> StateFile:
        """Always load fresh state from disk to avoid caching issues."""
        if not self.state_file_path.exists():
            return StateFile()
        try:
            data = json.loads(self.state_file_path.read_text())
            return StateFile(**data)
        except (json.JSONDecodeError, FileNotFoundError):
            return StateFile()

    def _save_state_file(self, state: StateFile) -> None:
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_file_path.write_text(state.model_dump_json(indent=2))

    def get_machine(self, task_id: str) -> TaskModel | None:
        """Loads and returns the HSM for a specific task."""
        state_file = self._load_state_file()
        task_state = state_file.tasks.get(task_id)

        if not task_state:
            return None

        model = TaskModel()
        HierarchicalMachine(
            model=model,
            states=states,
            transitions=transitions,
            initial=task_state.current_state,
        )
        return model

    def create_machine(self, task_id: str) -> TaskModel:
        """Creates a new task and its HSM."""
        state_file = self._load_state_file()
        if task_id in state_file.tasks:
            raise TaskAlreadyExistsError

        task_state = TaskState(task_id=task_id, current_state=INITIAL_STATE)
        state_file.tasks[task_id] = task_state

        model = TaskModel()
        HierarchicalMachine(model=model, states=states, transitions=transitions, initial=INITIAL_STATE)
        self._save_state_file(state_file)

        return model

    def save_machine_state(self, task_id: str, model: TaskModel, feedback: str | None = None) -> None:
        """Saves the current state of a task's HSM."""
        state_file = self._load_state_file()
        task_state = state_file.tasks.get(task_id)

        if not task_state:
            raise TaskNotFoundError

        task_state.current_state = model.state
        task_state.revision_feedback = feedback

        state_file.tasks[task_id] = task_state
        self._save_state_file(state_file)

    def set_active_task(self, task_id: str) -> None:
        """Mark a task as active and deactivate all others."""
        state_file = self._load_state_file()
        if task_id not in state_file.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Deactivate all tasks
        for task in state_file.tasks.values():
            task.is_active = False

        # Activate the specified task
        state_file.tasks[task_id].is_active = True
        self._save_state_file(state_file)

    def get_active_task(self) -> str | None:
        """Get the currently active task ID, if any."""
        state_file = self._load_state_file()
        for task_id, task_state in state_file.tasks.items():
            if task_state.is_active:
                return task_id
        return None

    def deactivate_all_tasks(self) -> None:
        """Deactivate all tasks."""
        state_file = self._load_state_file()
        for task in state_file.tasks.values():
            task.is_active = False
        self._save_state_file(state_file)

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/progress_tools.py
```python
# File: src/epic_task_manager/tools/progress_tools.py

from pydantic import ValidationError

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.execution.exceptions import ArtifactNotFoundError, InvalidArtifactError
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models.artifacts import ExecutionPlanArtifact
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
prompter = Prompter()
artifact_manager = ArtifactManager()


async def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    """
    Marks a single step as complete, persists state, and returns the next step.
    This is the core checkpoint tool for resilient, multi-step phase execution.
    """
    if not settings.config_file.exists():
        return ToolResponse(status=STATUS_ERROR, message="Project not initialized.")

    model = state_manager.get_machine(task_id)
    if not model or getattr(model, "state", None) != "coding_working":
        current_state = "Not Found" if not model else getattr(model, "state", "Unknown")
        return ToolResponse(status=STATUS_ERROR, message=f"Invalid state: Tool can only be used in 'coding_working'. Current state: {current_state}")

    try:
        # --- START REFACTOR ---
        # REMOVE all old regex and parsing logic here.
        # REPLACE with direct JSON loading.

        # Load the execution plan DIRECTLY from the JSON artifact
        plan_data = artifact_manager.read_json_artifact(task_id, "planning")
        plan = ExecutionPlanArtifact(**plan_data)
        # --- END REFACTOR ---

        state_file = state_manager._load_state_file()
        task_state = state_file.tasks[task_id]

        # Validate step
        if task_state.current_step >= len(plan.execution_steps):
            return ToolResponse(status=STATUS_ERROR, message="All steps are already complete. You should call 'submit_for_review' now.")

        expected_step_id = plan.execution_steps[task_state.current_step].prompt_id
        if step_id != expected_step_id:
            return ToolResponse(status=STATUS_ERROR, message=f"Incorrect step ID. Expected '{expected_step_id}', but received '{step_id}'.")

        # Update state
        task_state.completed_steps.append(step_id)
        task_state.current_step += 1
        state_manager._save_state_file(state_file)

        # Check if all steps are complete
        if task_state.current_step == len(plan.execution_steps):
            next_prompt = (
                "# All Execution Steps Complete\n\n"
                "You have successfully executed all steps in the plan. The final action is to submit a lightweight completion manifest.\n\n"
                "Please call the `submit_for_review` tool now with the following structure:\n"
                '```json\n{\n  "implementation_summary": "string - High-level summary of what was implemented",\n  "execution_steps_completed": ["array of strings - should match the completed_steps list"],\n  "testing_notes": "string - Instructions for testing the implementation"\n}\n```'
            )
            message = f"Step '{step_id}' completed. All steps finished. Ready for final submission."
        else:
            # Generate prompt for the next step
            next_prompt = prompter.generate_prompt(task_id, getattr(model, "state", "coding_working"))
            message = f"Step '{step_id}' completed. Proceeding to next step."

        return ToolResponse(status=STATUS_SUCCESS, message=message, next_prompt=next_prompt)

    except (ArtifactNotFoundError, InvalidArtifactError, ValidationError, Exception) as e:
        return ToolResponse(status=STATUS_ERROR, message=f"An error occurred: {e}")

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/scaffolding/work.md
```markdown
# Role: Code Scaffolder

Your task is to scaffold the codebase for `{task_id}` by adding detailed TODO comments based on the execution plan from the planning phase.

**Your scaffolding MUST be based on the verified execution plan from the previous phase.**

---
**Verified Execution Plan (Source of Truth):**
```json
{verified_execution_plan_artifact}
```

## Instructions:

You must analyze the execution plan and create TODO comments in the appropriate files. Each execution step should be transcribed as a detailed TODO comment in the target files.

### TODO Comment Format Requirements:

Each TODO comment must include:
1. **Step ID**: The exact step ID from the execution plan (e.g., STEP-001, STEP-002)
2. **Instruction Text**: The complete instruction from the execution step
3. **File Context**: Clear indication of where the implementation should go

### Language-Specific Comment Syntax:

Use appropriate comment syntax for each file type:
- **Python (.py)**: `# TODO: [STEP-XXX] instruction text`
- **JavaScript/TypeScript (.js/.ts)**: `// TODO: [STEP-XXX] instruction text`
- **CSS (.css)**: `/* TODO: [STEP-XXX] instruction text */`
- **HTML (.html)**: `<!-- TODO: [STEP-XXX] instruction text -->`
- **Markdown (.md)**: `<!-- TODO: [STEP-XXX] instruction text -->`
- **JSON (.json)**: Add comments where possible, or create adjacent .md files
- **Other**: Use appropriate comment syntax for the language

### Example TODO Format:
```python
# TODO: [STEP-001] Add scaffolding_mode Feature Flag
# INSTRUCTION: Locate the FeatureFlags class in the file
#             Add a new boolean field named 'scaffolding_mode' with default=False
#             Add appropriate description: 'Enables an optional phase after planning...'
#             Follow existing field pattern using Field() with default and description parameters
class FeatureFlags(BaseModel):
    # ... existing fields ...
    pass  # Implementation will go here
```

### Scaffolding Process:

1. **Analyze Execution Steps**: Review each step in the execution plan
2. **Identify Target Files**: Determine which files need scaffolding based on step targets
3. **Create TODO Comments**: Add structured TODO comments to each target file
4. **Maintain File Structure**: Ensure all files remain syntactically valid
5. **Document Changes**: Track all files that were scaffolded

### Important Guidelines:

- **DO NOT implement actual code** - only add TODO comments
- **Preserve existing code** - do not modify or remove existing functionality
- **Maintain syntax validity** - ensure files can still be parsed/compiled
- **Be comprehensive** - include TODO comments for all execution steps
- **Use exact step IDs** - match the step IDs from the execution plan exactly

**Revision Feedback:** {revision_feedback}

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "files_scaffolded": ["array of file paths that were modified with TODO comments"]
}
```

**Example:**
```json
{
  "files_scaffolded": [
    "src/epic_task_manager/models/config.py",
    "src/epic_task_manager/models/artifacts.py",
    "src/epic_task_manager/state/machine.py"
  ]
}
```

**CRITICAL NOTES:**
- Use EXACTLY this field name: `files_scaffolded`
- Must be an array of strings (file paths)
- Include all files that were modified with TODO comments
- Use relative paths from the project root
- Do not include files that were not actually modified

Construct the complete scaffolding artifact and call the submit_for_review tool.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/gitsetup/work.md
```markdown
<role>
Interactive Git Branch Manager
</role>

<objective>
Establish proper git branch hygiene by ensuring the session is on a clean feature branch named `feature/{task_id}`. Your primary directive is to be **interactive**. If the repository is not in a perfect state, you must **stop, report to the user, and wait for their instructions.**
</objective>

<context name="Task and Guidelines">
## Task: {task_id} - Git Setup Phase

Your goal is to ensure we are on a clean feature branch named `feature/{task_id}`.

---
**Relevant Guidelines:**
```markdown
{guidelines}
```
---
</context>

<instructions>
## Interactive Workflow

Follow these steps in order.

### **Step 1: Check Repository Status**
Run the following commands to gather information:
1.  `git status --porcelain` (to check for uncommitted changes)
2.  `git branch --show-current` (to get the current branch name)

### **Step 2: Analyze Status and Act**
Analyze the information from Step 1 and choose one of the following paths.

#### **Path A: The Golden Path (Automatic Action)**
*   **IF AND ONLY IF:**
    *   `git status --porcelain` has **NO output** (the directory is clean),
    *   **AND** the current branch is `main` or `master`.
*   **THEN:**
    1.  Inform the user you are proceeding automatically.
    2.  Run `git checkout -b feature/{task_id}` to create and switch to the new branch.
    3.  **Proceed directly to Step 3.**

#### **Path B: The Interactive Loop (User Intervention Required)**
*   **IF the directory is dirty** (`git status --porcelain` has output):
    1.  **STOP.** Do not proceed.
    2.  Report the full output of `git status` to the user.
    3.  Politely ask them to clean the working directory (e.g., "Please commit or stash your changes and let me know when it's safe to proceed.").
    4.  After the user confirms they have fixed it, **you must return to Step 1** and re-run your checks to verify.

*   **IF the current branch is NOT `main`, `master`, or `feature/{task_id}`:**
    1.  **STOP.** Do not proceed.
    2.  Report the current branch name to the user (e.g., "You are currently on the branch `some-other-feature`. The target branch is `feature/{task_id}`.").
    3.  Ask for explicit instructions: "Should I create the new feature branch from here, or should you switch to `main` first?"
    4.  Wait for their decision before taking any action. If they tell you to proceed, you may create the branch. If they say they will fix it, wait for their confirmation then **return to Step 1** to re-run your checks.

### **Step 3: Submit Final Artifact**
*   **ONLY** submit this artifact once you have successfully reached a state where you are on the `feature/{task_id}` branch and the working directory is clean.
</instructions>

<required_artifact_structure>
**Required `work_artifact` Structure:**
```json
{
  "branch_name": "feature/{task_id}",
  "branch_created": "boolean - True if you created a new branch in this session, false if it already existed.",
  "branch_status": "clean",
  "ready_for_work": true
}
```
</required_artifact_structure>

<revision_feedback>
**Previous Revision Feedback:**
{revision_feedback}
</revision_feedback>

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/jira/sync.py
```python
"""
Jira synchronization utilities for mapping MCP phases to Jira statuses
"""

from __future__ import annotations

from epic_task_manager.models.enums import TaskPhase

from .schemas import JiraStatus


def get_suggested_jira_status(mcp_phase: TaskPhase) -> JiraStatus | None:
    """
    Determine what Jira status should be based on MCP phase.
    Returns the suggested Jira status, or None if no change recommended.

    This is for MVP - users manually update Jira based on these suggestions.
    """
    phase_to_jira: dict[TaskPhase, JiraStatus | None] = {
        TaskPhase.GATHER_REQUIREMENTS: None,  # Stay in TO DO
        TaskPhase.GIT_SETUP: None,  # Stay in TO DO
        TaskPhase.PLANNING: None,  # Stay in TO DO
        TaskPhase.SCAFFOLDING: None,  # Stay in TO DO
        TaskPhase.CODING: JiraStatus.IN_PROGRESS,  # First code work starts
        TaskPhase.TESTING: None,  # Stay in In Progress
        TaskPhase.FINALIZE: JiraStatus.CODE_REVIEW,  # Ready for team review
    }

    return phase_to_jira.get(mcp_phase)


def get_jira_phase_instructions(mcp_phase: TaskPhase) -> str:
    """
    Get developer-readable instructions for what to do in each phase,
    including Jira status updates.
    """
    instructions = {
        TaskPhase.GATHER_REQUIREMENTS: """
**Phase: Gather Requirements**
- Task has been fetched from Jira
- Review requirements and acceptance criteria
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.GIT_SETUP: """
**Phase: Git Setup**
- Setting up git environment for the task
- Creating feature branch
- Ensuring clean working directory
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.PLANNING: """
**Phase: Planning**
- Create implementation plan
- Identify files to modify/create
- Plan approach and architecture
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.SCAFFOLDING: """
**Phase: Scaffolding**
- Set up project structure and boilerplate
- Create necessary directories and basic files
- Prepare development environment
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.CODING: """
**Phase: Coding**
- Implement the planned solution
- Write/modify code
- **ACTION REQUIRED: Update Jira status to "In Progress"**
        """.strip(),
        TaskPhase.TESTING: """
**Phase: Testing**
- Test your implementation locally
- Review code quality and completeness
- Fix any issues found
- Jira Status: Keep as "In Progress"
        """.strip(),
        TaskPhase.FINALIZE: """
**Phase: Finalize**
- Code is complete and tested
- Ready to create pull request
- **ACTION REQUIRED: Create PR and update Jira status to "Code Review"**
        """.strip(),
    }

    return instructions.get(mcp_phase, "Unknown phase")


def format_jira_status_summary(mcp_phase: TaskPhase) -> str:
    """
    Format a summary showing MCP phase and suggested Jira action.
    """
    suggested_jira = get_suggested_jira_status(mcp_phase)

    status_line = f"**MCP Phase**: {mcp_phase.value}"

    if suggested_jira:
        status_line += f"  |  **Suggested Jira Status**: {suggested_jira.value}"

    return status_line

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/planning/solution_design_work.md
```markdown
<role>
Lead Software Architect (Solution Design Phase)
</role>

<objective>
Translate the approved strategy into a comprehensive file-by-file implementation plan for task `{task_id}`.
</objective>

<context name="Verified Requirements">
**Verified Requirements (Source of Truth):**
```markdown
{verified_gather_requirements_artifact}
```
</context>

<context name="Approved Strategy">
**Approved Strategy (Your Blueprint):**
```markdown
{approved_strategy_artifact}
```
</context>

<instructions>
## Instructions:

1. Review the approved strategy carefully.
2. Create a detailed technical design that implements the strategy.
3. Break down the implementation into specific file changes.
4. Ensure every component mentioned in the strategy is addressed.
5. If revision feedback is provided, address it specifically.

**CRITICAL NOTES:**
- Your design must fully implement the approved strategy
- Include ALL files that need to be changed
- Be specific about what changes will be made to each file
- Consider the order of implementation (some changes may depend on others)
- Ensure the design is complete and leaves no gaps

Construct the complete solution design artifact and call the `submit_for_review` tool with the result.
</instructions>

<required_artifact_structure>
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
</required_artifact_structure>

<revision_feedback>
**Revision Feedback:** {revision_feedback}
</revision_feedback>

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/client/implement_next_task.md
```markdown
# Role: The Epic Task Manager (ETM) Assistant

You are an expert AI pair programmer. Your primary function is to interact with the Epic Task Manager (ETM) server to drive software development tasks through a structured, professional workflow. You will translate the user's conversational requests into the appropriate ETM tool calls.

---
## Core Directive: The Server is the Orchestrator

Your behavior is dictated by a simple, elegant loop. You **must** follow it at all times.

1.  You will call an ETM tool, based on the user's request or the server's last instruction.
2.  You will receive a `ToolResponse` object from the ETM server.
3.  Your **next instruction** is always located in the `next_prompt` field of that response.
4.  You will then execute the content of that `next_prompt`.

**CRITICAL:** You do NOT need to remember the entire multi-phase workflow. The server manages the state and the workflow logic. Your only job is to faithfully execute the current `next_prompt` you receive. This makes you a stateless, efficient executor.

---
## Available Tools on the ETM Server

You have access to the following tools on the `epic-task-manager` server. The server will guide you on which ones to use via the `next_prompt`. You can obviously confirm this by using list tools.

*   `initialize_project`: Sets up the ETM workspace for a new project. This is the very first command to run.
*   `begin_or_resume_task`: Begins work on a new task or resumes a previously started task.
*   `submit_for_review`: Submits a completed work artifact for a given phase (e.g., planning, coding).
*   `approve_or_request_changes`: Used for AI self-review or to provide human feedback on an artifact.
*   `approve_and_advance`: The human-approval step to move from one major phase (like 'planning') to the next (like 'coding').
*   `get_task_summary`: A quick, lightweight tool to check the current status of a task.
*   `inspect_archived_artifact`: A tool to view the full content of a previously completed and archived phase artifact.

---
## Handling Errors

If any tool call returns a response with `status: 'error'`, do the following:
1.  **Do not** attempt to fix the problem yourself or try the command again.
2.  **Report** the `message` from the error response clearly to the user.
3.  **Wait** for the user to provide guidance.

---
## Initial Action

To begin, ask the user what they would like to do.

*   If they want to start work on a specific task, ask for the **task ID** (e.g., "IS-1234", "PROJ-456").
*   Once you have the task ID, your first action will be to call the `begin_or_resume_task` tool.
    *   **Example:** `mcp_epic-task-manager_begin_or_resume_task(task_id="IS-1234")`
*   If they are setting up a brand new project, they will likely ask you to initialize it. In that case, call the `initialize_project()` tool.

From that point on, simply follow the `next_prompt` you receive from the server.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/planning/execution_plan_work.md
```markdown
# Role: Lead Software Architect (Execution Plan Generation Phase)

You are in the **final stage** of planning for task `{task_id}`. Your sole objective is to mechanically translate an approved Solution Design into a series of precise, machine-executable **Execution Steps**.

The output of this phase will be the exact script that the next AI agent will use to write the code.

---
**Approved Solution Design (Your Implementation Plan):**
```markdown
{approved_solution_design_artifact}
```
---
**Previous Revision Feedback:** {revision_feedback}
---

## Instructions:

1.  Extract the `approved_design_summary` and `execution_order_notes` from the "Solution Design" artifact above. You will need to pass these through.
2.  Analyze the `file_breakdown` from the Solution Design. For each item in the breakdown, generate one complete `ExecutionStep` object.
3.  Combine these elements into the final artifact structure.

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object. This structure directly maps to the `ExecutionPlanArtifact` Pydantic model.

```json
{
  "approved_design_summary": "string - A brief summary of the approved solution design, carried over from the previous step.",
  "execution_steps": [
    {
      "prompt_id": "STEP-001",
      "prompt_text": "string - The first complete execution step instruction.",
      "target_files": ["string - A list of files affected."],
      "depends_on": []
    }
  ],
  "execution_order_notes": "string - Notes on the optimal execution order for the execution steps."
}
```

**Example of a complete ExecutionStep object:**

```json
{
  "prompt_id": "STEP-001",
  "prompt_text": "// --- Task: Add the StrategyArtifact Pydantic Model ---\n\nLOCATION: src/epic_task_manager/models/artifacts.py\nOPERATION: MODIFY\nSPECIFICATION:\n  - Append a new Pydantic model named 'StrategyArtifact' to the file.\n  - The model must have the following fields: 'metadata: ArtifactMetadata', 'high_level_strategy: str', 'key_components: List[str]', 'architectural_decisions: str', and 'risk_analysis: str'.\nTEST:\n  - After modification, the file must be valid Python code.\n  - An instance of the new 'StrategyArtifact' model must be creatable without errors.",
  "target_files": ["src/epic_task_manager/models/artifacts.py"],
  "depends_on": []
}
```

**CRITICAL NOTES:**
- The `execution_steps` field must be an array of ExecutionStep objects, not strings
- Each ExecutionStep object must have: `prompt_id`, `prompt_text`, `target_files`, and `depends_on`
- The `prompt_id` must follow the pattern "STEP-XXX" where XXX is a zero-padded number (e.g., STEP-001, STEP-002)
- This is a mechanical translation of the approved design. Do not add new features or logic.
- The `coding` phase will execute these steps verbatim. Clarity and precision are essential.

Construct the complete artifact and call the `submit_for_review` tool with the result.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/models/config.py
```python
"""
Configuration models for Epic Task Manager
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskSource(StrEnum):
    """Supported task management systems"""

    ATLASSIAN = "atlassian"
    LINEAR = "linear"
    LOCAL = "local"


class ConnectionMethod(StrEnum):
    """Connection methods for task sources"""

    API = "api"  # Direct API calls
    MCP = "mcp"  # MCP-based connections
    WEBHOOK = "webhook"  # Future webhook support


class JiraConfig(BaseModel):
    """Configuration for Jira integration"""

    cloud_id: str | None = None
    project_key: str | None = None
    default_issue_type: str = "Task"
    base_url: str | None = None
    connection_method: ConnectionMethod = ConnectionMethod.MCP


class LinearConfig(BaseModel):
    """Configuration for Linear integration"""

    team_id: str | None = None
    workspace: str | None = None
    default_state_id: str | None = None
    connection_method: ConnectionMethod = ConnectionMethod.MCP


class FeatureFlags(BaseModel):
    """Feature flags for Epic Task Manager"""

    auto_assign: bool = True
    auto_transition: bool = True
    smart_context: bool = True
    yolo_mode: bool = Field(default=False, description="Enables autonomous mode, where the AI automatically approves its own work and advances to the next phase without human intervention.")
    scaffolding_mode: bool = Field(default=False, description="Enables an optional phase after planning where the AI first scaffolds the codebase with TODO comments based on the execution plan.")


class TaskSourceConfig(BaseModel):
    """Task source specific configuration"""

    jira: JiraConfig | None = None
    linear: LinearConfig | None = None


class ProvidersConfig(BaseModel):
    """Provider configuration under new structure"""

    task_source: TaskSource = TaskSource.LOCAL
    task_source_config: TaskSourceConfig = Field(default_factory=TaskSourceConfig)


class EpicConfig(BaseModel):
    """Main configuration for Epic Task Manager"""

    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0"

    def get_active_config(self) -> JiraConfig | LinearConfig | None:
        """Get the configuration for the active task source"""
        if self.providers.task_source == TaskSource.ATLASSIAN:
            return self.providers.task_source_config.jira
        if self.providers.task_source == TaskSource.LINEAR:
            return self.providers.task_source_config.linear
        return None

    def get_task_source(self) -> TaskSource:
        """Get the current task source"""
        return self.providers.task_source

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/models/enums.py
```python
"""
Enums for Epic Task Manager
"""

from enum import Enum


class TaskPhase(str, Enum):
    """Valid task phases in the workflow"""

    GATHER_REQUIREMENTS = "gatherrequirements"
    GIT_SETUP = "gitsetup"
    PLANNING = "planning"
    SCAFFOLDING = "scaffolding"
    CODING = "coding"
    TESTING = "testing"
    FINALIZE = "finalize"


class TaskStateValue(str, Enum):
    """Complete task states including phases and substates"""

    # Gather requirements states
    GATHER_REQUIREMENTS_WORKING = "gatherrequirements_working"
    GATHER_REQUIREMENTS_DEV_REVIEW = "gatherrequirements_devreview"
    GATHER_REQUIREMENTS_VERIFIED = "gatherrequirements_verified"

    # Git setup states
    GIT_SETUP_WORKING = "gitsetup_working"
    GIT_SETUP_DEV_REVIEW = "gitsetup_devreview"
    GIT_SETUP_VERIFIED = "gitsetup_verified"

    # Planning states (three-stage workflow)
    PLANNING_STRATEGY = "planning_strategy"
    PLANNING_STRATEGY_DEV_REVIEW = "planning_strategydevreview"
    PLANNING_SOLUTION_DESIGN = "planning_solutiondesign"
    PLANNING_SOLUTION_DESIGN_DEV_REVIEW = "planning_solutiondesigndevreview"
    PLANNING_EXECUTION_PLAN = "planning_executionplan"
    PLANNING_EXECUTION_PLAN_DEV_REVIEW = "planning_executionplandevreview"
    PLANNING_VERIFIED = "planning_verified"

    # Scaffolding states
    SCAFFOLDING_WORKING = "scaffolding_working"
    SCAFFOLDING_AI_REVIEW = "scaffolding_aireview"
    SCAFFOLDING_DEV_REVIEW = "scaffolding_devreview"
    SCAFFOLDING_VERIFIED = "scaffolding_verified"

    # Coding states
    CODING_WORKING = "coding_working"
    CODING_DEV_REVIEW = "coding_devreview"
    CODING_VERIFIED = "coding_verified"

    # Testing states
    TESTING_WORKING = "testing_working"
    TESTING_DEV_REVIEW = "testing_devreview"
    TESTING_VERIFIED = "testing_verified"

    # Finalize states
    FINALIZE_WORKING = "finalize_working"
    FINALIZE_DEV_REVIEW = "finalize_devreview"
    FINALIZE_VERIFIED = "finalize_verified"

    # Final state
    DONE = "done"


class ArtifactStatus(str, Enum):
    """Status values for artifacts"""

    WORKING = "working"
    PENDING_DEVELOPER_REVIEW = "pending_human_review"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"


class FileAction(str, Enum):
    """File modification actions"""

    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/testing/work.md
```markdown
# Role: QA Engineer

Your task is to run the full project test suite for `{task_id}` and submit the test results.

**Your testing MUST validate the actual implemented code changes in the repository.**

## Instructions:

---
**Relevant Guidelines:**
```markdown
{guidelines}
```
---

1. Run the project's main test command: `uv run pytest -v` (using uv for proper dependency management)
2. Capture the complete test execution details:
   - The exact command that was run
   - The exit code (0 = success, non-zero = failure)
   - The full output from the test execution
3. Submit your results using the `submit_for_review` tool with a TestingArtifact containing:
   - test_results: A nested object with command_run, exit_code, and full_output
4. If revision feedback is provided, you must address it.

**Revision Feedback:** {revision_feedback}

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "test_results": {
    "command_run": "string - The exact test command that was executed",
    "exit_code": "integer - The exit code from test execution (0 = success, non-zero = failure)",
    "full_output": "string - Complete output from test execution including any error messages"
  }
}
```

**Example:**
```json
{
  "test_results": {
    "command_run": "uv run pytest -v",
    "exit_code": 0,
    "full_output": "====================== test session starts ======================\nplatform darwin -- Python 3.11.13, pytest-8.3.5\ncollected 10 items\n\ntests/test_example.py::test_function PASSED [100%]\n\n====================== 10 passed in 0.24s ======================"
  }
}
```

**CRITICAL NOTES:**
- Use EXACTLY this nested structure: `test_results` containing `command_run`, `exit_code`, `full_output`
- `exit_code` must be an integer (0 for success, non-zero for failure)
- `full_output` must contain the COMPLETE test output, including warnings and errors
- Run tests from the project root directory using `uv run pytest -v`
- Include all test output (both passing and failing tests)
- Do not modify any code - only run tests and report results
- If tests fail, capture the failure details in the full_output

## Testing Process:

1. Run tests from the project root directory
2. Include all test output (both passing and failing tests)
3. Do not modify any code - only run tests and report results
4. If tests fail, capture the failure details in the full_output
5. Report the exact command used and exit code received

Construct the complete testing artifact and call the submit_for_review tool.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/review_tools.py
```python
# File: src/epic_task_manager/tools/review_tools.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
prompter = Prompter()


async def approve_or_request_changes(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """The single tool for all reviews (AI and Developer)."""

    if not settings.config_file.exists():
        return ToolResponse(
            status=STATUS_ERROR,
            message="Project not initialized. Please run the 'initialize_project' tool first.",
        )

    model = state_manager.get_machine(task_id)
    if not model:
        return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

    current_state = model.state
    trigger_attempted = ""
    try:
        if is_approved:
            if model.state.endswith("_aireview"):
                trigger_attempted = "ai_approves"
                model.ai_approves()
            elif model.state in ["planning_strategydevreview", "planning_solutiondesigndevreview", "planning_executionplandevreview"]:
                trigger_attempted = "human_approves"
                model.human_approves()
            else:
                return ToolResponse(
                    status=STATUS_ERROR,
                    message=f"Human approval from state '{current_state}' must be done via the 'approve_and_advance' tool.",
                )
        else:
            trigger_attempted = "request_revision"
            model.request_revision()

        state_manager.save_machine_state(task_id, model, feedback=feedback_notes)

        prompt = prompter.generate_prompt(task_id, model.state, revision_feedback=feedback_notes)

        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Review feedback submitted. State transitioned from '{current_state}' to '{model.state}'.",
            next_prompt=prompt,
        )
    except Exception as e:
        # A bit of a hack to get the underlying error from the transitions library
        if "Can't trigger event" in str(e):
            return ToolResponse(
                status=STATUS_ERROR,
                message=f"Invalid action from state '{current_state}'.",
                data={"error_details": {"type": "StateTransitionError", "current_state": current_state, "attempted_transition": trigger_attempted, "message": str(e)}},
            )
        return ToolResponse(status=STATUS_ERROR, message=f"Could not process feedback from state '{current_state}'. Error: {e}", data={"error_details": {"type": type(e).__name__, "message": str(e)}})

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/config/settings.py
```python
"""
Configuration settings for Epic Task Manager using pydantic_settings
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from epic_task_manager.constants import TASKS_INBOX_DIR_NAME, WORKSPACE_DIR_NAME


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_prefix="EPIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Allow extra environment variables without errors
    )

    # Credential environment variables
    jira_api_token: str | None = None
    jira_user_email: str | None = None
    linear_api_key: str | None = None

    # Server configuration
    server_name: str = "epic-task-manager"
    version: str = "0.2.0"

    # Directory configuration
    epic_task_manager_dir_name: str = ".epictaskmanager"
    contexts_subdir: str = "contexts"
    state_filename: str = "state.json"
    config_filename: str = "config.json"

    # Base paths
    project_root: Path = Path.cwd()

    @property
    def templates_dir(self) -> Path:
        """Get the templates directory path"""
        return Path(__file__).parent.parent / "templates"

    @property
    def epic_task_manager_dir(self) -> Path:
        """Get the epic directory path"""
        return self.project_root / self.epic_task_manager_dir_name

    @property
    def contexts_dir(self) -> Path:
        """Get the contexts directory path"""
        return self.epic_task_manager_dir / self.contexts_subdir

    @property
    def state_file(self) -> Path:
        """Get the state file path"""
        return self.epic_task_manager_dir / self.state_filename

    @property
    def config_file(self) -> Path:
        """Get the config.json file path"""
        return self.epic_task_manager_dir / self.config_filename

    @property
    def workspace_dir(self) -> Path:
        """Get the workspace directory path (replaces old tasks directory)"""
        return self.epic_task_manager_dir / WORKSPACE_DIR_NAME

    @property
    def tasks_inbox_dir(self) -> Path:
        """Get the tasks inbox directory path for local markdown files"""
        return self.epic_task_manager_dir / TASKS_INBOX_DIR_NAME

    @property
    def prompts_dir(self) -> Path:
        """Get the prompts directory path for local template customization"""
        return self.epic_task_manager_dir / "prompts"


# Global settings instance
settings = Settings()

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/management_tools.py
```python
# File: src/epic_task_manager/tools/management_tools.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
prompter = Prompter()


async def inspect_and_manage_task(task_id: str, force_transition: str | None = None) -> ToolResponse:
    """
    Inspects a task's state and valid triggers, or forces a state transition.
    This is a powerful tool for recovering stuck tasks.
    """
    if not settings.config_file.exists():
        return ToolResponse(status=STATUS_ERROR, message="Project not initialized.")

    model = state_manager.get_machine(task_id)
    if not model:
        return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

    current_state = model.state

    # --- CORRECTED LOGIC ---
    # Use the library's built-in method to get a list of valid triggers for the current state.
    valid_trigger_names = model.get_triggers(current_state)
    # --- END CORRECTION ---

    if force_transition is None:
        # --- Inspection Mode ---
        data = {
            "task_id": task_id,
            "current_state": current_state,
            "valid_triggers": valid_trigger_names,
        }
        message = "Task state inspected. See data for available triggers."
        return ToolResponse(status=STATUS_SUCCESS, message=message, data=data)
    # --- Management (Force Transition) Mode ---
    if force_transition not in valid_trigger_names:
        error_message = f"Invalid transition '{force_transition}' from state '{current_state}'. Valid triggers are: {valid_trigger_names}"
        return ToolResponse(status=STATUS_ERROR, message=error_message)

    try:
        # Dynamically call the trigger method on the model (e.g., model.advance())
        trigger_func = getattr(model, force_transition)
        trigger_func()

        # Persist the new state
        state_manager.save_machine_state(task_id, model)

        # Get the prompt for the new state
        next_prompt = prompter.generate_prompt(task_id, model.state)

        message = f"Successfully forced transition '{force_transition}'. Task '{task_id}' is now in state '{model.state}'."
        return ToolResponse(status=STATUS_SUCCESS, message=message, next_prompt=next_prompt)

    except Exception as e:
        # Catch any other errors during the transition process
        return ToolResponse(
            status=STATUS_ERROR,
            message=f"Failed to force transition '{force_transition}': {e}",
        )

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/planning/strategy_work.md
```markdown
# Role: Lead Software Architect (Strategy Phase)

You are developing the high-level strategic plan for task `{task_id}`.

**Your objective is to create a strategic architectural vision that will guide the detailed implementation.**

---
**Verified Requirements (Source of Truth):**
```markdown
{verified_gatherrequirements_artifact}
```

---

## Instructions:

1. Analyze the verified requirements thoroughly.
2. Develop a high-level strategic approach for implementation.
3. Focus on architectural decisions, component design, and risk mitigation.
4. If revision feedback is provided, address it specifically.

**Revision Feedback:** {revision_feedback}

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "high_level_strategy": "string - Overall approach and strategic decisions for implementation",
  "key_components": ["string - List of major components or modules to be implemented"],
  "architectural_decisions": "string - Key architectural choices and rationale",
  "risk_analysis": "string - Potential risks and mitigation strategies"
}
```

**Example:**
```json
{
  "high_level_strategy": "Implement a modular three-stage planning workflow using the existing hierarchical state machine. Each stage will have its own work/review cycle, with human approval gates between stages to ensure quality and alignment.",
  "key_components": [
    "Strategy Phase - High-level architectural planning",
    "Solution Design Phase - Detailed file-by-file breakdown",
    "Execution Plan Phase - Machine-executable task list",
    "Enhanced Prompter - Context-aware prompt generation",
    "Artifact Models - Structured data models for each stage"
  ],
  "architectural_decisions": "1. Leverage existing HSM infrastructure: Extend the current state machine rather than creating a new one. 2. Use composition pattern: Each planning sub-stage will compose into the overall planning phase. 3. Context propagation: Each stage will receive the approved artifact from the previous stage as context.",
  "risk_analysis": "Risks: 1. State explosion - Mitigated by reusing existing review patterns. 2. Context size - Mitigated by only passing approved artifacts forward. 3. Complexity - Mitigated by clear separation of concerns between stages."
}
```

**CRITICAL NOTES:**
- Focus on HIGH-LEVEL strategy, not implementation details
- Consider architectural patterns, design principles, and best practices
- Think about maintainability, extensibility, and testability
- Address all aspects of the requirements but at a strategic level
- Your strategy will guide the detailed design in the next phase

Construct the complete strategy artifact and call the `submit_for_review` tool with the result.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/get_active_task.py
```python
# src/epic_task_manager/tools/get_active_task.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager


async def get_active_task() -> ToolResponse:
    """
    Gets the currently active task. If the active task is complete, it instructs
    the client to find the next available task.
    """
    if not settings.config_file.exists():
        return ToolResponse(status=STATUS_ERROR, message="Project not initialized. Please run 'initialize_project' first.")

    state_manager = StateManager()
    active_task_id = state_manager.get_active_task()

    if not active_task_id:
        # No active task exists. The correct next action is to find one.
        return ToolResponse(
            status=STATUS_SUCCESS,
            message="No active task found.",
            data={"active_task_id": None},
            next_prompt=(
                "<objective>Inform the user there is no active task and find available work.</objective>\n"
                "<instructions>Call the `list_available_tasks` tool to discover what to work on.</instructions>"
            ),
        )

    # An active task exists, we must check its state.
    machine = state_manager.get_machine(active_task_id)

    if machine and machine.state == "done":
        # The active task is complete. It should not be worked on. Find the next one.
        state_manager.deactivate_all_tasks()  # Clean up the invalid active state.
        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Active task {active_task_id} is already complete.",
            data={"active_task_id": active_task_id, "status": "done"},
            next_prompt=(
                "<objective>Inform the user the active task is complete and find the next one.</objective>\n"
                f"<instructions>1. Report to the user that task '{active_task_id}' is done.\n"
                "2. Call the `list_available_tasks` tool to discover what to work on next.</instructions>"
            ),
        )

    # The active task exists and is not done. Return its ID for work to be resumed.
    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Active task is {active_task_id}.",
        data={"active_task_id": active_task_id},
        next_prompt=(
            "<objective>Resume work on the active task.</objective>\n"
            f"<instructions>An active task, '{active_task_id}', was found. Call `begin_or_resume_task` to continue working on it.</instructions>"
        ),
    )

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/finalize/work.md
```markdown
# Role: DevOps Engineer

Your task is to finalize the implementation for `{task_id}` by executing the complete git workflow to push changes and create a Pull Request.

**Your finalization MUST be based on the verified test results from the previous phase.**

---
**Verified Test Results (Source of Truth):**
```markdown
{verified_testing_artifact}
```

## Instructions:

You must execute the following git workflow sequence in order and capture the outputs:

### Step 1: Stage All Changes
```bash
git add .
```

### Step 2: Create Commit with Structured Message
```bash
git commit -m "[{task_id}] <descriptive commit message based on Jira summary>"
```
- Use the Jira task summary to create a meaningful commit message
- Include the task ID in brackets at the beginning

### Step 3: Push Feature Branch to Remote
```bash
git push origin <current_branch_name>
```
- Use the actual current branch name (get it with `git branch --show-current`)

### Step 4: Create Pull Request
```bash
gh pr create --title "[{task_id}] <title from Jira>" --body "<description from Jira acceptance criteria>"
```
- Use the Jira summary as the PR title
- Use the acceptance criteria as the PR body
- This command will return the Pull Request URL

### Step 5: Capture Results
After executing all commands, capture:
1. **Commit Hash**: From the commit command output or `git rev-parse HEAD`
2. **Pull Request URL**: From the `gh pr create` command output

**Revision Feedback:** {revision_feedback}

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "commit_hash": "string - The git commit hash from the final commit",
  "pull_request_url": "string - The complete URL of the created pull request"
}
```

**Example:**
```json
{
  "commit_hash": "a1b2c3d4e5f6789012345678901234567890abcd",
  "pull_request_url": "https://github.com/owner/repo/pull/123"
}
```

**CRITICAL NOTES:**
- Use EXACTLY these field names: `commit_hash`, `pull_request_url`
- Both fields must be non-empty strings
- The commit hash should be the full 40-character SHA
- The pull request URL must be a complete, valid URL
- Capture the actual outputs, don't fabricate values

Construct the complete finalize artifact and call the submit_for_review tool.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/scaffolding/ai_review.md
```markdown
# Role: Scaffolding QA Inspector

You are performing a scaffolding validation review for task `{task_id}`.

**Artifact to Review:**
```markdown
{artifact_content}
```

## Review Criteria:

1. **Files Scaffolded List**: Does the manifest include a comprehensive list of files that were modified with TODO comments?
2. **File Path Accuracy**: Are all file paths valid and correctly formatted (relative to project root)?
3. **Completeness**: Does the list appear to cover all files that should have been scaffolded based on the execution plan?

## Review Standards:

**APPROVE (is_approved=True) when:**
- Files scaffolded list is populated with actual file paths
- All file paths are valid and follow consistent formatting
- The number of files appears reasonable for the execution plan scope
- No obvious missing files that should have been scaffolded
- Manifest structure is complete and properly formatted

**REJECT (is_approved=False) when:**
- Files scaffolded list is empty or missing
- File paths are invalid or incorrectly formatted
- List appears incomplete compared to execution plan scope
- Contains placeholder or dummy values instead of actual file paths
- Manifest structure is malformed or incomplete

## Validation Checklist:

### ✅ Manifest Structure
- [ ] **Files List Present**: `files_scaffolded` field is populated
- [ ] **Valid Array**: Field contains an array of strings
- [ ] **Non-Empty**: At least one file path is included
- [ ] **No Placeholders**: Contains actual file paths, not examples

### ✅ File Path Validation
- [ ] **Path Format**: All paths use forward slashes and relative format
- [ ] **File Extensions**: Paths include appropriate file extensions
- [ ] **No Duplicates**: No duplicate file paths in the list
- [ ] **Realistic Paths**: Paths appear to be actual project files

### ✅ Scope Validation
- [ ] **Comprehensive Coverage**: List appears to cover expected scope
- [ ] **Reasonable Size**: Number of files aligns with execution plan complexity
- [ ] **No Missing Core Files**: Key files that need scaffolding are included

## Required Action:

Call `approve_or_request_changes` with:
- `is_approved`: true if scaffolding manifest validation passes, false otherwise
- `feedback_notes`: Specific feedback on completeness, file path accuracy, and any missing elements

Focus on manifest validation and scaffolding completeness. This review ensures the TODO comments were properly added to the appropriate files before advancing to the coding phase.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/gatherrequirements/local_work.md
```markdown
<role>
Requirements Gathering Assistant (Local Files)
</role>

<objective>Gather and analyze requirements from a local task file by reading task details from a markdown file in the tasks inbox directory and extracting key information needed for implementation planning.</objective>

<context name="Task Information">
Please gather requirements for task **{task_id}** from the local tasks directory and extract the essential information.
</context>

<instructions>
## Required Actions

1. **Read Task File**: Use file reading tools to access the task file at `.epictaskmanager/tasks/{task_id}.md` (or handle the case where the task_id already includes the .md extension).

2. **Parse Markdown Content**: Extract information from the markdown file structure:
   - **Title**: From the main heading (# Title) or filename
   - **Description**: Content under "## Description" section
   - **Acceptance Criteria**: Items listed under "## Acceptance Criteria" section

3. **Structure the Information**: Organize the extracted information into a clear, well-formatted work artifact.

## File Reading Guidelines

- Use the `Read` tool or similar file reading capabilities to access the task file
- Handle both `{task_id}` and `{task_id}.md` filename formats
- If the file doesn't exist, provide a clear error message
- Parse markdown structure carefully to extract the right content sections

## Expected Markdown Structure

```markdown
# Task Title

## Description
Detailed description of what needs to be done.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Additional Notes
Optional additional context.
```

## Guidelines

- Be thorough in extracting ALL relevant information from the task file
- Clean up any markdown formatting artifacts (like checkbox syntax)
- Ensure acceptance criteria are complete and actionable
- If any sections are missing, note this in your artifact

---

Once you have gathered all the task information from the local file, call the `submit_for_review` tool with your complete work artifact containing the task_summary, task_description, and acceptance_criteria.
</instructions>

<required_artifact_structure>
Your work artifact MUST contain these exact keys:
- `task_summary`: String - the task title
- `task_description`: String - the complete task description
- `acceptance_criteria`: Array of strings - each acceptance criteria as a separate array item
</required_artifact_structure>

<revision_feedback>
{revision_feedback}
</revision_feedback>

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/inspect_archived_artifact.py
```python
# File: src/epic_task_manager/tools/inspect_archived_artifact.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.exceptions import TaskNotFoundError
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager


async def inspect_archived_artifact(task_id: str, phase_name: str) -> ToolResponse:
    """Get the content of an archived artifact for a completed phase."""
    if not settings.config_file.exists():
        return ToolResponse(
            status=STATUS_ERROR,
            message="Project not initialized. Please run the 'initialize_project' tool first.",
        )

    try:
        state_manager = StateManager()
        artifact_manager = ArtifactManager()

        if not state_manager.get_machine(task_id):
            return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

        valid_phases = ["gatherrequirements", "planning", "coding", "testing", "finalize"]
        if phase_name not in valid_phases:
            return ToolResponse(
                status=STATUS_ERROR,
                message=f"Invalid phase_name '{phase_name}'. Must be one of: {', '.join(valid_phases)}",
            )

        archive_path = artifact_manager.get_archive_path(task_id, phase_name, 1)

        if not archive_path.exists():
            return ToolResponse(
                status=STATUS_ERROR,
                message=f"No archived artifact found for task {task_id} phase '{phase_name}'. The phase may not have been completed yet.",
            )

        artifact_content = archive_path.read_text(encoding="utf-8")

        response_data = {
            "task_id": task_id,
            "phase_name": phase_name,
            "artifact_content": artifact_content,
        }

        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Archived artifact for phase '{phase_name}' retrieved.",
            data=response_data,
        )

    except (TaskNotFoundError, FileNotFoundError, PermissionError) as e:
        return ToolResponse(
            status=STATUS_ERROR,
            message=f"Failed to inspect archived artifact: {e!s}",
        )

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/finalize/ai_review.md
```markdown
# Role: QA Reviewer - Git Workflow Validation

Please review the finalize artifact for task `{task_id}` to ensure the git workflow was completed successfully.

**Artifact to Review:**
```markdown
{artifact_content}
```

## Validation Checklist:

### ✅ Commit Hash Validation
- [ ] **Format**: Commit hash is exactly 40 characters long
- [ ] **Characters**: Contains only valid hexadecimal characters (0-9, a-f)
- [ ] **Not Empty**: Field is populated with actual hash value
- [ ] **Not Placeholder**: Not a dummy/example value

### ✅ Pull Request URL Validation
- [ ] **Format**: Valid URL format starting with https://
- [ ] **GitHub**: Points to GitHub repository (github.com domain)
- [ ] **Path Structure**: Follows pattern `/owner/repo/pull/number`
- [ ] **Not Empty**: Field is populated with actual URL
- [ ] **Not Placeholder**: Not a dummy/example value

### ✅ Workflow Completion
- [ ] **Both Fields Present**: Both commit_hash and pull_request_url are provided
- [ ] **Realistic Values**: Values appear to be actual git/GitHub outputs
- [ ] **Consistency**: Task ID referenced in commit/PR aligns with current task

## Review Decision:

**APPROVE** if:
- Commit hash is valid 40-character SHA
- Pull request URL is properly formatted GitHub URL
- Both fields contain real values (not placeholders)
- Workflow appears to have completed successfully

**REQUEST REVISION** if:
- Either field is missing, empty, or contains placeholder values
- Commit hash format is invalid (wrong length, invalid characters)
- Pull request URL is malformed or not a GitHub URL
- Values appear to be fabricated rather than actual command outputs

## Instructions:

Call the `approve_or_request_changes` tool with:
- `is_approved: true` if all validations pass
- `is_approved: false` with specific `feedback_notes` if any issues are found

Focus on technical validation of the git workflow outputs rather than code quality.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/get_task_summary.py
```python
# File: src/epic_task_manager/tools/get_task_summary.py

import json

import yaml

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.exceptions import StateFileError, TaskNotFoundError
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager


async def get_task_summary(task_id: str) -> ToolResponse:
    """Get a lightweight summary of a task's current status."""
    if not settings.config_file.exists():
        return ToolResponse(
            status=STATUS_ERROR,
            message="Project not initialized. Please run the 'initialize_project' tool first.",
        )

    try:
        state_manager = StateManager()
        artifact_manager = ArtifactManager()

        model = state_manager.get_machine(task_id)
        if not model:
            return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

        current_state = model.state
        artifact_status = "unknown"
        try:
            artifact_content = artifact_manager.read_artifact(task_id)
            if artifact_content:
                metadata, _ = artifact_manager.parse_artifact(artifact_content)
                artifact_status = metadata.get("status", "unknown")
            else:
                artifact_status = "missing"
        except (yaml.YAMLError, json.JSONDecodeError, UnicodeDecodeError):
            artifact_status = "invalid_format"

        summary_data = {
            "task_id": task_id,
            "current_state": current_state,
            "artifact_status": artifact_status,
            "is_active": state_manager.get_active_task() == task_id,
        }

        return ToolResponse(
            status=STATUS_SUCCESS,
            message="Task summary retrieved successfully.",
            data=summary_data,
        )

    except (TaskNotFoundError, StateFileError, FileNotFoundError, PermissionError) as e:
        return ToolResponse(status=STATUS_ERROR, message=f"Failed to get task summary: {e!s}")

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/execution/constants.py
```python
"""Constants for the execution module."""

# Archive filename format
ARCHIVE_FILENAME_FORMAT = "{phase_number:02d}-{phase_name}.md"


# Error messages
ERROR_VERIFIED_ARTIFACT_NOT_FOUND = "Error: Could not find verified {phase} artifact."
ERROR_APPROVED_ARTIFACT_NOT_FOUND = "Error: Could not find approved {artifact_type} artifact."
ERROR_SECTION_NOT_FOUND = "Error: Could not find '{section_title}' section in scratchpad."

# Template types
TEMPLATE_TYPE_PROMPTS = "prompts"
TEMPLATE_TYPE_ARTIFACTS = "artifacts"

# Template suffixes
TEMPLATE_SUFFIX_WORK = "work"
TEMPLATE_SUFFIX_AI_REVIEW = "ai_review"
TEMPLATE_SUFFIX_SOLUTION_DESIGN = "solution_design_work"
TEMPLATE_SUFFIX_EXECUTION_PLAN = "execution_plan_work"
TEMPLATE_SUFFIX_STRATEGY = "strategy_work"

# Workflow stages
WORKFLOW_STAGE_WORKING = "working"
WORKFLOW_STAGE_AI_REVIEW = "aireview"
WORKFLOW_STAGE_DEV_REVIEW = "devreview"
WORKFLOW_STAGE_STRATEGY = "strategy"
WORKFLOW_STAGE_SOLUTION_DESIGN = "solutiondesign"
WORKFLOW_STAGE_EXECUTION_PLAN = "executionplan"
WORKFLOW_STAGE_VERIFIED = "verified"

# Planning sub-stage review states
PLANNING_SUB_REVIEW_STATES = ["strategydevreview", "solutiondesigndevreview", "executionplandevreview"]

# Phase names
PHASE_REQUIREMENTS = "gatherrequirements"
PHASE_GITSETUP = "gitsetup"
PHASE_PLANNING = "planning"
PHASE_CODING = "coding"
PHASE_TESTING = "testing"
PHASE_FINALIZE = "finalize"

# Task source specific
TASK_SOURCE_GENERIC = "generic"

# Section titles
SECTION_PLANNING_STRATEGY = "Planning Strategy"
SECTION_SOLUTION_DESIGN = "Solution Design"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/gatherrequirements/linear_work.md
```markdown
<role>
Requirements Gathering Assistant (Linear Integration)
</role>

<objective>Gather and analyze requirements from a Linear task by fetching task details using Linear MCP tools and extracting key information needed for implementation planning.</objective>

<context name="Task Information">
Please gather requirements for task **{task_id}** and extract the essential information.
</context>

<instructions>
## Required Actions

1. **Fetch Linear Task Details**: Use the `mcp_linear_get_issue` tool to retrieve the complete task information from Linear.

2. **Extract Key Information**: From the Linear response, extract:
   - **Title**: The exact title from Linear
   - **Description**: The complete description including any user stories, background context, and technical details
   - **Acceptance Criteria**: All acceptance criteria listed in the task (these define what constitutes completion)

3. **Structure the Information**: Organize the extracted information into a clear, well-formatted work artifact.

## Tools Available

- `mcp_linear_get_issue`: Retrieve issue details by ID
- Other Linear MCP tools as needed

## Guidelines

- Be thorough in extracting ALL relevant information from the Linear task
- Preserve the original formatting and structure of descriptions
- Ensure acceptance criteria are complete and actionable
- If any information is missing or unclear, note this in your artifact

---

Once you have gathered all the task information, call the `submit_for_review` tool with your complete work artifact containing the task_summary, task_description, and acceptance_criteria.
</instructions>

<required_artifact_structure>
Your work artifact MUST contain these exact keys:
- `task_summary`: String - the exact task title from Linear
- `task_description`: String - the complete task description
- `acceptance_criteria`: Array of strings - each acceptance criteria as a separate array item
</required_artifact_structure>

<revision_feedback>
{revision_feedback}
</revision_feedback>

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/testing/ai_review.md
```markdown
# Role: QA Reviewer (Testing Phase)

You are performing a test result review for task `{task_id}`.

**Artifact to Review:**
```markdown
{artifact_content}
```

## Review Instructions:

1. **Examine the test execution results** in the artifact above
2. **Check the exit_code field** - this is the critical success indicator:
   - exit_code = 0: Tests passed successfully
   - exit_code ≠ 0: Tests failed (any non-zero value indicates failure)
3. **Review the full_output** for any error messages, failed test details, or warnings
4. **Apply Automatic Review Rules:**
   - If exit_code is NOT 0: MUST set is_approved=False (triggers test-fix loop)
   - If exit_code is 0: Review output for concerning issues, usually approve

## Decision Examples:

**REJECT (is_approved=False) when:**
```json
{
  "command_run": "uv run pytest -v",
  "exit_code": 1,  // Non-zero = failure
  "full_output": "...FAILED tests/test_example.py::test_function..."
}
```

**APPROVE (is_approved=True) when:**
```json
{
  "command_run": "uv run pytest -v",
  "exit_code": 0,  // Zero = success
  "full_output": "...10 passed in 0.24s..."
}
```

## Required Action:

Call `approve_or_request_changes` with:
- `is_approved`: true if exit_code=0 AND no critical issues, false otherwise
- `feedback_notes`: Clear explanation of your decision

**CRITICAL:** Failed tests (exit_code ≠ 0) MUST be rejected to trigger the test-fix loop, routing back to coding phase for fixes. This is the core quality gate functionality.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/gatherrequirements/generic_work.md
```markdown
<role>
Business Analyst
</role>

<objective>Gather and structure the requirements for `{task_id}` from the provided task information.</objective>

<context name="Source Information">
{jira_ticket_info}
</context>

<instructions>
1. Extract the key information from the task
2. Structure the requirements clearly for the development team
3. If revision feedback is provided, you must address it.

## Guidelines

Extract all relevant information from the task and construct the complete requirements artifact. Call the `submit_for_review` tool with the result.
</instructions>

<required_artifact_structure>
You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "task_summary": "string - The exact summary/title from the task",
  "task_description": "string - The complete description from the task",
  "acceptance_criteria": ["array of strings - Each acceptance criterion as a separate string"]
}
```

**Example:**
```json
{
  "task_summary": "[WORKFLOW] Implement 'testing' Phase",
  "task_description": "Add testing phase as quality gate after coding phase...",
  "acceptance_criteria": [
    "Add new 'testing' parent state to state machine",
    "Update Prompter to handle testing_working state",
    "Create TestingArtifact Pydantic model"
  ]
}
```

**CRITICAL NOTES:**
- Use EXACTLY these field names: `task_summary`, `task_description`, `acceptance_criteria`
- `acceptance_criteria` must be an array of strings, not a single string
- Include the complete task description, not a summary
- Extract ALL acceptance criteria from the task
</required_artifact_structure>

<revision_feedback>
{revision_feedback}
</revision_feedback>

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/constants.py
```python
"""
Constants for Epic Task Manager
"""

# Phase numbering for archives
PHASE_NUMBERS = {
    "gatherrequirements": 1,
    "gitsetup": 2,
    "planning": 3,
    "scaffolding": 4,
    "coding": 5,
    "testing": 6,
    "finalize": 7,
}

# State transition triggers
ADVANCE_TRIGGERS = {
    "gatherrequirements_verified": "advance",
    "gitsetup_verified": "advance",
    "planning_verified": "advance_to_code",  # Will be overridden by conditional logic
    "scaffolding_verified": "advance_from_scaffold",
    "coding_verified": "advance",
    "testing_verified": "advance",
    "finalize_verified": "advance",
    # Planning substage devreview states use human_approves trigger
    "planning_strategydevreview": "human_approves",
    "planning_solutiondesigndevreview": "human_approves",
    "planning_executionplandevreview": "human_approves",
}

# Default values
DEFAULT_AI_MODEL = "claude-3.5-sonnet"
DEFAULT_ARTIFACT_VERSION = "1.0"

# File patterns
ARTIFACT_FILENAME = "scratchpad.md"
ARCHIVE_DIR_NAME = "archive"
WORKSPACE_DIR_NAME = "workspace"
TASKS_INBOX_DIR_NAME = "tasks"

# Response status values
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/coding/ai_review.md
```markdown
# Role: Completion Manifest Reviewer

You are performing a manifest validation review for task `{task_id}`.

**Artifact to Review:**
```markdown
{artifact_content}
```

## Review Criteria:

1. **Implementation Summary**: Is it accurate and complete? Does it reflect what was actually accomplished?
2. **Execution Steps Completed**: Does the list of completed execution steps match the planning scope? Are all required steps accounted for?
3. **Testing Notes**: Are the testing instructions sufficient for the next phase? Do they provide clear guidance for validation?

## Review Standards:

**APPROVE (is_approved=True) when:**
- Implementation summary accurately reflects the work done
- All planned execution steps are properly tracked as completed
- Testing notes provide clear validation instructions
- Completion manifest is consistent and complete

**REJECT (is_approved=False) when:**
- Implementation summary is vague or inaccurate
- Missing execution steps from the completion list
- Testing notes are inadequate or unclear
- Manifest appears incomplete or inconsistent

## Required Action:

Call `approve_or_request_changes` with:
- `is_approved`: true if manifest validation passes, false otherwise
- `feedback_notes`: Specific feedback on completeness, accuracy, and any missing elements

Focus on manifest validation, completion tracking, and testing adequacy. This is NOT a code review - the code review happens via git diff in the IDE before human approval.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/models/core.py
```python
# File: src/epic_task_manager/models/core.py

# Standard library imports
from typing import Any

# Third-party imports
from pydantic import BaseModel, Field

# Local application imports
# (none needed)


class TaskState(BaseModel):
    """Represents the persisted state of a single task"""

    task_id: str
    current_state: str
    # We will store the full state dictionary from the 'transitions' library
    machine_state: dict[str, Any] = Field(default_factory=dict)
    # Stores feedback notes during revision loops
    revision_feedback: str | None = None
    # Tracks if this task is currently active
    is_active: bool = Field(default=False)
    # The index of the next execution step to be processed in a multi-step phase
    current_step: int = Field(default=0, description="The index of the next execution step to be processed in a multi-step phase.")
    # A list of completed step IDs for the current phase
    completed_steps: list[str] = Field(default_factory=list, description="A list of completed step IDs for the current phase.")


class StateFile(BaseModel):
    """Represents the root state.json file"""

    tasks: dict[str, TaskState] = Field(default_factory=dict)

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/gitsetup/ai_review.md
```markdown
# Role: QA Reviewer - Git Setup Validation

You are reviewing the git setup artifact for task `{task_id}` to ensure it is safe to proceed with development.

**Artifact to Review:**
```markdown
{artifact_content}
```

## Review Criteria:

Your primary responsibility is to enforce safety and correctness based on this **final artifact**.

1.  **`ready_for_work` MUST be `true`:** This is a non-negotiable, hard requirement.
2.  **`branch_name` MUST be `feature/{task_id}`:** The branch name must follow the exact convention.
3.  **`branch_status` MUST be `"clean"`:** No other status is acceptable in the final artifact.

## Review Standards:

**APPROVE (`is_approved=True`) ONLY when ALL of the following are met:**
- `ready_for_work` is `true`.
- `branch_name` is exactly `feature/{task_id}`.
- `branch_status` is the string `"clean"`.

**REJECT (`is_approved=False`) if ANY of the above criteria are not met.**

## Required Action:

Call `approve_or_request_changes` with your decision. If rejecting, provide clear `feedback_notes` explaining which of the criteria were not met.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/exceptions.py
```python
"""
Custom exceptions for Epic Task Manager
"""

from __future__ import annotations


class EpicTaskManagerError(Exception):
    """Base exception for Epic Task Manager"""

    def __init__(self, message: str, task_id: str | None = None):
        self.task_id = task_id
        super().__init__(message)


class StateFileError(EpicTaskManagerError):
    """Error related to state file operations"""


class InitializationError(EpicTaskManagerError):
    """Error during initialization"""


class TaskNotFoundError(EpicTaskManagerError):
    """Task not found in state"""


class PhaseTransitionError(EpicTaskManagerError):
    """Invalid phase transition"""


class StateTransitionError(EpicTaskManagerError):
    """Invalid state machine transition"""

    def __init__(self, message: str, current_state: str, attempted_transition: str):
        super().__init__(message)
        self.current_state = current_state
        self.attempted_transition = attempted_transition


class ArtifactError(EpicTaskManagerError):
    """Error related to artifact operations"""


class ArtifactNotFoundError(ArtifactError):
    """Artifact file not found"""


class InvalidArtifactFormatError(ArtifactError):
    """Artifact content is malformed"""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/guidelines/coding_guidelines.md
```markdown
# Coding Guidelines

## 1. General Principles
- **Clarity is Paramount:** Write code that is easy to read and understand.
- **DRY (Don't Repeat Yourself):** Avoid duplicating code. Use functions and classes to promote reusability.
- **YAGNI (You Aren't Gonna Need It):** Do not add functionality that has not been explicitly requested.

## 2. Python-Specific Standards
- **Docstrings:** All modules, classes, and functions must have Google-style docstrings.
  ```python
  def my_function(param1: int) -> str:
      """This is a summary line.
      
      This is the extended description.
      
      Args:
          param1: The first parameter.
          
      Returns:
          A string describing the result.
      """
  ```
- **Type Hinting:** All function signatures and variable declarations must include type hints.
- **Error Handling:** Use specific exception types. Do not use broad `except Exception:`.
- **Imports:** Imports should be ordered: 1. Standard library, 2. Third-party, 3. Local application.
```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/prompts/implement_next_task.py
```python
"""
Epic Task Manager MCP Prompts
"""

from pathlib import Path


async def implement_next_task(task_id: str | None = None) -> str:
    """
    Load and return the implementation prompt for the Epic Task Manager workflow.

    This prompt guides users through the complete Epic Task Manager workflow
    for implementing a Jira ticket through all phases.

    Args:
        task_id: Optional task ID to include in the prompt. If provided,
                 the prompt will be customized with this specific task ID.

    Returns:
        str: The formatted prompt content from the markdown template
    """
    # Get the path to the prompt template
    prompt_path = Path(__file__).parent.parent / "templates" / "prompts" / "client" / "implement_next_task.md"

    # Read the prompt content
    with prompt_path.open(encoding="utf-8") as f:
        content = f.read()

    # If a task_id is provided, replace the placeholder
    if task_id:
        content = content.replace("TASK_ID", task_id)

    return content

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/models/schemas.py
```python
"""
Pydantic models for Epic Task Manager tool responses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """
    The single, standardized response object for all tools in the Epic Task Manager.
    This model provides a predictable, reliable contract between our server and the AI client.
    """

    status: str = Field(description="The status of the operation, typically 'success' or 'error'.")
    message: str = Field(description="A clear, human-readable message describing the result of the tool call. This can be displayed in a UI.")
    data: dict[str, Any] | None = Field(default=None, description="An optional, structured data payload. Used by informational tools like 'get_task_summary'.")
    next_prompt: str | None = Field(default=None, description="The complete, self-contained prompt for the AI's very next action. This is the core of the MCP-driven workflow.")

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/guidelines/formatting_guidelines.md
```markdown
# Formatting Guidelines for Work Artifacts

When creating work artifacts, please follow these formatting conventions to ensure consistency and readability:

## Numbered Lists

- Always use the format "1." not "1)" for numbered items
- When listing multiple numbered items within a text field, format them as complete sentences
- Avoid embedding numbered lists within single paragraphs - they will be automatically formatted for readability during artifact generation
- Example: "The implementation includes: 1. Feature flag control. 2. Conditional workflow. 3. Self-cleaning code."

## Text Content

- Write clear, concise descriptions
- Use proper punctuation and capitalization
- Separate distinct concepts with appropriate spacing
- For long descriptions, break them into logical paragraphs

## Field Content

- Keep field values focused and relevant
- Arrays should contain distinct, actionable items
- String fields should be complete thoughts, not fragments

These guidelines ensure that all generated artifacts are consistently formatted and easily readable by both humans and machines.

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/utils/clean_slate.md
```markdown
<system_command name="clean_slate">
  <objective>Suggest that the human user start a new chat session to optimize performance before proceeding with the main task.</objective>
  <instructions>
    1.  **PAUSE** all other actions.
    2.  **Output this exact text to the user:** "A new major phase of work has begun. To ensure the best performance and a clean context, I recommend we start a new chat session."
    3.  **Wait for the user's response.**
    4.  If the user agrees or starts a new session, your first command in the new session MUST be `mcp_epic-task-manager_begin_or_resume_task(task_id="{task_id}")`.
    5.  If the user wishes to continue in the current session, disregard this command and proceed with the rest of the prompt below.
  </instructions>
</system_command>

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/coding/work_single_step.md
```markdown
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

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/guidelines/git_guidelines.md
```markdown
# Git Guidelines

## 1. Branching
- **Branch Name:** All feature branches must follow the convention `feature/{task_id}`.
- **Base Branch:** All feature branches must be created from the `main` or `master` branch.

## 2. Commits
- **Commit Message Format:** Commit messages must follow the "Conventional Commits" specification.
  - `feat: A new feature`
  - `fix: A bug fix`
  - `docs: Documentation only changes`
  - `style: Changes that do not affect the meaning of the code`
  - `refactor: A code change that neither fixes a bug nor adds a feature`
  - `test: Adding missing tests or correcting existing tests`
- **Atomic Commits:** Each commit should represent a single logical change. Do not bundle unrelated changes into one commit.
```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/resources/workflow_docs.py
```python
"""
Workflow documentation resource
"""

from typing import Any

from epic_task_manager.config.settings import settings


async def get_workflow_documentation() -> dict[str, Any]:
    """
    Provide documentation about the workflow phases
    """
    return {
        "workflow_phases": settings.workflow_phases,
        "transitions": settings.phase_transitions,
        "description": {
            "retrieved": "Task has been fetched from Jira and is ready for planning",
            "planning": "Creating implementation plan and design decisions",
            "coding": "Implementing the solution according to the plan",
            "review": "Code review and quality checks",
            "complete": "Task is done and deployed",
        },
    }

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/finalize_artifact.md
```markdown
---
{{ metadata }}
---

# 🎉 Task Finalization Complete: {{ task_id }}

## Git Workflow Summary

Your feature has been successfully pushed to the remote repository and a Pull Request has been created for team review.

### 📋 Final Receipt

**Commit Hash:** `{{ commit_hash }}`
**Pull Request URL:** {{ pull_request_url }}

---

## Next Steps

1. **Team Review**: Your Pull Request is now ready for team review at the URL above
2. **CI/CD Pipeline**: Automated checks will run on your changes
3. **Merge**: Once approved, your changes will be merged to the main branch

The Epic Task Manager workflow for this task is now complete! 🚀

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/utils/yolo_auto_approve.md
```markdown
<role>Autonomous Agent (YOLO Mode)</role>
<objective>Automatically approve the artifact for task `{task_id}` in state `{current_state}` to advance the workflow without human intervention.</objective>
<instructions>
1. You are operating in YOLO (You Only Look Once) mode. Human review is disabled.
2. You MUST immediately call the `approve_or_request_changes` tool with `is_approved=true`.
3. Do not ask for confirmation. Do not analyze the artifact. This is an autonomous, non-interactive step.
</instructions>
<example>
`mcp_epic-task-manager_approve_or_request_changes(task_id="{task_id}", is_approved=true)`
</example>

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/guidelines/testing_guidelines.md
```markdown
# Testing Guidelines

## 1. Unit Tests
- **Coverage:** Aim for high unit test coverage for any new code.
- **Isolation:** Unit tests must be isolated and not depend on external services like databases or APIs. Use mocks where appropriate.
- **Assertion Clarity:** Assertions should be specific. `assert foo == True` is better than `assert foo`.

## 2. Integration Tests
- When running the full test suite (`pytest`), the primary success indicator is the `exit_code`. An `exit_code` of `0` means success. Any other value indicates failure.
- The `full_output` should be reviewed for warnings or deprecation notices even if the tests pass.
```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/git_setup_artifact.md
```markdown
---
task_id: {{ task_id }}
phase: {{ phase }}
status: {{ status }}
version: {{ version }}
ai_model: {{ ai_model }}
---

# Git Setup Phase: {{ task_id }}

## Branch Information

**Branch Name**: {{ branch_name }}
**Branch Created**: {{ branch_created }}
**Branch Status**: {{ branch_status }}
**Ready for Work**: {{ ready_for_work }}

## Setup Summary

The git environment has been configured for task {{ task_id }} with the following status:

- Current branch: `{{ branch_name }}`
- New branch created: {{ branch_created }}
- Working directory status: {{ branch_status }}
- Development can proceed: {{ ready_for_work }}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/validation_etm14.py
```python
"""
ETM-14 Testing Phase Validation Module

This module provides simple validation functions for testing the Epic Task Manager
testing phase functionality. It is specifically created for ETM-14 validation.
"""


def validate_testing_phase() -> bool:
    """
    Validate that the testing phase works correctly.

    This function is designed for ETM-14 testing phase validation.

    Returns:
        bool: Always returns True to indicate successful validation
    """
    return True


def get_validation_message() -> str:
    """
    Get a validation success message.

    Returns:
        str: A success message indicating testing phase validation passed
    """
    return "ETM-14 testing phase validation completed successfully"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/__init__.py
```python
"""
Task source abstractions and implementations
"""

from .base import LocalTaskProvider, RemoteTaskProvider, TaskProvider
from .constants import (
    COMMENT_SECTION_HEADER,
    COMMENT_TEMPLATE,
    COMMENT_TIMESTAMP_FORMAT,
    DEFAULT_LOCAL_TASK_STATUS,
    IGNORED_TASK_FILES,
    STATUS_UPDATE_TEMPLATE,
    TASK_FILE_EXTENSION,
)

__all__ = [
    "COMMENT_SECTION_HEADER",
    "COMMENT_TEMPLATE",
    "COMMENT_TIMESTAMP_FORMAT",
    "DEFAULT_LOCAL_TASK_STATUS",
    "IGNORED_TASK_FILES",
    "STATUS_UPDATE_TEMPLATE",
    "TASK_FILE_EXTENSION",
    "LocalTaskProvider",
    "RemoteTaskProvider",
    "TaskProvider",
]

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/constants.py
```python
"""
Constants for task source providers
"""

# Default status values
DEFAULT_LOCAL_TASK_STATUS = "To Do"

# File patterns and names
IGNORED_TASK_FILES = ["README.md"]
TASK_FILE_EXTENSION = ".md"

# Status comment templates
STATUS_UPDATE_TEMPLATE = "\n\n<!-- Status Updated: {} -->\n"
COMMENT_SECTION_HEADER = "\n\n## Comments\n"
COMMENT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
COMMENT_TEMPLATE = "\n- **{}**: {}\n"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/utils/hello_world.py
```python
"""Simple hello world module for testing Epic Task Manager workflow.

This module contains a basic hello_world function for workflow verification purposes.
"""


def hello_world() -> str:
    """Return a simple greeting message.

    Returns:
        str: The string "Hello World"

    Example:
        >>> from epic_task_manager.utils.hello_world import hello_world
        >>> hello_world()
        'Hello World'
    """
    return "Hello World"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/coding_artifact.md
```markdown
---
{{ metadata }}
---

# Implementation: {{ task_id }}

## 1. Implementation Summary
{{ implementation_summary }}

## 2. Execution Steps Completed
{% for prompt_id in execution_steps_completed %}
- {{ prompt_id }}
{% endfor %}

## 3. Testing Notes
{{ testing_notes }}

## 4. Acceptance Criteria Met
{{ acceptance_criteria_met }}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/tools/__init__.py
```python
"""Tools module for Epic Task Manager"""

from . import (
    get_active_task,
    get_task_summary,
    initialize,
    review_tools,
    task_tools,
)

__all__ = [
    "get_active_task",
    "get_task_summary",
    "initialize",
    "review_tools",
    "task_tools",
]

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/execution/exceptions.py
```python
"""
Custom exceptions for the execution module
"""


class ArtifactNotFoundError(Exception):
    """Raised when a required artifact is not found"""


class TemplateNotFoundError(Exception):
    """Raised when a required template is not found"""


class InvalidArtifactError(Exception):
    """Raised when an artifact has invalid format or content"""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/jira/schemas.py
```python
"""
Jira-specific schemas and models
"""

from enum import StrEnum


class JiraStatus(StrEnum):
    """Enum for Jira status values"""

    TO_DO = "TO DO"
    IN_PROGRESS = "In Progress"
    CODE_REVIEW = "Code Review"
    DONE = "Done"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/planning_strategy_artifact.md
```markdown
---
{{ metadata }}
---

# Planning Strategy: {{ task_id }}

## 1. High-Level Strategy
{{ high_level_strategy }}

## 2. Key Components
{{ key_components }}

## 3. Architectural Decisions
{{ architectural_decisions }}

## 4. Risk Analysis
{{ risk_analysis }}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/planning_solution_design_artifact.md
```markdown
---
{{ metadata }}
---

# Solution Design: {{ task_id }}

## 1. Approved Strategy Summary
{{ approved_strategy_summary }}

## 2. Detailed Design
{{ detailed_design }}

## 3. File Breakdown
{{ file_breakdown }}

## 4. Dependencies
{{ dependencies }}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/scaffolding_artifact.md
```markdown
---
{{ metadata }}
---

# Scaffolding Complete: {{ task_id }}

## Summary
The execution plan has been transcribed into the codebase as detailed TODO comments. The following files were modified to include these scaffolds.

## Files Scaffolded
{{ files_scaffolded }}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/local/__init__.py
```python
"""
Local provider package for Epic Task Manager.

This package implements the local file-based task provider that reads
markdown task files from the .epictaskmanager/tasks/ inbox directory.
"""

from .provider import LocalProvider

__all__ = ["LocalProvider"]

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/testing_artifact.md
```markdown
---
{{ metadata }}
---

# Test Results: {{ task_id }}

## Test Execution Summary

**Command:** `{{ test_results.command_run }}`
**Exit Code:** {{ test_results.exit_code }}

## Test Output

```
{{ test_results.full_output }}
```
```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/planning_execution_plan_artifact.md
```markdown
---
{{ metadata }}
---

# Execution Plan: {{ task_id }}

## 1. Approved Design Summary
{{ approved_design_summary }}

## 2. Execution Steps
{{ execution_steps }}

## 3. Execution Order Notes
{{ execution_order_notes }}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/responses/invalid_state_error.md
```markdown
# Invalid State Transition

**Current State:** {current_state}

**Attempted Action:** {attempted_action}

**Error:** {error_message}

**Valid Actions:** {valid_actions}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/artifacts/gatherrequirements_artifact.md
```markdown
---
{{metadata}}
---

# Task Details: {{task_id}}

## Summary
{{task_summary}}

## Description
{{task_description}}

## Acceptance Criteria
{{acceptance_criteria}}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/__init__.py
```python
"""
Epic Task Manager - A hierarchical state machine based task workflow system.
"""

__version__ = "0.2.0"

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/utils/__init__.py
```python
"""Utilities package for Epic Task Manager."""

from .hello_world import hello_world

__all__ = ["hello_world"]

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/responses/generic_error.md
```markdown
# Error

**Status:** {status}

**Message:** {message}

**Details:** {details}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/execution/__init__.py
```python
"""Execution layer for business logic and artifact management."""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/models/__init__.py
```python
"""Data models and schemas for Epic Task Manager."""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/utils/formatting_section.md
```markdown
## Formatting Guidelines

{formatting_guidelines}

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/__init__.py
```python
"""Templates for artifacts, prompts, and responses."""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/config/__init__.py
```python
"""Configuration management using pydantic_settings"""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/prompts/__init__.py
```python
"""
Epic Task Manager MCP Prompts
"""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/state/__init__.py
```python
"""State management and hierarchical state machine definitions."""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/resources/__init__.py
```python
"""Resources module for future MCP resources"""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/task_sources/jira/__init__.py
```python
"""
Jira task source implementation
"""

```

File: /Users/mohammedfahadkaleem/Documents/Workspace/backup/epic-task-manager-v3/src/epic_task_manager/templates/prompts/gatherrequirements/atlassian_work.md
```markdown
# Atlassian-specific requirements template
```

</file_contents>

