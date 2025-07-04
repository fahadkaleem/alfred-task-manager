"""Discovery planning workflow state machine implementation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from transitions.core import Machine

from alfred.constants import ToolName
from alfred.core.state_machine_builder import workflow_builder
from alfred.core.workflow import BaseWorkflowTool
from alfred.models.planning_artifacts import (
    ContextDiscoveryArtifact,
    ClarificationArtifact,
    ContractDesignArtifact,
    ImplementationPlanArtifact,
    ValidationArtifact,
)


class PlanTaskState(str, Enum):
    """State enumeration for the discovery planning workflow."""

    DISCOVERY = "discovery"
    CLARIFICATION = "clarification"
    CONTRACTS = "contracts"
    IMPLEMENTATION_PLAN = "implementation_plan"
    VALIDATION = "validation"
    VERIFIED = "verified"


class PlanTaskTool(BaseWorkflowTool):
    """Discovery planning tool with conversational, context-rich workflow."""

    def __init__(self, task_id: str, restart_context: Optional[Dict] = None, autonomous_mode: bool = False):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK)

        # Define artifact mapping
        self.artifact_map = {
            PlanTaskState.DISCOVERY: ContextDiscoveryArtifact,
            PlanTaskState.CLARIFICATION: ClarificationArtifact,
            PlanTaskState.CONTRACTS: ContractDesignArtifact,
            PlanTaskState.IMPLEMENTATION_PLAN: ImplementationPlanArtifact,
            PlanTaskState.VALIDATION: ValidationArtifact,
        }

        # Handle re-planning context
        if restart_context:
            initial_state = self._determine_restart_state(restart_context)
            self._load_preserved_artifacts(restart_context)
        else:
            initial_state = PlanTaskState.DISCOVERY

        # Initially include all states - we'll skip dynamically during transitions
        workflow_states = [PlanTaskState.DISCOVERY, PlanTaskState.CLARIFICATION, PlanTaskState.CONTRACTS, PlanTaskState.IMPLEMENTATION_PLAN, PlanTaskState.VALIDATION]

        # Use the builder to create state machine configuration
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=workflow_states,
            terminal_state=PlanTaskState.VERIFIED,
            initial_state=initial_state,
        )

        # Create the state machine
        self.machine = Machine(model=self, states=machine_config["states"], transitions=machine_config["transitions"], initial=machine_config["initial"], auto_transitions=False)

        # Configuration flags
        self._skip_contracts = False
        self.autonomous_mode = autonomous_mode

        # Store autonomous mode in context for templates
        self.context_store["autonomous_mode"] = autonomous_mode
        if autonomous_mode:
            self.context_store["autonomous_note"] = "Running in autonomous mode - human reviews will be skipped"
        else:
            self.context_store["autonomous_note"] = "Running in interactive mode - human reviews are enabled for each phase"

    def get_final_work_state(self) -> str:
        """Return the final work state that produces the main artifact."""
        return PlanTaskState.VALIDATION.value

    def _determine_restart_state(self, restart_context: Dict) -> PlanTaskState:
        """Determine initial state for re-planning."""
        restart_from = restart_context.get("restart_from", "DISCOVERY")
        return PlanTaskState(restart_from.lower())

    def _load_preserved_artifacts(self, restart_context: Dict) -> None:
        """Load preserved artifacts from previous planning attempt."""
        preserved = restart_context.get("preserve_artifacts", [])
        for artifact_name in preserved:
            # Load preserved artifact into context_store
            self.context_store[f"preserved_{artifact_name}"] = restart_context.get(artifact_name)

    def _determine_workflow_states(self, discovery_artifact: Optional[ContextDiscoveryArtifact] = None) -> list:
        """Determine which states to include based on complexity."""
        base_states = [PlanTaskState.DISCOVERY, PlanTaskState.CLARIFICATION]

        # Only add CONTRACTS state for complex tasks
        if discovery_artifact and not self.should_skip_contracts(discovery_artifact):
            base_states.append(PlanTaskState.CONTRACTS)
        elif discovery_artifact is None:
            # If no discovery artifact yet (initial setup), include contracts
            # Will be validated later in the workflow
            base_states.append(PlanTaskState.CONTRACTS)

        base_states.extend([PlanTaskState.IMPLEMENTATION_PLAN, PlanTaskState.VALIDATION])

        return base_states

    def should_skip_contracts(self, discovery_artifact: ContextDiscoveryArtifact) -> bool:
        """Determine if CONTRACTS state should be skipped for simple tasks."""
        if not discovery_artifact:
            return False

        # Simple task criteria based on multiple factors
        complexity = getattr(discovery_artifact, "complexity_assessment", "MEDIUM")
        relevant_files = getattr(discovery_artifact, "relevant_files", [])
        integration_points = getattr(discovery_artifact, "integration_points", [])
        code_patterns = getattr(discovery_artifact, "code_patterns", [])

        # Skip contracts for simple tasks if:
        # 1. Complexity is explicitly LOW
        # 2. Few files affected (≤ 3)
        # 3. No new integration points
        # 4. Follows existing patterns (no new architecture)

        is_low_complexity = complexity == "LOW"
        few_files = len(relevant_files) <= 3
        no_new_integrations = len(integration_points) == 0
        follows_patterns = len(code_patterns) > 0  # Uses existing patterns

        # Skip if it's clearly a simple task
        should_skip = is_low_complexity and few_files and no_new_integrations

        return should_skip

    def check_complexity_after_clarification(self) -> None:
        """Check if we should skip contracts after clarification phase."""
        # Get discovery artifact from context store
        discovery_artifact = self.context_store.get("context_discovery_artifact")
        if discovery_artifact and self.should_skip_contracts(discovery_artifact):
            self._skip_contracts = True
            # Add note to context for templates
            self.context_store["skip_contracts"] = True
            self.context_store["complexity_note"] = "Skipping CONTRACTS phase due to LOW complexity assessment"

    def get_next_state_after_clarification(self) -> str:
        """Determine next state after clarification based on complexity."""
        if self._skip_contracts:
            return PlanTaskState.IMPLEMENTATION_PLAN.value
        return PlanTaskState.CONTRACTS.value

    def should_auto_approve(self) -> bool:
        """Check if we should automatically approve after AI review."""
        return self.autonomous_mode

    def get_autonomous_config(self) -> Dict[str, Any]:
        """Get configuration for autonomous mode."""
        return {"skip_human_reviews": self.autonomous_mode, "auto_approve_after_ai": self.autonomous_mode, "question_handling": "best_guess" if self.autonomous_mode else "interactive"}

    def initiate_replanning(self, trigger: str, restart_from: str, changes: str, preserve_artifacts: Optional[List[str]] = None) -> Dict[str, Any]:
        """Initiate re-planning with preserved context."""
        restart_context = {
            "trigger": trigger,  # "requirements_changed", "implementation_failed", "review_failed"
            "restart_from": restart_from,  # State to restart from
            "changes": changes,  # What changed
            "preserve_artifacts": preserve_artifacts or [],
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "previous_state": self.state,
        }

        # Store restart context for next planning session
        self.context_store["restart_context"] = restart_context

        return restart_context

    def can_restart_from_state(self, state: str) -> bool:
        """Check if we can restart planning from a given state."""
        valid_restart_states = [
            PlanTaskState.DISCOVERY.value,
            PlanTaskState.CLARIFICATION.value,
            PlanTaskState.CONTRACTS.value,
            PlanTaskState.IMPLEMENTATION_PLAN.value,
            PlanTaskState.VALIDATION.value,
        ]
        return state in valid_restart_states
