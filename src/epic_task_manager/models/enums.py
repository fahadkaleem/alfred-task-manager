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
