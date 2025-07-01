# **ALFRED TEMPLATE SYSTEM PRINCIPLES**

## **CORE PHILOSOPHY**
Templates are **DATA, not CODE**. They should be as static and predictable as possible.

## **THE GOLDEN RULES**

### **1. NEVER MODIFY TEMPLATE STRUCTURE**
- Templates follow a **STRICT SECTION FORMAT** - do not add, remove, or reorder sections
- The sections are: CONTEXT → OBJECTIVE → BACKGROUND → INSTRUCTIONS → CONSTRAINTS → OUTPUT → EXAMPLES
- If a section doesn't apply, leave it empty - DO NOT REMOVE IT

### **2. TEMPLATES ARE WRITE-ONCE**
- Once a template file is created, its **variables** are FROZEN
- You can edit the text content, but NEVER add new `${variables}`
- If you need new data, pass it through existing variables or create a NEW template

### **3. ONE FILE = ONE PURPOSE**
- Each template file serves **exactly one** state/purpose
- No conditional logic inside templates
- No dynamic content generation
- If you need different content for different scenarios, create separate template files

### **4. VARIABLE NAMING IS SACRED**
```
Standard variables (NEVER RENAME THESE):
- ${task_id}          - The task identifier
- ${tool_name}        - Current tool name  
- ${current_state}    - Current workflow state
- ${task_title}       - Task title
- ${task_context}     - Task goal/context
- ${implementation_details} - Implementation overview
- ${acceptance_criteria}    - Formatted AC list
- ${artifact_json}    - JSON representation of artifacts
- ${feedback}         - Review feedback
```

### **5. NO LOGIC IN TEMPLATES**
- **FORBIDDEN**: `{% if %}`, `{% for %}`, complex Jinja2
- **ALLOWED**: Simple `${variable}` substitution only
- If you need logic, handle it in Python and pass the result as a variable

### **6. EXPLICIT PATHS ONLY**
- Template location = `prompts/{tool_name}/{state}.md`
- No dynamic path construction
- No fallback chains
- If a template doesn't exist, it's an ERROR - don't silently fall back

## **WHEN WORKING WITH TEMPLATES**

### **DO:**
- ✅ Edit prompt text to improve AI behavior
- ✅ Clarify instructions within existing structure  
- ✅ Add examples in the EXAMPLES section
- ✅ Improve formatting for readability
- ✅ Fix typos and grammar

### **DON'T:**
- ❌ Add new variables to existing templates
- ❌ Create dynamic template paths
- ❌ Add conditional logic
- ❌ Merge multiple templates into one
- ❌ Create "smart" template loading logic
- ❌ Mix templates with code generation

## **ADDING NEW FUNCTIONALITY**

### **Need a new prompt?**
1. Create a new file at the correct path: `prompts/{tool_name}/{state}.md`
2. Use ONLY the standard variables listed above
3. Follow the EXACT section structure
4. Test that it renders with standard context

### **Need new data in a prompt?**
1. **STOP** - Can you use existing variables?
2. If absolutely necessary, document the new variable in the template header
3. Update the PromptBuilder to provide this variable
4. Update THIS DOCUMENT with the new standard variable

### **Need conditional behavior?**
1. Create separate template files for each condition
2. Handle the logic in Python code
3. Choose which template to load based on the condition

## **TEMPLATE HEADER REQUIREMENT**

Every template MUST start with this header:

```markdown
<!--
Template: {tool_name}.{state}
Purpose: [One line description]
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  [List ALL variables used in this template]
-->
```

## **TESTING TEMPLATES**

Before committing ANY template change:

1. **Variable Check**: List all `${variables}` in the template
2. **Render Test**: Ensure it renders with standard context
3. **No Logic Check**: Confirm no `{% %}` tags exist
4. **Structure Check**: Verify all sections are present

```python
# Test snippet to include in your tests
def verify_template(template_path):
    content = template_path.read_text()
    
    # No Jinja2 logic
    assert '{%' not in content, "No logic allowed in templates"
    
    # Has all sections
    required_sections = ['# CONTEXT', '# OBJECTIVE', '# BACKGROUND', 
                        '# INSTRUCTIONS', '# CONSTRAINTS', '# OUTPUT']
    for section in required_sections:
        assert section in content, f"Missing {section}"
    
    # Extract variables
    import re
    variables = re.findall(r'\$\{(\w+)\}', content)
    
    # All variables are standard
    standard_vars = {'task_id', 'tool_name', 'current_state', 'task_title',
                    'task_context', 'implementation_details', 'acceptance_criteria',
                    'artifact_json', 'feedback'}
    
    unknown_vars = set(variables) - standard_vars
    assert not unknown_vars, f"Unknown variables: {unknown_vars}"
```

## **ERROR MESSAGES**

When templates fail, the error should be:
- **SPECIFIC**: "Missing required variable 'task_id' in template plan_task.contextualize"
- **ACTIONABLE**: Show what variables were provided vs required
- **TRACEABLE**: Include the template file path

Never:
- Silently fall back to a default
- Generate templates dynamically
- Guess at missing variables

## **THE MAINTENANCE PLEDGE**

*"I will treat templates as immutable contracts. I will not add complexity to make them 'smarter'. I will keep logic in code and content in templates. When in doubt, I will create a new template rather than make an existing one more complex."*

---

**Remember**: Every time you add logic to a template, somewhere a production system breaks at 3 AM. Keep templates simple, predictable, and boring. Boring templates are reliable templates.