"""Pure function context loaders for discovery planning."""

from typing import Any, Dict
from alfred.models.schemas import Task
from alfred.models.state import TaskState


def load_plan_task_context(task: Task, task_state: TaskState) -> Dict[str, Any]:
    """Pure function context loader for plan_task tool.

    Args:
        task: The task being planned
        task_state: Current task state with artifacts and context

    Returns:
        Context dictionary for prompt template rendering

    Raises:
        ValueError: If required dependencies are missing
    """
    # Check for re-planning context from active tool state
    restart_context = None
    context_store = {}
    if task_state.active_tool_state:
        restart_context = task_state.active_tool_state.context_store.get("restart_context")
        context_store = task_state.active_tool_state.context_store

    # Base context for all planning states
    context = {
        "task_title": task.title or "Untitled Task",
        "task_context": task.context or "",
        "implementation_details": task.implementation_details or "",
        "acceptance_criteria": task.acceptance_criteria or [],
        "restart_context": restart_context,
        "preserved_artifacts": context_store.get("preserved_artifacts", []),
        # Autonomous mode configuration
        "autonomous_mode": context_store.get("autonomous_mode", False),
        "autonomous_note": context_store.get("autonomous_note", "Running in interactive mode - human reviews are enabled for each phase"),
        "skip_contracts": context_store.get("skip_contracts", False),
        "complexity_note": context_store.get("complexity_note", ""),
    }

    # Add state-specific context
    current_state = None
    if task_state.active_tool_state:
        current_state = task_state.active_tool_state.current_state
        context["current_state"] = current_state

        # Add artifacts from previous states using context_store from active tool
        # Map the stored artifact keys to template variable names
        if current_state != "discovery":
            discovery_artifact = task_state.active_tool_state.context_store.get("context_discovery_artifact")
            if discovery_artifact:
                context["discovery_artifact"] = discovery_artifact
                # Flatten for template access
                if hasattr(discovery_artifact, "findings"):
                    context["discovery_findings"] = discovery_artifact.findings
                elif isinstance(discovery_artifact, dict) and "findings" in discovery_artifact:
                    context["discovery_findings"] = discovery_artifact["findings"]

                if hasattr(discovery_artifact, "questions"):
                    context["discovery_questions"] = "\n".join(f"- {q}" for q in discovery_artifact.questions)
                elif isinstance(discovery_artifact, dict) and "questions" in discovery_artifact:
                    questions = discovery_artifact.get("questions", [])
                    context["discovery_questions"] = "\n".join(f"- {q}" for q in questions)

        if current_state in ["contracts", "implementation_plan", "validation"]:
            clarification_artifact = task_state.active_tool_state.context_store.get("clarification_artifact")
            if clarification_artifact:
                context["clarification_artifact"] = clarification_artifact

        if current_state in ["implementation_plan", "validation"]:
            contracts_artifact = task_state.active_tool_state.context_store.get("contract_design_artifact")
            if contracts_artifact:
                context["contracts_artifact"] = contracts_artifact

        if current_state == "validation":
            implementation_artifact = task_state.active_tool_state.context_store.get("implementation_plan_artifact")
            if implementation_artifact:
                context["implementation_artifact"] = implementation_artifact

    return context


def load_simple_task_context(task: Task, task_state: TaskState) -> Dict[str, Any]:
    """Context loader for simple tasks that skip CONTRACTS state."""
    context = load_plan_task_context(task, task_state)
    context["skip_contracts"] = True
    return context
