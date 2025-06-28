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
