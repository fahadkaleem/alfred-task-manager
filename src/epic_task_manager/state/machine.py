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
