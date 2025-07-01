# CRITICAL REFACTORING INSTRUCTION: Step 4 - Unify Prompt System with Template Inheritance

**ATTENTION**: This is the fourth CRITICAL refactoring task. We need to reduce prompt template duplication while respecting the existing template principles. Many prompts share 80% of their content but are completely duplicated. Triple check that all prompts still render correctly after refactoring.

## OBJECTIVE
Create a template inheritance system that eliminates duplication while maintaining the strict template principles (simple variable substitution only, no logic in templates).

## CURRENT PROBLEM
Looking at the prompt templates:
- Many prompts have identical CONTEXT sections
- CONSTRAINTS sections are often repeated
- OUTPUT sections follow similar patterns
- ~30 prompt files with ~70% duplication
- Same boilerplate repeated everywhere

Example duplication:
- Every workflow prompt starts with the same CONTEXT format
- Every review prompt has similar structure
- Every "awaiting" state has similar instructions

## STEP-BY-STEP IMPLEMENTATION

### 1. Create Base Template Classes
**CREATE** a new file: `src/alfred/core/template_base.py`

```python
"""
Base template system for reducing prompt duplication.

This system respects the template principles:
- Templates are data, not code
- Simple variable substitution only
- No conditional logic in templates
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class TemplateSection:
    """Represents a single section of a template."""
    
    def __init__(self, name: str, content: str = ""):
        self.name = name
        self.content = content
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render this section with variable substitution."""
        if not self.content:
            return ""
        
        # Simple variable substitution using regex
        def replace_var(match):
            var_name = match.group(1)
            if var_name in context:
                value = context[var_name]
                return str(value) if value is not None else ""
            return match.group(0)  # Return unchanged if var not found
        
        rendered = re.sub(r'\$\{(\w+)\}', replace_var, self.content)
        return f"# {self.name}\n{rendered}"


class BasePromptTemplate(ABC):
    """
    Base class for all prompt templates.
    
    This provides the standard structure while allowing customization
    of individual sections. No logic in templates - only data.
    """
    
    # Standard sections in order
    SECTION_NAMES = [
        "CONTEXT",
        "OBJECTIVE", 
        "BACKGROUND",
        "INSTRUCTIONS",
        "CONSTRAINTS",
        "OUTPUT",
        "EXAMPLES"
    ]
    
    def __init__(self):
        self.sections: Dict[str, TemplateSection] = {}
        self._initialize_sections()
    
    def _initialize_sections(self):
        """Initialize all sections, subclasses override to provide content."""
        for section_name in self.SECTION_NAMES:
            method_name = f"_get_{section_name.lower()}_content"
            if hasattr(self, method_name):
                content = getattr(self, method_name)()
            else:
                content = ""
            self.sections[section_name] = TemplateSection(section_name, content)
    
    @abstractmethod
    def get_required_variables(self) -> List[str]:
        """Return list of required variables for this template."""
        pass
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render the complete template with the given context."""
        # Validate required variables
        required = set(self.get_required_variables())
        provided = set(context.keys())
        missing = required - provided
        
        if missing:
            raise ValueError(
                f"Missing required variables: {', '.join(sorted(missing))}\n"
                f"Required: {', '.join(sorted(required))}\n"
                f"Provided: {', '.join(sorted(provided))}"
            )
        
        # Render each section
        rendered_sections = []
        for section_name in self.SECTION_NAMES:
            if section_name in self.sections:
                rendered = self.sections[section_name].render(context)
                if rendered:  # Only include non-empty sections
                    rendered_sections.append(rendered)
        
        return "\n\n".join(rendered_sections)


class WorkflowPromptTemplate(BasePromptTemplate):
    """Base template for all workflow state prompts."""
    
    def _get_context_content(self) -> str:
        """Standard context section for workflow prompts."""
        return """Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}"""
    
    def get_required_variables(self) -> List[str]:
        """Base required variables for workflow prompts."""
        return [
            "task_id",
            "tool_name", 
            "current_state",
            "task_title"
        ]


class WorkflowWithTaskDetailsTemplate(WorkflowPromptTemplate):
    """Base template for workflow prompts that need task details."""
    
    def _get_background_content(self) -> str:
        """Standard background with task details."""
        return """**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}"""
    
    def get_required_variables(self) -> List[str]:
        """Extended required variables including task details."""
        base_vars = super().get_required_variables()
        return base_vars + [
            "task_context",
            "implementation_details",
            "acceptance_criteria",
            "feedback_section"
        ]


class SubmitWorkPromptTemplate(WorkflowWithTaskDetailsTemplate):
    """Base template for prompts that end with submit_work."""
    
    def _get_output_content(self) -> str:
        """Standard output section for submit_work prompts."""
        return """Create a ${artifact_type} with:
${artifact_fields}

**Required Action:** Call `alfred.submit_work` with a `${artifact_type}`"""
    
    def get_required_variables(self) -> List[str]:
        """Add artifact-related variables."""
        base_vars = super().get_required_variables()
        return base_vars + ["artifact_type", "artifact_fields"]


class ReviewPromptTemplate(BasePromptTemplate):
    """Base template for review state prompts."""
    
    def _get_context_content(self) -> str:
        """Standard context for review prompts."""
        return """Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}"""
    
    def _get_objective_content(self) -> str:
        """Standard objective for review prompts."""
        return """${review_objective}"""
    
    def _get_background_content(self) -> str:
        """Standard background for review prompts."""
        return """${review_background}"""
    
    def _get_constraints_content(self) -> str:
        """Standard constraints for review prompts."""
        return """- ${review_constraints}"""
    
    def _get_output_content(self) -> str:
        """Standard output for review prompts."""
        return """${review_action}

**Required Action:** Call `alfred.provide_review` with your decision
- For approval: `is_approved=true`
- For revision: `is_approved=false` with detailed `feedback_notes`"""
    
    def get_required_variables(self) -> List[str]:
        return [
            "task_id",
            "tool_name",
            "current_state",
            "review_objective",
            "review_background",
            "review_constraints",
            "review_action"
        ]
```

### 2. Create Concrete Template Classes
**CREATE** a new file: `src/alfred/core/prompt_templates.py`

```python
"""
Concrete prompt template implementations.

Each template is a data structure - no logic, just content definition.
"""
from src.alfred.core.template_base import (
    WorkflowPromptTemplate,
    WorkflowWithTaskDetailsTemplate,
    SubmitWorkPromptTemplate,
    ReviewPromptTemplate
)


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
        base_vars.remove("artifact_type")
        base_vars.remove("artifact_fields")
        return base_vars


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
        return base_vars + [
            "dispatch_objective",
            "dispatch_context", 
            "dispatch_instructions",
            "dispatch_action",
            "artifact_type",
            "artifact_requirements"
        ]
```

### 3. Create Template Registry
**CREATE** a new file: `src/alfred/core/template_registry.py`

```python
"""
Registry for mapping states to template classes.

This maintains the explicit path principle - each state maps to one template.
"""
from typing import Dict, Type, Optional

from src.alfred.core.template_base import BasePromptTemplate
from src.alfred.core.prompt_templates import (
    PlanTaskContextualizeTemplate,
    PlanTaskStrategizeTemplate,
    AIReviewTemplate,
    HumanReviewTemplate,
    SimpleDispatchingTemplate
)


class TemplateRegistry:
    """Maps tool.state combinations to template classes."""
    
    def __init__(self):
        self._templates: Dict[str, Type[BasePromptTemplate]] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register all default templates."""
        # Plan task templates
        self.register("plan_task.contextualize", PlanTaskContextualizeTemplate)
        self.register("plan_task.strategize", PlanTaskStrategizeTemplate)
        
        # Generic review templates
        self.register("review.ai_review", AIReviewTemplate)
        self.register("review.human_review", HumanReviewTemplate)
        
        # Add more registrations as we migrate templates
    
    def register(self, key: str, template_class: Type[BasePromptTemplate]):
        """Register a template class for a tool.state combination."""
        self._templates[key] = template_class
    
    def get_template(self, tool_name: str, state: str) -> Optional[Type[BasePromptTemplate]]:
        """Get template class for the given tool and state."""
        # Try exact match first
        key = f"{tool_name}.{state}"
        if key in self._templates:
            return self._templates[key]
        
        # Handle review states
        if state.endswith("_awaiting_ai_review"):
            return self._templates.get("review.ai_review")
        elif state.endswith("_awaiting_human_review"):
            return self._templates.get("review.human_review")
        
        return None
    
    def has_template_class(self, tool_name: str, state: str) -> bool:
        """Check if a template class exists for this state."""
        return self.get_template(tool_name, state) is not None


template_registry = TemplateRegistry()
```

### 4. Update Prompter to Use Templates
**UPDATE** `src/alfred/core/prompter.py`:

```python
# Add imports at the top
from src.alfred.core.template_registry import template_registry

# Update the PromptLibrary class
class PromptLibrary:
    """Manages file-based prompt templates with template class fallback."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt library."""
        if prompts_dir is None:
            # Check for user customization first
            user_prompts = settings.alfred_dir / "templates" / "prompts"
            if user_prompts.exists():
                prompts_dir = user_prompts
                logger.info(f"Using user prompt templates from {user_prompts}")
            else:
                # Fall back to packaged prompts
                prompts_dir = Path(__file__).parent.parent / "templates" / "prompts"
                logger.info(f"Using default prompt templates from {prompts_dir}")
        
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, PromptTemplate] = {}
        self._load_all_prompts()
    
    def get(self, prompt_key: str, context: Dict[str, Any] = None) -> Union[PromptTemplate, str]:
        """
        Get a prompt template by key.
        
        First checks for file-based template, then falls back to template class.
        """
        # Check file-based cache first
        if prompt_key in self._cache:
            return self._cache[prompt_key]
        
        # Check if we have a template class
        if context and "." in prompt_key:
            tool_name, state = prompt_key.rsplit(".", 1)
            template_class = template_registry.get_template(tool_name, state)
            if template_class:
                # Render directly from template class
                template_instance = template_class()
                return template_instance.render(context)
        
        # Fallback to not found
        available = ", ".join(sorted(self._cache.keys()))
        raise KeyError(
            f"Prompt '{prompt_key}' not found in files or template registry.\n"
            f"Available file prompts: {available}"
        )
    
    def render(self, prompt_key: str, context: Dict[str, Any], strict: bool = True) -> str:
        """Render a prompt with context."""
        template = self.get(prompt_key, context)
        
        # If we got a string back, it's already rendered
        if isinstance(template, str):
            return template
        
        # Otherwise it's a file-based PromptTemplate
        if not strict:
            # Add empty strings for missing vars
            for var in template._required_vars:
                if var not in context:
                    context[var] = ""
        
        return template.render(context)
```

### 5. Migrate a Few Templates as Examples
**CREATE** migration instructions in a new file: `docs/template_migration.md`

```markdown
# Template Migration Guide

## How to Migrate a Template to the Class System

1. Identify templates with common patterns
2. Create or reuse a base template class
3. Create a concrete implementation
4. Register in template_registry
5. Delete the original .md file (optional - can keep for overrides)

## Benefits of Migration

- 70% less duplication
- Consistent structure
- Easier to maintain
- Still allows file overrides

## Example Migration

### Before (plan_task/contextualize.md):
```markdown
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Analyze the existing codebase...

[... 100 lines total ...]
```

### After (PlanTaskContextualizeTemplate class):
```python
class PlanTaskContextualizeTemplate(SubmitWorkPromptTemplate):
    # Only define what's unique - inherits common sections
    def _get_objective_content(self) -> str:
        return "Analyze the existing codebase..."
    
    # 20 lines total instead of 100
```

## Priority Templates to Migrate

1. All review states (they're nearly identical)
2. All dispatching states  
3. Plan task states (share lots of structure)
4. Implementation/test/finalize states

## Keeping File Override Capability

The system checks files first, then template classes. This means:
- Users can still override with custom .md files
- We can migrate incrementally
- No breaking changes
```

## VERIFICATION CHECKLIST
**CRITICAL**: After implementing this system:

1. ✓ Template classes respect all template principles (no logic, only data)
2. ✓ Variable substitution works exactly as before
3. ✓ File-based templates still take precedence
4. ✓ All required variables are validated
5. ✓ Rendered output is identical to original templates
6. ✓ No Jinja2 or conditional logic in templates
7. ✓ Template registry correctly maps states
8. ✓ Error messages are clear when templates not found

## TESTING REQUIREMENTS

1. **Render Comparison Test**:
```python
def test_template_compatibility():
    """Ensure class templates render identically to file templates."""
    
    # Test context
    context = {
        "task_id": "TEST-1",
        "tool_name": "plan_task",
        "current_state": "contextualize",
        "task_title": "Test Task",
        "task_context": "Test context",
        "implementation_details": "Test details",
        "acceptance_criteria": "- Test AC",
        "feedback_section": ""
    }
    
    # For each migrated template
    for tool_state in ["plan_task.contextualize", "plan_task.strategize"]:
        # Render from file
        file_prompt = prompt_library.render(tool_state, context)
        
        # Render from class
        tool, state = tool_state.split(".")
        template_class = template_registry.get_template(tool, state)
        class_prompt = template_class().render(context)
        
        # Should be very similar (maybe whitespace differences ok)
        assert normalize_whitespace(file_prompt) == normalize_whitespace(class_prompt)
```

2. **Variable Validation Test**:
```python
def test_variable_validation():
    """Ensure missing variables are caught."""
    
    template = PlanTaskContextualizeTemplate()
    
    # Missing required variables
    with pytest.raises(ValueError) as exc:
        template.render({"task_id": "TEST-1"})
    
    assert "Missing required variables" in str(exc.value)
    assert "tool_name" in str(exc.value)
```

## MIGRATION STRATEGY

This is an incremental migration:

1. **Phase 1** (Now): Create the system, migrate 5-10 templates as proof
2. **Phase 2**: Migrate all review states (biggest win - they're all the same)
3. **Phase 3**: Migrate dispatching states
4. **Phase 4**: Migrate remaining workflow states
5. **Phase 5**: Delete migrated .md files (optional)

## EXPECTED OUTCOME

- Template code reduced by ~70%
- Easier to maintain consistent structure
- Still respects all template principles
- No breaking changes for users
- Can still override with custom files

## FINAL CHECK

Count the impact:
- Lines in template .md files: ~3000 lines
- Lines after migration: ~1000 lines 
- **Net reduction: ~2000 lines**

But more importantly:
- Changes to common sections happen in ONE place
- Adding new templates is much easier
- Structure is enforced automatically