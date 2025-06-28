"""
Comprehensive tests for StateManager class covering HSM functionality
"""

import json

import pytest

from epic_task_manager.models.core import StateFile
from epic_task_manager.state.machine import INITIAL_STATE
from epic_task_manager.state.manager import StateManager, TaskAlreadyExistsError, TaskModel, TaskNotFoundError


class TestStateManager:
    """Tests for StateManager HSM functionality following testing guidelines."""

    @pytest.fixture(scope="function")
    def state_manager(self, isolated_epic_settings):
        """Create StateManager with isolated test settings."""
        return StateManager()

    def test_create_machine_initializes_task_in_gatherrequirements_working_state(self, state_manager, sample_task_id, initialized_project):
        """Test create_machine correctly initializes a task in the gatherrequirements_working state."""
        # Create new machine
        machine = state_manager.create_machine(sample_task_id)

        # Verify machine state
        assert machine.state == INITIAL_STATE
        assert machine.state == "gatherrequirements_working"

        # Verify state file was created
        assert initialized_project.state_file.exists()

        # Verify task was saved to state file
        state_data = json.loads(initialized_project.state_file.read_text())
        assert sample_task_id in state_data["tasks"]
        assert state_data["tasks"][sample_task_id]["current_state"] == INITIAL_STATE

    def test_create_machine_raises_error_for_duplicate_task(self, state_manager, sample_task_id):
        """Test ValueError is raised when creating a task that already exists."""
        # Create first machine
        state_manager.create_machine(sample_task_id)

        # Attempt to create duplicate should raise TaskAlreadyExistsError
        with pytest.raises(TaskAlreadyExistsError):
            state_manager.create_machine(sample_task_id)

    def test_get_machine_correctly_retrieves_existing_machine(self, state_manager, sample_task_id):
        """Test get_machine correctly retrieves an existing machine."""
        # Create machine first
        original_machine = state_manager.create_machine(sample_task_id)

        # Retrieve machine
        retrieved_machine = state_manager.get_machine(sample_task_id)

        # Verify machine was retrieved correctly
        assert retrieved_machine is not None
        assert retrieved_machine.state == original_machine.state
        assert retrieved_machine.state == "gatherrequirements_working"

    def test_get_machine_returns_none_for_nonexistent_task(self, state_manager):
        """Test get_machine returns None for nonexistent task."""
        machine = state_manager.get_machine("NONEXISTENT-TASK")
        assert machine is None

    def test_save_machine_state_updates_current_state_and_feedback(self, state_manager, sample_task_id, initialized_project):
        """Test save_machine_state accurately updates current_state and revision_feedback in state.json."""
        # Create and modify machine state
        machine = state_manager.create_machine(sample_task_id)
        machine.submit_for_ai_review()  # Transition to aireview state

        feedback_message = "Please add more details to the implementation"

        # Save the updated state with feedback
        state_manager.save_machine_state(sample_task_id, machine, feedback_message)

        # Verify state file was updated
        state_data = json.loads(initialized_project.state_file.read_text())
        task_state = state_data["tasks"][sample_task_id]

        assert task_state["current_state"] == "gatherrequirements_verified"
        assert task_state["revision_feedback"] == feedback_message

    def test_save_machine_state_raises_error_for_nonexistent_task(self, state_manager):
        """Test save_machine_state raises ValueError for nonexistent task."""
        fake_machine = TaskModel()
        fake_machine.state = "gatherrequirements_working"

        with pytest.raises(TaskNotFoundError):
            state_manager.save_machine_state("NONEXISTENT", fake_machine)

    def test_load_state_file_handles_missing_file(self, state_manager, initialized_project):
        """Test _load_state_file returns empty StateFile when file doesn't exist."""
        # Ensure state file doesn't exist
        if initialized_project.state_file.exists():
            initialized_project.state_file.unlink()

        state_file = state_manager._load_state_file()

        assert isinstance(state_file, StateFile)
        assert len(state_file.tasks) == 0

    def test_load_state_file_handles_corrupted_json(self, state_manager, initialized_project):
        """Test _load_state_file handles corrupted JSON gracefully."""
        # Create corrupted JSON file
        initialized_project.state_file.parent.mkdir(parents=True, exist_ok=True)
        initialized_project.state_file.write_text("invalid json content")

        state_file = state_manager._load_state_file()

        assert isinstance(state_file, StateFile)
        assert len(state_file.tasks) == 0

    def test_save_state_file_creates_directory_if_missing(self, state_manager, initialized_project):
        """Test _save_state_file creates parent directory if it doesn't exist."""
        # Remove the entire directory
        if initialized_project.epic_task_manager_dir.exists():
            import shutil

            shutil.rmtree(initialized_project.epic_task_manager_dir)

        # Create and save state file
        state_file = StateFile()
        state_manager._save_state_file(state_file)

        # Verify directory and file were created
        assert initialized_project.epic_task_manager_dir.exists()
        assert initialized_project.state_file.exists()

    def test_state_machine_transitions_work_correctly(self, state_manager, sample_task_id):
        """Test that HSM transitions work correctly through the simplified workflow."""
        # Create machine and verify initial state
        machine = state_manager.create_machine(sample_task_id)
        assert machine.state == "gatherrequirements_working"

        # Test direct transition to verified for requirements
        machine.submit_for_ai_review()
        assert machine.state == "gatherrequirements_verified"

        # Test advancement to next phase (now goes to gitsetup)
        machine.advance()
        assert machine.state == "gitsetup_working"

    def test_state_machine_revision_cycle_works(self, state_manager, sample_task_id):
        """Test that revision requests work correctly for non-simplified phases."""
        machine = state_manager.create_machine(sample_task_id)

        # Advance to coding phase which has full review cycle
        machine.submit_for_ai_review()  # requirements -> verified
        machine.advance()  # gatherrequirements_verified -> gitsetup_working
        machine.submit_for_ai_review()  # gitsetup -> aireview
        machine.ai_approves()  # gitsetup_aireview -> devreview
        machine.human_approves()  # gitsetup_devreview -> verified
        machine.advance()  # gitsetup_verified -> planning_strategy

        # Skip planning phases to get to coding
        machine.submit_for_ai_review()  # strategy -> strategydevreview
        machine.human_approves()  # strategydevreview -> solutiondesign
        machine.submit_for_ai_review()  # solutiondesign -> solutiondesigndevreview
        machine.human_approves()  # solutiondesigndevreview -> executionplan
        machine.submit_for_ai_review()  # executionplan -> executionplandevreview
        machine.human_approves()  # executionplandevreview -> verified
        machine.advance_to_code()  # planning_verified -> coding_working

        # Test revision cycle in coding phase
        machine.submit_for_ai_review()
        assert machine.state == "coding_aireview"

        machine.request_revision()
        assert machine.state == "coding_working"

        # Test revision from dev review
        machine.submit_for_ai_review()
        machine.ai_approves()
        assert machine.state == "coding_devreview"

        machine.request_revision()
        assert machine.state == "coding_working"

    @pytest.mark.parametrize(
        "task_id",
        ["", "VALID-123", "test-task"],
        ids=["empty_task_id", "valid_format", "lowercase_format"],
    )
    def test_create_machine_duplicate_error_messages(self, state_manager, task_id):
        """Test that duplicate task creation raises TaskAlreadyExistsError."""
        # Create first task
        state_manager.create_machine(task_id)

        # Attempt duplicate creation
        with pytest.raises(TaskAlreadyExistsError):
            state_manager.create_machine(task_id)

    def test_concurrent_state_modifications(self, sample_task_id, initialized_project):
        """Test handling of concurrent state modifications."""
        # Create two separate StateManager instances
        manager1 = StateManager()
        manager2 = StateManager()

        # Create task with first manager
        machine1 = manager1.create_machine(sample_task_id)

        # Get task with second manager
        manager2.get_machine(sample_task_id)

        # Modify state with first manager
        machine1.submit_for_ai_review()
        manager1.save_machine_state(sample_task_id, machine1)

        # Verify second manager can load updated state
        updated_machine2 = manager2.get_machine(sample_task_id)
        assert updated_machine2.state == "gatherrequirements_verified"
