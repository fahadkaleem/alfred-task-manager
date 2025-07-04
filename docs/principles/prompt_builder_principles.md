# **ALFRED PROMPT BUILDER PRINCIPLES**

## **CORE PHILOSOPHY**
Prompt building is **DETERMINISTIC ASSEMBLY, not DYNAMIC GENERATION**. Templates are data, context is data, prompts are predictable combinations.

## **THE GOLDEN RULES**

### **1. CONSOLIDATION OVER DUPLICATION**
- **ONE SYSTEM ONLY**: File-based templates with `PromptLibrary`
- Kill the class-based template system completely
- All prompts come from `.md` files in `prompts/` directory
- No exceptions, no fallbacks, no dual systems

### **2. TEMPLATE RESOLUTION IS EXPLICIT**
```python
Template path formula (NEVER CHANGE):
prompts/{tool_name}/{state}.md

Examples:
- prompts/plan_task/contextualize.md
- prompts/implement_task/dispatching.md
- prompts/review_task/working.md
```

### **3. VARIABLE SUBSTITUTION IS SIMPLE**
- Use `string.Template` for variable substitution
- Variables follow `${variable_name}` format
- No Jinja2, no complex templating logic
- No conditional rendering, no loops

### **4. CONTEXT BUILDERS ARE PURE FUNCTIONS**
```python
Context builder requirements:
- Take (task, task_state, **kwargs) → return dict
- No side effects or state mutations
- No external API calls or file operations
- Deterministic output for same inputs
```

### **5. TEMPLATE CACHING IS TRANSPARENT**
- Templates loaded once at startup
- Cache invalidation only on restart
- No hot-reloading in production
- File changes require server restart

### **6. VARIABLE VALIDATION IS MANDATORY**
- All template variables must be provided
- Missing variables cause immediate failure
- No default substitutions or silent failures
- Clear error messages with variable names

## **WHEN WORKING WITH PROMPTS**

### **DO:**
- ✅ Use `PromptLibrary.render_template()` for all prompts
- ✅ Create pure function context builders
- ✅ Follow exact template path formula
- ✅ Validate all required variables provided
- ✅ Use simple `${variable}` substitution
- ✅ Fail fast on missing templates or variables

### **DON'T:**
- ❌ Create class-based templates
- ❌ Add complex templating logic
- ❌ Implement dynamic template paths
- ❌ Cache context data
- ❌ Add fallback template systems
- ❌ Use conditional template rendering

## **PROMPT BUILDING PATTERNS**

### **Simple Template Rendering**
```python
# GOOD - Standard template rendering
def build_planning_prompt(task: Task, state: TaskState) -> str:
    context = {
        "task_id": task.task_id,
        "task_title": task.title,
        "task_context": task.context,
        "current_state": "contextualize"
    }
    
    return PromptLibrary.render_template(
        tool_name="plan_task",
        state="contextualize", 
        context=context
    )

# BAD - Dynamic template selection
def build_planning_prompt(task: Task, state: TaskState) -> str:
    template_name = f"planning_{task.priority.lower()}"  # NO!
    if task.complexity > 5:
        template_name += "_complex"  # NO!
    return PromptLibrary.render_template(template_name, context)
```

### **Context Builder Pattern**
```python
# GOOD - Pure context builder
def build_implementation_context(task: Task, task_state: TaskState) -> dict:
    execution_plan = task_state.get_artifact("execution_plan")
    if not execution_plan:
        raise ValueError("Missing required artifact: execution_plan")
    
    return {
        "task_id": task.task_id,
        "execution_plan": json.dumps(execution_plan, indent=2),
        "task_context": task.context,
        "implementation_details": task.implementation_details
    }

# BAD - Stateful context builder
def build_implementation_context(task: Task, task_state: TaskState) -> dict:
    global last_context  # NO! No global state
    cache.set(task.task_id, task_state)  # NO! No side effects
    return {...}
```

## **TEMPLATE STRUCTURE ENFORCEMENT**

### **Required Template Sections**
Every template MUST have these sections:
```markdown
# CONTEXT
# OBJECTIVE  
# BACKGROUND
# INSTRUCTIONS
# CONSTRAINTS
# OUTPUT
# EXAMPLES
```

### **Variable Documentation**
Every template MUST start with this header:
```markdown
<!--
Template: {tool_name}.{state}
Purpose: [Description]
Variables:
  - task_id: Task identifier
  - task_title: Task title
  - [All other variables]
-->
```

## **ERROR HANDLING PATTERNS**

### **Template Not Found**
```python
# Clear, actionable error messages
try:
    template = PromptLibrary.get_template("plan_task", "contextualize")
except TemplateNotFoundError:
    raise ToolResponse.error(
        f"Missing template: prompts/plan_task/contextualize.md"
    )
```

### **Missing Variables**
```python
# Fail fast with specific missing variables
try:
    prompt = template.substitute(context)
except KeyError as e:
    missing_var = e.args[0]
    raise ToolResponse.error(
        f"Missing required variable: {missing_var}"
    )
```

## **PROMPT LIBRARY INTERFACE**

### **Core Methods (ONLY these exist)**
```python
class PromptLibrary:
    @classmethod
    def render_template(cls, tool_name: str, state: str, context: dict) -> str:
        """Render template with context - main interface"""
    
    @classmethod  
    def get_template(cls, tool_name: str, state: str) -> Template:
        """Get raw template object - for testing only"""
        
    @classmethod
    def reload_templates(cls) -> None:
        """Reload all templates - development only"""
```

### **"But I need custom prompt logic!"**
No, you need a different template. Create a new template file instead of adding logic.

## **TESTING PROMPT BUILDING**

Test rendering, not template content:

```python
def test_prompt_rendering():
    context = {
        "task_id": "TEST-1",
        "task_title": "Test Task", 
        "task_context": "Test context",
        "current_state": "contextualize"
    }
    
    # Test successful rendering
    prompt = PromptLibrary.render_template(
        "plan_task", "contextualize", context
    )
    assert "TEST-1" in prompt
    assert "Test Task" in prompt
    
    # Test missing variable error
    del context["task_id"]
    with pytest.raises(KeyError):
        PromptLibrary.render_template("plan_task", "contextualize", context)
```

## **TEMPLATE MIGRATION STRATEGY**

### **Phase 1: Consolidation (IMMEDIATE)**
- Remove all class-based template code
- Migrate remaining templates to file-based
- Update all prompt building to use `PromptLibrary`

### **Phase 2: Validation (NEXT)**
- Add template variable validation
- Implement template header checking
- Create template testing utilities

## **THE PROMPT BUILDER PLEDGE**

*"I will not create complex templating systems. I will not add dynamic template logic. I will trust in simple substitution. When I think I need template complexity, I will remember: Complexity in templates leads to debugging nightmares. Simple templates are predictable templates. Predictable templates are maintainable templates."*

## **ENFORCEMENT**

Any PR that:
- Adds class-based templates → REJECTED
- Implements dynamic template paths → REJECTED
- Adds complex templating logic → REJECTED
- Creates template fallback systems → REJECTED
- Bypasses `PromptLibrary` → REJECTED

Templates are data files. Context is data. Prompts are deterministic assembly. Keep it simple.