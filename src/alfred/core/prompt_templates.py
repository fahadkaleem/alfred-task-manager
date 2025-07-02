"""
Concrete prompt template implementations.

Each template is a data structure - no logic, just content definition.
"""

from typing import List
from src.alfred.core.template_base import WorkflowPromptTemplate, WorkflowWithTaskDetailsTemplate, SubmitWorkPromptTemplate, ReviewPromptTemplate


# Plan Task Templates


class PlanTaskContextualizeTemplate(SubmitWorkPromptTemplate):
    """Template for plan_task.contextualize state."""

    def _get_objective_content(self) -> str:
        return "Analyze the existing codebase and identify any ambiguities or questions that need clarification before planning can begin."

    def _get_instructions_content(self) -> str:
        return """1. Analyze the codebase starting from the project root
2. Identify all files and components relevant to this task
3. Note any existing patterns or conventions that should be followed
4. Create a list of specific questions about any ambiguities or unclear requirements
5. Prepare a comprehensive context analysis"""

    def _get_constraints_content(self) -> str:
        return """- Focus only on understanding, not designing solutions yet
- Questions should be specific and actionable
- Identify actual ambiguities, not hypothetical issues
- Consider both technical and business context"""

    def _get_examples_content(self) -> str:
        return """Good question: "Should the new authentication system integrate with the existing UserService or create a separate AuthService?"
Bad question: "How should I implement this?" (too vague)"""

    def get_required_variables(self) -> List[str]:
        base_vars = super().get_required_variables()
        # Remove generic artifact vars, add specific ones
        filtered_vars = [v for v in base_vars if v not in ["artifact_type", "artifact_fields"]]
        return filtered_vars


class PlanTaskStrategizeTemplate(SubmitWorkPromptTemplate):
    """Template for plan_task.strategize state."""

    def _get_objective_content(self) -> str:
        return "Create a high-level technical strategy that will guide the detailed design and implementation of the task."

    def _get_background_content(self) -> str:
        base = super()._get_background_content()
        return f"""Context has been verified and any necessary clarifications have been provided. You must now develop a technical strategy that:
- Defines the overall approach to solving the problem
- Identifies key components that need to be created or modified
- Considers dependencies and potential risks
- Serves as the foundation for detailed design

{base}"""

    def _get_instructions_content(self) -> str:
        return """1. Review the verified context and requirements
2. Define the overall technical approach (e.g., "Create a new microservice," "Refactor the existing UserService," "Add a new middleware layer")
3. List the major components, classes, or modules that will be created or modified
4. Identify any new third-party libraries or dependencies required
5. Analyze potential risks or important architectural trade-offs
6. Create a concise technical strategy document"""

    def _get_constraints_content(self) -> str:
        return """- Focus on high-level approach, not implementation details
- Ensure the strategy aligns with existing architecture patterns
- Consider scalability, maintainability, and performance
- Be realistic about risks and trade-offs"""


# Review Templates


class AIReviewTemplate(ReviewPromptTemplate):
    """Template for AI review states."""

    def _get_instructions_content(self) -> str:
        return """1. Review the submitted artifact below
2. Check against the original requirements for this step
3. Evaluate completeness, clarity, and correctness
4. Determine if any critical issues need to be addressed
5. Provide your review decision

**Submitted Artifact:**
```json
${artifact_json}
```"""

    def get_required_variables(self) -> List[str]:
        base_vars = super().get_required_variables()
        return base_vars + ["artifact_json"]


class HumanReviewTemplate(ReviewPromptTemplate):
    """Template for human review states."""

    def _get_background_content(self) -> str:
        return """The artifact has passed AI self-review and is now ready for human validation. The human will provide a simple approval decision or request specific changes.

**Artifact Summary:** ${artifact_summary}"""

    def _get_instructions_content(self) -> str:
        return """1. Present the complete artifact below to the human developer
2. Wait for their review decision
3. If they approve, proceed with approval
4. If they request changes, capture their exact feedback
5. Submit the review decision

**Artifact for Review:**
```json
${artifact_json}
```"""

    def _get_constraints_content(self) -> str:
        return """- Present the artifact clearly and completely
- Capture human feedback verbatim if changes are requested
- Do not modify or interpret the human's feedback"""

    def get_required_variables(self) -> List[str]:
        base_vars = super().get_required_variables()
        return base_vars + ["artifact_json", "artifact_summary"]


# Dispatching Templates


class SimpleDispatchingTemplate(WorkflowPromptTemplate):
    """Template for simple dispatching states."""

    def _get_objective_content(self) -> str:
        return "${dispatch_objective}"

    def _get_background_content(self) -> str:
        return "${dispatch_context}"

    def _get_instructions_content(self) -> str:
        return "${dispatch_instructions}"

    def _get_output_content(self) -> str:
        return """Once ${dispatch_action}, call `alfred.submit_work` with ${artifact_type} containing:
${artifact_requirements}"""

    def get_required_variables(self) -> List[str]:
        base_vars = super().get_required_variables()
        return base_vars + ["dispatch_objective", "dispatch_context", "dispatch_instructions", "dispatch_action", "artifact_type", "artifact_requirements"]
