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
