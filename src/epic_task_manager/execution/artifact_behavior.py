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
