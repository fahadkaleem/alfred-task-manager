"""
Comprehensive tests for ArtifactBehaviorConfig class covering behavior mapping and configuration logic
"""

import pytest

from epic_task_manager.execution.artifact_behavior import ArtifactBehavior, ArtifactBehaviorConfig


class TestArtifactBehavior:
    """Test ArtifactBehavior enum functionality"""

    def test_artifact_behavior_enum_values(self):
        """Test that ArtifactBehavior enum has correct values"""
        assert ArtifactBehavior.REPLACE.value == "replace"
        assert ArtifactBehavior.APPEND_ONLY.value == "append_only"
        assert len(ArtifactBehavior) == 2


class TestArtifactBehaviorConfig:
    """Test ArtifactBehaviorConfig configuration and behavior detection"""

    @pytest.fixture
    def behavior_config(self):
        """Create ArtifactBehaviorConfig instance for testing"""
        return ArtifactBehaviorConfig()

    def test_default_configuration_initialization(self, behavior_config):
        """Test that default configuration is properly initialized"""
        # Planning should be configured as append-only
        assert "planning" in behavior_config._append_only_phases

        # First sub-stage mapping should exist for planning
        assert behavior_config._first_sub_stages.get("planning") == "strategy"

        # Sub-stages should be properly configured
        expected_planning_stages = {"strategy", "solutiondesign", "executionplan"}
        assert behavior_config._phase_sub_stages.get("planning") == expected_planning_stages

    def test_get_behavior_for_planning_phases(self, behavior_config):
        """Test get_behavior returns APPEND_ONLY for planning phases"""
        planning_states = ["planning_strategy", "planning_solutiondesign", "planning_executionplan"]

        for state in planning_states:
            behavior = behavior_config.get_behavior(state)
            assert behavior == ArtifactBehavior.APPEND_ONLY

    def test_get_behavior_for_non_planning_phases(self, behavior_config):
        """Test get_behavior returns REPLACE for non-planning phases"""
        non_planning_states = ["gatherrequirements_working", "gitsetup_working", "coding_working", "testing_working", "finalize_working"]

        for state in non_planning_states:
            behavior = behavior_config.get_behavior(state)
            assert behavior == ArtifactBehavior.REPLACE

    def test_is_first_sub_stage_for_planning_strategy(self, behavior_config):
        """Test is_first_sub_stage returns True for planning_strategy"""
        assert behavior_config.is_first_sub_stage("planning_strategy") is True

    def test_is_first_sub_stage_for_subsequent_planning_stages(self, behavior_config):
        """Test is_first_sub_stage returns False for subsequent planning stages"""
        subsequent_stages = ["planning_solutiondesign", "planning_executionplan"]

        for stage in subsequent_stages:
            assert behavior_config.is_first_sub_stage(stage) is False

    def test_is_first_sub_stage_for_non_planning_phases(self, behavior_config):
        """Test is_first_sub_stage returns False for non-planning phases"""
        non_planning_states = ["gatherrequirements_working", "coding_working", "testing_working"]

        for state in non_planning_states:
            assert behavior_config.is_first_sub_stage(state) is False

    def test_should_append_for_planning_strategy(self, behavior_config):
        """Test should_append returns False for planning_strategy (first stage)"""
        assert behavior_config.should_append("planning_strategy") is False

    def test_should_append_for_subsequent_planning_stages(self, behavior_config):
        """Test should_append returns True for subsequent planning stages"""
        subsequent_stages = ["planning_solutiondesign", "planning_executionplan"]

        for stage in subsequent_stages:
            assert behavior_config.should_append(stage) is True

    def test_should_append_for_non_planning_phases(self, behavior_config):
        """Test should_append returns False for non-planning phases"""
        non_planning_states = ["gatherrequirements_working", "coding_working", "testing_working"]

        for state in non_planning_states:
            assert behavior_config.should_append(state) is False

    def test_extract_phase_name_from_various_states(self, behavior_config):
        """Test _extract_phase_name correctly parses different state formats"""
        test_cases = [("planning_strategy", "planning"), ("coding_working", "coding"), ("gatherrequirements_working", "gatherrequirements"), ("testing_aireview", "testing")]

        for state, expected_phase in test_cases:
            phase = behavior_config._extract_phase_name(state)
            assert phase == expected_phase

    def test_parse_state_with_sub_stage(self, behavior_config):
        """Test _parse_state correctly separates phase and sub-stage"""
        phase, sub_stage = behavior_config._parse_state("planning_strategy")
        assert phase == "planning"
        assert sub_stage == "strategy"

    def test_parse_state_without_sub_stage(self, behavior_config):
        """Test _parse_state handles states without explicit sub-stage"""
        phase, sub_stage = behavior_config._parse_state("coding")
        assert phase == "coding"
        assert sub_stage == "working"

    def test_add_append_only_phase_for_extensibility(self, behavior_config):
        """Test add_append_only_phase method for future extensibility"""
        # Add coding as append-only phase
        coding_sub_stages = {"implementation", "review", "finalization"}
        behavior_config.add_append_only_phase("coding", "implementation", coding_sub_stages)

        # Verify coding is now configured as append-only
        assert behavior_config.get_behavior("coding_implementation") == ArtifactBehavior.APPEND_ONLY
        assert behavior_config.is_first_sub_stage("coding_implementation") is True
        assert behavior_config.should_append("coding_review") is True
        assert behavior_config.should_append("coding_finalization") is True

    def test_behavior_consistency_across_methods(self, behavior_config):
        """Test that behavior methods are consistent with each other"""
        # For APPEND_ONLY phases
        append_only_states = ["planning_strategy", "planning_solutiondesign", "planning_executionplan"]

        for state in append_only_states:
            behavior = behavior_config.get_behavior(state)
            assert behavior == ArtifactBehavior.APPEND_ONLY

            # First stage should not append, subsequent should append
            if behavior_config.is_first_sub_stage(state):
                assert behavior_config.should_append(state) is False
            else:
                assert behavior_config.should_append(state) is True

        # For REPLACE phases
        replace_states = ["gatherrequirements_working", "coding_working"]

        for state in replace_states:
            behavior = behavior_config.get_behavior(state)
            assert behavior == ArtifactBehavior.REPLACE
            assert behavior_config.should_append(state) is False

    def test_edge_cases_and_error_handling(self, behavior_config):
        """Test edge cases and potential error conditions"""
        # Empty state should not cause errors
        behavior = behavior_config.get_behavior("")
        assert behavior == ArtifactBehavior.REPLACE

        # Unknown phase should default to REPLACE
        behavior = behavior_config.get_behavior("unknown_phase_working")
        assert behavior == ArtifactBehavior.REPLACE

        # Single word state should work
        behavior = behavior_config.get_behavior("singleword")
        assert behavior == ArtifactBehavior.REPLACE


class TestArtifactBehaviorConfigIntegration:
    """Integration tests for ArtifactBehaviorConfig with realistic scenarios"""

    def test_complete_planning_workflow_behavior(self):
        """Test behavior configuration through complete planning workflow"""
        config = ArtifactBehaviorConfig()

        # Simulate planning workflow progression
        planning_workflow = [
            ("planning_strategy", False, False),  # First stage: write
            ("planning_solutiondesign", True, True),  # Second stage: append
            ("planning_executionplan", True, True),  # Third stage: append
        ]

        for state, should_append_expected, is_append_only in planning_workflow:
            behavior = config.get_behavior(state)
            should_append_actual = config.should_append(state)

            if is_append_only:
                assert behavior == ArtifactBehavior.APPEND_ONLY

            assert should_append_actual == should_append_expected

    def test_mixed_phase_behavior_consistency(self):
        """Test that different phases maintain consistent behavior"""
        config = ArtifactBehaviorConfig()

        # Planning phases should be append-only
        planning_phases = ["planning_strategy", "planning_solutiondesign", "planning_executionplan"]
        for phase in planning_phases:
            assert config.get_behavior(phase) == ArtifactBehavior.APPEND_ONLY

        # All other phases should be replace
        other_phases = ["gatherrequirements_working", "gitsetup_working", "coding_working", "testing_working", "finalize_working"]
        for phase in other_phases:
            assert config.get_behavior(phase) == ArtifactBehavior.REPLACE
            assert config.should_append(phase) is False

    def test_configuration_immutability_after_initialization(self):
        """Test that default configuration remains stable after creation"""
        config1 = ArtifactBehaviorConfig()
        config2 = ArtifactBehaviorConfig()

        # Both instances should have identical behavior
        test_states = ["planning_strategy", "planning_solutiondesign", "coding_working", "testing_working"]

        for state in test_states:
            assert config1.get_behavior(state) == config2.get_behavior(state)
            assert config1.should_append(state) == config2.should_append(state)
            assert config1.is_first_sub_stage(state) == config2.is_first_sub_stage(state)
