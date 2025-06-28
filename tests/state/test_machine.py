"""
Comprehensive tests for Epic Task Manager State Machine
Tests the hierarchical state machine configuration, transitions, and validation.
"""

import pytest

from epic_task_manager.state.machine import INITIAL_STATE, review_lifecycle_children, states, transitions


class TestStateMachineConfiguration:
    """Test the state machine configuration is valid and complete."""

    def test_initial_state_is_valid(self):
        """Test INITIAL_STATE is a valid state."""
        # Extract all valid state names
        valid_states = set()
        for state in states:
            if isinstance(state, dict):
                if "children" in state:
                    # Hierarchical state - add parent and children
                    parent_name = state["name"]
                    valid_states.add(parent_name)
                    for child in state["children"]:
                        child_name = child["name"]
                        valid_states.add(f"{parent_name}_{child_name}")
                else:
                    valid_states.add(state["name"])
            else:
                # Simple state
                valid_states.add(state)

        assert INITIAL_STATE in valid_states

    def test_review_lifecycle_children_structure(self):
        """Test review lifecycle children have correct structure."""
        expected_children = ["working", "aireview", "devreview", "verified"]

        assert len(review_lifecycle_children) == 4
        for i, child in enumerate(review_lifecycle_children):
            assert child["name"] == expected_children[i]

    def test_all_phases_have_review_lifecycle(self):
        """Test all main phases use appropriate lifecycle (simplified for requirements, standard for gitsetup/coding/testing/finalize, custom for planning)."""
        expected_phases = ["gatherrequirements", "gitsetup", "planning", "scaffolding", "coding", "testing", "finalize"]

        phases_with_children = []
        for state in states:
            if isinstance(state, dict) and "children" in state:
                phases_with_children.append(state["name"])
                # Check if it's planning phase with custom children
                if state["name"] == "planning":
                    assert len(state["children"]) == 7  # 3 stages x 2 states each + verified
                    assert state["initial"] == "strategy"
                elif state["name"] == "gatherrequirements":
                    # Simplified phase uses only working and verified states
                    assert state["children"] == [{"name": "working"}, {"name": "verified"}]
                    assert state["initial"] == "working"
                else:
                    # Other phases (gitsetup, scaffolding, coding, testing, finalize) use standard review lifecycle
                    assert state["children"] == review_lifecycle_children
                    assert state["initial"] == "working"

        assert phases_with_children == expected_phases

    def test_done_state_exists(self):
        """Test 'done' state exists as terminal state."""
        # Find done state
        done_state = None
        for state in states:
            if state == "done":
                done_state = state
                break

        assert done_state == "done"

    @pytest.mark.parametrize(
        "phase,expected_states",
        [
            ("gatherrequirements", ["gatherrequirements_working", "gatherrequirements_verified"]),
            ("gitsetup", ["gitsetup_working", "gitsetup_aireview", "gitsetup_devreview", "gitsetup_verified"]),
            (
                "planning",
                [
                    "planning_strategy",
                    "planning_strategydevreview",
                    "planning_solutiondesign",
                    "planning_solutiondesigndevreview",
                    "planning_executionplan",
                    "planning_executionplandevreview",
                    "planning_verified",
                ],
            ),
            ("coding", ["coding_working", "coding_aireview", "coding_devreview", "coding_verified"]),
            ("testing", ["testing_working", "testing_aireview", "testing_devreview", "testing_verified"]),
            ("finalize", ["finalize_working", "finalize_aireview", "finalize_devreview", "finalize_verified"]),
        ],
        ids=["gatherrequirements", "gitsetup", "planning", "coding", "testing", "finalize"],
    )
    def test_phase_substates_are_complete(self, phase, expected_states):
        """Test each phase has all required substates."""
        # Find the phase configuration
        phase_config = None
        for state in states:
            if isinstance(state, dict) and state["name"] == phase:
                phase_config = state
                break

        assert phase_config is not None

        # Build expected state names
        actual_states = [f"{phase}_{child['name']}" for child in phase_config["children"]]
        assert actual_states == expected_states


class TestStateTransitionConfiguration:
    """Test state transition configuration is valid and complete."""

    def test_all_working_states_can_submit_for_review(self):
        """Test all initial work states have submit_for_ai_review transition."""
        all_phases = ["gatherrequirements", "gitsetup", "planning", "coding", "testing", "finalize"]

        # Test all phases
        for phase in all_phases:
            if phase == "planning":
                # Planning has special three-stage workflow
                planning_stages = [
                    ("planning_strategy", "planning_strategydevreview"),
                    ("planning_solutiondesign", "planning_solutiondesigndevreview"),
                    ("planning_executionplan", "planning_executionplandevreview"),
                ]
                for stage, dest_state in planning_stages:
                    transition_found = False
                    for transition in transitions:
                        if transition["trigger"] == "submit_for_ai_review" and transition["source"] == stage and transition["dest"] == dest_state:
                            transition_found = True
                            break
                    assert transition_found, f"Missing submit_for_ai_review transition for {stage}"
            elif phase == "gatherrequirements":
                # Claimtask is simplified phase that goes directly to verified
                working_state = f"{phase}_working"
                verified_state = f"{phase}_verified"

                # Find the transition
                transition_found = False
                for transition in transitions:
                    if transition["trigger"] == "submit_for_ai_review" and transition["source"] == working_state and transition["dest"] == verified_state:
                        transition_found = True
                        break

                assert transition_found, f"Missing submit_for_ai_review transition for {working_state}"
            else:
                # Standard phases go to aireview
                working_state = f"{phase}_working"
                aireview_state = f"{phase}_aireview"

                # Find the transition
                transition_found = False
                for transition in transitions:
                    if transition["trigger"] == "submit_for_ai_review" and transition["source"] == working_state and transition["dest"] == aireview_state:
                        transition_found = True
                        break

                assert transition_found, f"Missing submit_for_ai_review transition for {working_state}"

    def test_all_aireview_states_can_approve_or_reject(self):
        """Test all _aireview states have ai_approves and request_revision transitions."""
        # All phases except planning and simplified phases use the standard aireview/devreview pattern
        all_phases = ["coding", "testing", "finalize"]

        for phase in all_phases:
            aireview_state = f"{phase}_aireview"
            devreview_state = f"{phase}_devreview"
            # Testing phase has special test-fix loop - failures go back to coding
            expected_reject_dest = "coding_working" if phase == "testing" else f"{phase}_working"

            # Check ai_approves transition
            approve_found = False
            reject_found = False

            for transition in transitions:
                if transition["trigger"] == "ai_approves" and transition["source"] == aireview_state and transition["dest"] == devreview_state:
                    approve_found = True
                elif transition["trigger"] == "request_revision" and transition["source"] == aireview_state and transition["dest"] == expected_reject_dest:
                    reject_found = True

            assert approve_found, f"Missing ai_approves transition for {aireview_state}"
            assert reject_found, f"Missing request_revision transition for {aireview_state} -> {expected_reject_dest}"

    def test_all_devreview_states_can_approve_or_reject(self):
        """Test all _devreview states have human_approves and request_revision transitions."""
        # All phases except planning and simplified phases use the standard devreview pattern
        all_phases = ["coding", "testing", "finalize"]

        for phase in all_phases:
            devreview_state = f"{phase}_devreview"
            verified_state = f"{phase}_verified"

            # Check human_approves transition
            approve_found = False
            reject_found = False

            for transition in transitions:
                if transition["trigger"] == "human_approves" and transition["source"] == devreview_state and transition["dest"] == verified_state:
                    approve_found = True
                elif transition["trigger"] == "request_revision" and transition["source"] == devreview_state:
                    reject_found = True

            assert approve_found, f"Missing human_approves transition for {devreview_state}"
            assert reject_found, f"Missing request_revision transition for {devreview_state}"

        # Test planning devreview states separately
        planning_devreview_states = [
            ("planning_strategydevreview", "planning_solutiondesign", "planning_strategy"),
            ("planning_solutiondesigndevreview", "planning_executionplan", "planning_solutiondesign"),
            ("planning_executionplandevreview", "planning_verified", "planning_executionplan"),
        ]

        for devreview_state, approve_dest, reject_dest in planning_devreview_states:
            # Check human_approves transition
            approve_found = False
            reject_found = False

            for transition in transitions:
                if transition["trigger"] == "human_approves" and transition["source"] == devreview_state and transition["dest"] == approve_dest:
                    approve_found = True
                elif transition["trigger"] == "request_revision" and transition["source"] == devreview_state and transition["dest"] == reject_dest:
                    reject_found = True

            assert approve_found, f"Missing human_approves transition for {devreview_state}"
            assert reject_found, f"Missing request_revision transition for {devreview_state}"

    def test_testing_phase_special_transitions(self):
        """Test testing phase has special transitions back to coding on rejection."""
        # Testing aireview -> coding_working on rejection
        reject_transition_found = False
        for transition in transitions:
            if transition["trigger"] == "request_revision" and transition["source"] == "testing_aireview" and transition["dest"] == "coding_working":
                reject_transition_found = True
                break

        assert reject_transition_found, "Missing testing_aireview -> coding_working transition"

        # Testing devreview -> coding_working on rejection
        reject_transition_found = False
        for transition in transitions:
            if transition["trigger"] == "request_revision" and transition["source"] == "testing_devreview" and transition["dest"] == "coding_working":
                reject_transition_found = True
                break

        assert reject_transition_found, "Missing testing_devreview -> coding_working transition"

    @pytest.mark.parametrize(
        "source,dest",
        [
            ("gatherrequirements_verified", "gitsetup_working"),
            ("gitsetup_verified", "planning_strategy"),
            ("planning_verified", "coding_working"),
            ("coding_verified", "testing_working"),
            ("testing_verified", "finalize_working"),
            ("finalize_verified", "done"),
        ],
        ids=["claim_to_gitsetup", "gitsetup_to_plan", "plan_to_code", "code_to_test", "test_to_finalize", "finalize_to_done"],
    )
    def test_phase_advancement_transitions(self, source, dest):
        """Test phase advancement transitions are correctly configured."""
        advance_found = False
        for transition in transitions:
            # Special case for planning to coding - can use either advance_to_code or advance_to_scaffold
            if source == "planning_verified" and dest == "coding_working":
                if transition["source"] == source and transition["dest"] == dest and transition["trigger"] in ["advance_to_code", "advance_to_scaffold"]:
                    advance_found = True
                    break
            elif transition["trigger"] == "advance" and transition["source"] == source and transition["dest"] == dest:
                advance_found = True
                break

        assert advance_found, f"Missing advance transition from {source} to {dest}"

    def test_planning_phase_three_stage_transitions(self):
        """Test planning phase has correct three-stage workflow transitions."""
        # Test strategy -> solution design transition
        transition_found = False
        for transition in transitions:
            if transition["trigger"] == "human_approves" and transition["source"] == "planning_strategydevreview" and transition["dest"] == "planning_solutiondesign":
                transition_found = True
                break
        assert transition_found, "Missing planning_strategydevreview -> planning_solutiondesign transition"

        # Test solution design -> execution plan transition
        transition_found = False
        for transition in transitions:
            if transition["trigger"] == "human_approves" and transition["source"] == "planning_solutiondesigndevreview" and transition["dest"] == "planning_executionplan":
                transition_found = True
                break
        assert transition_found, "Missing planning_solutiondesigndevreview -> planning_executionplan transition"

        # Test execution plan -> verified transition
        transition_found = False
        for transition in transitions:
            if transition["trigger"] == "human_approves" and transition["source"] == "planning_executionplandevreview" and transition["dest"] == "planning_verified":
                transition_found = True
                break
        assert transition_found, "Missing planning_executionplandevreview -> planning_verified transition"


class TestTransitionTriggers:
    """Test transition trigger names and consistency."""

    def test_all_required_triggers_exist(self):
        """Test all required triggers are defined."""
        expected_triggers = {"submit_for_ai_review", "ai_approves", "request_revision", "human_approves", "advance", "advance_to_scaffold", "advance_to_code", "advance_from_scaffold"}

        actual_triggers = set()
        for transition in transitions:
            actual_triggers.add(transition["trigger"])

        assert actual_triggers == expected_triggers

    def test_trigger_naming_consistency(self):
        """Test trigger names follow consistent naming conventions."""
        for transition in transitions:
            trigger = transition["trigger"]

            # All triggers should be lowercase with underscores
            assert trigger.islower(), f"Trigger {trigger} should be lowercase"
            assert " " not in trigger, f"Trigger {trigger} should not contain spaces"

            # Check valid trigger patterns
            valid_patterns = ["submit_for_ai_review", "ai_approves", "request_revision", "human_approves", "advance", "advance_to_scaffold", "advance_to_code", "advance_from_scaffold"]

            assert trigger in valid_patterns, f"Unknown trigger: {trigger}"

    def test_no_duplicate_transitions(self):
        """Test there are no duplicate transitions (same source + trigger)."""
        seen_combinations = set()

        for transition in transitions:
            combination = (transition["source"], transition["trigger"])
            assert combination not in seen_combinations, f"Duplicate transition: {combination}"
            seen_combinations.add(combination)


class TestStateMachineValidation:
    """Test state machine validation and edge cases."""

    def test_no_unreachable_states(self):
        """Test all states are reachable from initial state."""
        # Build reachability graph
        reachable = {INITIAL_STATE}
        transitions_map = {}

        # Build transition map
        for transition in transitions:
            source = transition["source"]
            dest = transition["dest"]
            if source not in transitions_map:
                transitions_map[source] = []
            transitions_map[source].append(dest)

        # BFS to find all reachable states
        queue = [INITIAL_STATE]
        while queue:
            current = queue.pop(0)
            if current in transitions_map:
                for dest in transitions_map[current]:
                    if dest not in reachable:
                        reachable.add(dest)
                        queue.append(dest)

        # Get all state names
        all_states = set()
        for state in states:
            if isinstance(state, dict):
                if "children" in state:
                    parent_name = state["name"]
                    for child in state["children"]:
                        all_states.add(f"{parent_name}_{child['name']}")
                else:
                    all_states.add(state["name"])
            else:
                all_states.add(state)

        # Check all states are reachable
        unreachable = all_states - reachable
        assert len(unreachable) == 0, f"Unreachable states: {unreachable}"

    def test_no_invalid_transition_sources(self):
        """Test all transition sources reference valid states."""
        # Get all valid state names
        valid_states = set()
        for state in states:
            if isinstance(state, dict):
                if "children" in state:
                    parent_name = state["name"]
                    for child in state["children"]:
                        valid_states.add(f"{parent_name}_{child['name']}")
                else:
                    valid_states.add(state["name"])
            else:
                valid_states.add(state)

        # Check all transition sources are valid
        for transition in transitions:
            source = transition["source"]
            assert source in valid_states, f"Invalid transition source: {source}"

    def test_no_invalid_transition_destinations(self):
        """Test all transition destinations reference valid states."""
        # Get all valid state names
        valid_states = set()
        for state in states:
            if isinstance(state, dict):
                if "children" in state:
                    parent_name = state["name"]
                    for child in state["children"]:
                        valid_states.add(f"{parent_name}_{child['name']}")
                else:
                    valid_states.add(state["name"])
            else:
                valid_states.add(state)

        # Check all transition destinations are valid
        for transition in transitions:
            dest = transition["dest"]
            assert dest in valid_states, f"Invalid transition destination: {dest}"

    def test_done_state_has_no_outgoing_transitions(self):
        """Test 'done' state has no outgoing transitions (true terminal state)."""
        for transition in transitions:
            source = transition["source"]
            assert source != "done", "Terminal 'done' state should not have outgoing transitions"

    def test_working_states_are_entry_points(self):
        """Test all initial states can be entered (have incoming transitions or are initial)."""
        initial_states = []
        for state in states:
            if isinstance(state, dict) and "children" in state:
                parent_name = state["name"]
                initial_substate = state["initial"]
                initial_states.append(f"{parent_name}_{initial_substate}")

        # Check each initial state
        for initial_state in initial_states:
            # Either it's the initial state or it has incoming transitions
            has_incoming = initial_state == INITIAL_STATE

            if not has_incoming:
                for transition in transitions:
                    if transition["dest"] == initial_state:
                        has_incoming = True
                        break

            assert has_incoming, f"Initial state {initial_state} has no incoming transitions"


class TestStateNamingConventions:
    """Test state naming conventions and consistency."""

    def test_phase_names_follow_convention(self):
        """Test phase names follow naming conventions."""
        expected_phases = ["gatherrequirements", "gitsetup", "planning", "scaffolding", "coding", "testing", "finalize"]

        actual_phases = []
        for state in states:
            if isinstance(state, dict) and "children" in state:
                actual_phases.append(state["name"])

        assert actual_phases == expected_phases

    def test_substate_names_follow_convention(self):
        """Test substate names follow naming conventions."""
        expected_substates = ["working", "aireview", "devreview", "verified"]

        for child in review_lifecycle_children:
            assert child["name"] in expected_substates

    def test_composite_state_names_follow_convention(self):
        """Test composite state names follow phase_substate convention."""
        # Get all composite state names from transitions
        composite_states = set()
        for transition in transitions:
            source = transition["source"]
            dest = transition["dest"]

            if "_" in source:
                composite_states.add(source)
            if "_" in dest and dest != "done":
                composite_states.add(dest)

        # Test each follows the pattern
        for state_name in composite_states:
            parts = state_name.split("_")
            assert len(parts) >= 2, f"State {state_name} should have at least one underscore"

            phase = parts[0]
            substate = "_".join(parts[1:])  # Handle multi-part substates like "strategy_devreview"
            assert phase in ["gatherrequirements", "gitsetup", "planning", "scaffolding", "coding", "testing", "finalize"], f"Invalid phase: {phase}"

            # Planning has special substates, others use standard review lifecycle
            if phase == "planning":
                valid_substates = ["strategy", "strategydevreview", "solutiondesign", "solutiondesigndevreview", "executionplan", "executionplandevreview", "verified"]
                assert substate in valid_substates, f"Invalid planning substate: {substate}"
            else:
                assert len(parts) == 2, f"Non-planning state {state_name} should have exactly one underscore"
                assert substate in ["working", "aireview", "devreview", "verified"], f"Invalid substate: {substate}"
