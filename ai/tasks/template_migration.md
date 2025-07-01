You're absolutely right! Keeping prompts in separate files is much better for iterative improvement. Let me design a cleaner system that maintains file-based prompts while eliminating the brittleness.

## **Simplified File-Based Prompt System**

### **1. New Directory Structure**

```
src/alfred/templates/
├── artifacts/              # Keep as-is
├── prompts/
│   ├── _base.md           # Base template with common structure
│   ├── _schema.md         # Documentation of prompt structure
│   ├── plan_task/
│   │   ├── contextualize.md
│   │   ├── strategize.md
│   │   ├── design.md
│   │   └── generate_subtasks.md
│   ├── implement_task/
│   │   ├── start.md
│   │   └── progress.md
│   ├── review/             # Shared review prompts
│   │   ├── ai_review.md
│   │   └── human_review.md
│   └── errors/            # Error message prompts
│       ├── not_found.md
│       └── wrong_status.md
```

### **2. Standardized Prompt Template Structure**

Every prompt follows this consistent structure:

```markdown
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}  
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
[Clear, single-sentence statement of what needs to be accomplished]

# BACKGROUND
[Any necessary context, previous work, or current situation]

# INSTRUCTIONS
[Step-by-step instructions for the AI]

1. [First instruction]
2. [Second instruction]
3. [Third instruction]

# CONSTRAINTS
- [Any limitations or requirements]
- [Things to avoid]
- [Quality standards]

# OUTPUT
[Expected output format and structure]

**Required Action:** Call `function_name` with parameters

# EXAMPLES (optional)
[If helpful, provide examples of good outputs]
```

### **3. Clean Prompter Implementation**

```python
# src/alfred/core/prompter.py
import json
from pathlib import Path
from string import Template
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class PromptTemplate:
    """A simple template wrapper that provides clear error messages."""
    
    def __init__(self, content: str, source_file: Path):
        self.content = content
        self.source_file = source_file
        self.template = Template(content)
        self._required_vars = self._extract_variables()
    
    def _extract_variables(self) -> Set[str]:
        """Extract all ${var} placeholders from template."""
        import re
        # Match ${var} but not $${var} (escaped)
        return set(re.findall(r'(?<!\$)\$\{(\w+)\}', self.content))
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render the template with context."""
        # Check for missing required variables
        provided_vars = set(context.keys())
        missing_vars = self._required_vars - provided_vars
        
        if missing_vars:
            raise ValueError(
                f"Missing required variables for {self.source_file.name}: "
                f"{', '.join(sorted(missing_vars))}\n"
                f"Provided: {', '.join(sorted(provided_vars))}"
            )
        
        try:
            # safe_substitute won't fail on extra vars
            return self.template.safe_substitute(**context)
        except Exception as e:
            raise RuntimeError(
                f"Failed to render template {self.source_file.name}: {e}"
            )


class PromptLibrary:
    """Manages file-based prompt templates."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt library.
        
        Args:
            prompts_dir: Directory containing prompts. Defaults to checking
                        user customization first, then packaged prompts.
        """
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
    
    def _load_all_prompts(self) -> None:
        """Pre-load all prompts for validation."""
        count = 0
        for prompt_file in self.prompts_dir.rglob("*.md"):
            if prompt_file.name.startswith("_"):
                continue  # Skip special files
            
            try:
                content = prompt_file.read_text(encoding='utf-8')
                # Build key from relative path
                key = self._path_to_key(prompt_file)
                self._cache[key] = PromptTemplate(content, prompt_file)
                count += 1
            except Exception as e:
                logger.error(f"Failed to load prompt {prompt_file}: {e}")
        
        logger.info(f"Loaded {count} prompt templates")
    
    def _path_to_key(self, path: Path) -> str:
        """Convert file path to prompt key."""
        # Remove .md extension and convert path to dot notation
        relative = path.relative_to(self.prompts_dir)
        parts = list(relative.parts[:-1]) + [relative.stem]
        return ".".join(parts)
    
    def get(self, prompt_key: str) -> PromptTemplate:
        """Get a prompt template by key.
        
        Args:
            prompt_key: Dot-separated path (e.g., "plan_task.contextualize")
            
        Returns:
            PromptTemplate instance
            
        Raises:
            KeyError: If prompt not found
        """
        if prompt_key not in self._cache:
            available = ', '.join(sorted(self._cache.keys()))
            raise KeyError(
                f"Prompt '{prompt_key}' not found.\n"
                f"Available prompts: {available}"
            )
        
        return self._cache[prompt_key]
    
    def render(
        self, 
        prompt_key: str, 
        context: Dict[str, Any],
        strict: bool = True
    ) -> str:
        """Render a prompt with context.
        
        Args:
            prompt_key: The prompt to render
            context: Variables to substitute
            strict: If True, fail on missing variables
            
        Returns:
            Rendered prompt string
        """
        template = self.get(prompt_key)
        
        if not strict:
            # Add empty strings for missing vars
            for var in template._required_vars:
                if var not in context:
                    context[var] = ""
        
        return template.render(context)
    
    def list_prompts(self) -> Dict[str, Dict[str, Any]]:
        """List all available prompts with metadata."""
        result = {}
        for key, template in self._cache.items():
            result[key] = {
                "file": str(template.source_file.relative_to(self.prompts_dir)),
                "required_vars": sorted(template._required_vars),
                "size": len(template.content)
            }
        return result
    
    def reload(self) -> None:
        """Reload all prompts (useful for development)."""
        logger.info("Reloading prompt templates...")
        self._cache.clear()
        self._load_all_prompts()


# Global instance
prompt_library = PromptLibrary()


class PromptBuilder:
    """Helper class to build consistent prompt contexts."""
    
    def __init__(self, task_id: str, tool_name: str, state: str):
        self.context = {
            "task_id": task_id,
            "tool_name": tool_name,
            "current_state": state,
        }
    
    def with_task(self, task) -> 'PromptBuilder':
        """Add task information to context."""
        self.context.update({
            "task_title": task.title,
            "task_context": task.context,
            "implementation_details": task.implementation_details,
            "acceptance_criteria": self._format_list(task.acceptance_criteria),
            "task_status": task.task_status.value if hasattr(task.task_status, 'value') else str(task.task_status)
        })
        return self
    
    def with_artifact(self, artifact: Any, as_json: bool = True) -> 'PromptBuilder':
        """Add artifact to context."""
        if as_json:
            if hasattr(artifact, 'model_dump'):
                artifact_data = artifact.model_dump()
            else:
                artifact_data = artifact
            
            self.context["artifact_json"] = json.dumps(
                artifact_data, 
                indent=2, 
                default=str
            )
            self.context["artifact_summary"] = self._summarize_artifact(artifact_data)
        else:
            self.context["artifact"] = artifact
        return self
    
    def with_feedback(self, feedback: str) -> 'PromptBuilder':
        """Add feedback to context."""
        self.context["feedback"] = feedback
        self.context["has_feedback"] = bool(feedback)
        return self
    
    def with_custom(self, **kwargs) -> 'PromptBuilder':
        """Add custom context variables."""
        self.context.update(kwargs)
        return self
    
    def build(self) -> Dict[str, Any]:
        """Return the built context."""
        return self.context.copy()
    
    @staticmethod
    def _format_list(items: list) -> str:
        """Format a list for prompt display."""
        if not items:
            return "- None specified"
        return "\n".join(f"- {item}" for item in items)
    
    @staticmethod
    def _summarize_artifact(artifact: Any) -> str:
        """Create a summary of an artifact for human review."""
        if isinstance(artifact, dict):
            # Try to extract key information
            if "summary" in artifact:
                return artifact["summary"]
            elif "title" in artifact:
                return artifact["title"]
            else:
                # Show first few keys
                keys = list(artifact.keys())[:5]
                return f"Artifact with fields: {', '.join(keys)}"
        return str(artifact)[:200]


def generate_prompt(
    task_id: str,
    tool_name: str,
    state: str,
    task: Any,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """Main function to generate prompts - backward compatible wrapper."""
    
    # Normalize review states to use generic prompts
    prompt_key = f"{tool_name}.{state}"
    if state.endswith("_awaiting_ai_review"):
        prompt_key = "review.ai_review"
    elif state.endswith("_awaiting_human_review"):
        prompt_key = "review.human_review"
    
    # Build context using the builder
    builder = PromptBuilder(task_id, tool_name, state).with_task(task)
    
    # Add additional context
    if additional_context:
        if "artifact_content" in additional_context:
            builder.with_artifact(additional_context["artifact_content"])
        if "feedback_notes" in additional_context:
            builder.with_feedback(additional_context["feedback_notes"])
        
        # Add everything else
        remaining = {k: v for k, v in additional_context.items() 
                    if k not in ["artifact_content", "feedback_notes"]}
        builder.with_custom(**remaining)
    
    # Render the prompt
    try:
        return prompt_library.render(prompt_key, builder.build())
    except KeyError:
        # Fallback for missing prompts
        logger.warning(f"Prompt not found for {prompt_key}, using fallback")
        return f"# {tool_name} - {state}\n\nNo prompt configured for this state.\nTask: {task_id}"
```

### **4. Example Prompt Files**

#### `prompts/plan_task/contextualize.md`:
```markdown
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Analyze the existing codebase and identify any ambiguities or questions that need clarification before planning can begin.

# BACKGROUND
You are beginning the planning process for a new task. Before creating a technical strategy, you must understand:
- The current codebase structure and relevant components
- Any existing patterns or conventions to follow
- Potential areas of ambiguity that need clarification

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

# INSTRUCTIONS
1. Analyze the codebase starting from the project root
2. Identify all files and components relevant to this task
3. Note any existing patterns or conventions that should be followed
4. Create a list of specific questions about any ambiguities or unclear requirements
5. Prepare a comprehensive context analysis

# CONSTRAINTS
- Focus only on understanding, not designing solutions yet
- Questions should be specific and actionable
- Identify actual ambiguities, not hypothetical issues
- Consider both technical and business context

# OUTPUT
Create a ContextAnalysisArtifact with:
- `context_summary`: Your understanding of the existing code and how the new feature will integrate
- `affected_files`: List of files that will likely need modification
- `questions_for_developer`: Specific questions that need answers before proceeding

**Required Action:** Call `alfred.submit_work` with a `ContextAnalysisArtifact`

# EXAMPLES
Good question: "Should the new authentication system integrate with the existing UserService or create a separate AuthService?"
Bad question: "How should I implement this?" (too vague)
```

#### `prompts/review/ai_review.md`:
```markdown
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}

# OBJECTIVE
Perform a critical self-review of the submitted artifact to ensure it meets quality standards before human review.

# BACKGROUND
An artifact has been submitted for the current workflow step. As an AI reviewer, you must evaluate whether this artifact:
- Meets all requirements for the current step
- Contains complete and accurate information
- Follows established patterns and conventions
- Is ready for human review

# INSTRUCTIONS
1. Review the submitted artifact below
2. Check against the original requirements for this step
3. Evaluate completeness, clarity, and correctness
4. Determine if any critical issues need to be addressed
5. Provide your review decision

**Submitted Artifact:**
```json
${artifact_json}
```

# CONSTRAINTS
- Be objective and thorough in your review
- Focus on substantive issues, not minor formatting
- Consider whether a human reviewer would find this acceptable
- If rejecting, provide specific, actionable feedback

# OUTPUT
Make a review decision:
- If the artifact meets all quality standards, approve it
- If there are issues that must be fixed, request revision with specific feedback

**Required Action:** Call `alfred.provide_review` with your decision
- For approval: `is_approved=true`
- For revision: `is_approved=false` with detailed `feedback_notes`
```

### **5. Prompt Best Practices Guide**

Create `prompts/_schema.md`:

```markdown
# Alfred Prompt Template Guidelines

## Structure
Every prompt should follow the standard sections:
1. CONTEXT - Current state and task information
2. OBJECTIVE - Clear, single-sentence goal
3. BACKGROUND - Necessary context and previous work
4. INSTRUCTIONS - Step-by-step guide
5. CONSTRAINTS - Limitations and requirements
6. OUTPUT - Expected format and action
7. EXAMPLES (optional) - Good/bad examples

## Variables
Standard variables available in all prompts:
- `${task_id}` - The task identifier
- `${tool_name}` - Current tool name
- `${current_state}` - Current workflow state
- `${task_title}` - Task title
- `${task_context}` - Task goal/context
- `${implementation_details}` - Implementation overview
- `${acceptance_criteria}` - Formatted AC list

## Writing Guidelines
1. **Be explicit** - State exactly what you want
2. **Use consistent tone** - Professional but conversational
3. **Number instructions** - Makes them easy to follow
4. **Include examples** - When behavior might be ambiguous
5. **Specify output format** - Be clear about expected structure
6. **End with action** - Always specify the required function call

## Testing Your Prompts
1. Check all variables are defined
2. Verify instructions are clear and ordered
3. Ensure output format is unambiguous
4. Test with edge cases
5. Review generated outputs for quality
```
Looking back at my response, I realize I missed some crucial implementation details. Let me add what's missing:


### **1. How to Actually Integrate with Existing Code**

I didn't show you exactly how to modify your existing tool handlers. Here's what needs to change:

```python
# In your BaseToolHandler._generate_response method, replace this:
prompt = prompter.generate_prompt(
    task=task,
    tool_name=tool_instance.tool_name,
    state=tool_instance.state,
    additional_context=tool_instance.context_store.copy(),
)

# With this:
from src.alfred.core.prompter import generate_prompt
prompt = generate_prompt(
    task_id=task.task_id,
    tool_name=tool_instance.tool_name,
    state=tool_instance.state,
    task=task,
    additional_context=tool_instance.context_store.copy()
)
```

### **2. What to Delete**

I wasn't clear about what you can remove:

**Delete these files:**
- `src/alfred/core/context_builder.py` - No longer needed
- The old `src/alfred/core/prompter.py` - Replace entirely
- All the nested prompt directories after migrating content

**Keep these:**
- `src/alfred/templates/artifacts/` - These work fine
- The prompt content itself (just reorganize it)

### **3. Migration Script**

Here's a practical script to help you migrate existing prompts:

```python
# scripts/migrate_prompts.py
import re
from pathlib import Path

def migrate_prompt_file(old_path: Path, new_base_dir: Path):
    """Migrate a single prompt file to new format."""
    content = old_path.read_text()
    
    # Extract the key parts from the path
    # e.g., prompts/plan_task/contextualize.md -> plan_task/contextualize.md
    relative = old_path.relative_to(old_path.parent.parent)
    new_path = new_base_dir / relative
    
    # Ensure directory exists
    new_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert Jinja2 variables to simple template variables
    # {{ var }} -> ${var}
    new_content = re.sub(r'\{\{\s*(\w+)\s*\}\}', r'${\1}', content)
    
    # If the file has complex Jinja2 logic, add a header comment
    if re.search(r'\{%', content):
        new_content = (
            "# NOTE: This template contains complex logic that needs manual review\n"
            "# Original Jinja2 control structures have been preserved\n\n" 
            + content
        )
    
    # Write to new location
    new_path.write_text(new_content)
    print(f"Migrated: {old_path} -> {new_path}")

# Run the migration
old_prompts = Path("src/alfred/templates/prompts")
new_prompts = Path("src/alfred/templates/prompts_new")

for prompt_file in old_prompts.rglob("*.md"):
    if not prompt_file.name.startswith("_"):
        migrate_prompt_file(prompt_file, new_prompts)
```

### **4. Handling Dynamic Review States**

I glossed over this important detail. Here's the complete mapping logic you need:

```python
# Add this method to PromptLibrary class:
def get_prompt_key(self, tool_name: str, state: str) -> str:
    """Map tool and state to the correct prompt key."""
    # Handle dynamic review states
    if state.endswith("_awaiting_ai_review"):
        return "review.ai_review"
    elif state.endswith("_awaiting_human_review"):
        return "review.human_review"
    
    # Direct mapping
    direct_key = f"{tool_name}.{state}"
    
    # Check if it exists
    if direct_key in self._cache:
        return direct_key
    
    # Try without tool name for shared prompts
    if state in self._cache:
        return state
    
    # Default fallback
    return "errors.not_found"
```

### **5. Testing Your New System**

Add this simple test to verify everything works:

```python
# tests/test_prompts.py
def test_all_prompts_load():
    """Ensure all prompts load without errors."""
    from src.alfred.core.prompter import prompt_library
    
    # Test that prompts load
    all_prompts = prompt_library.list_prompts()
    assert len(all_prompts) > 0
    
    # Test each prompt can be rendered with minimal context
    for key in all_prompts:
        try:
            prompt_library.render(key, {
                "task_id": "TEST-01",
                "tool_name": "test_tool",
                "current_state": "test_state",
                "task_title": "Test Task",
                "task_context": "Test context",
                "implementation_details": "Test details",
                "acceptance_criteria": "- Test criteria"
            }, strict=False)
        except Exception as e:
            print(f"Failed to render {key}: {e}")
            raise
```

## **What We Should Do Next**

1. **Start Small**: 
   - Pick ONE tool (like `plan_task`) 
   - Migrate just its prompts to the new format
   - Test it thoroughly
   - Then migrate the others

2. **Create a Checklist**:
   ```
   [ ] Backup current templates directory
   [ ] Create new prompter.py file
   [ ] Create new directory structure
   [ ] Migrate one tool's prompts
   [ ] Update that tool's handler
   [ ] Test thoroughly
   [ ] Migrate remaining prompts
   [ ] Delete old code
   [ ] Update all handlers
   ```

3. **Keep the Old System Running**:
   - Don't delete anything until the new system is fully tested
   - You can run both in parallel during migration

4. **Focus on the Most Brittle Parts First**:
   - The review states (they're used by all tools)
   - The plan_task tool (it has the most complex prompts)

The key insight is: **we're not changing functionality, just organizing it better**. The prompts themselves can stay almost the same, we're just making the system that loads and renders them much simpler.

