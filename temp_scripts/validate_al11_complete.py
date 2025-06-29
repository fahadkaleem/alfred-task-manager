#!/usr/bin/env python
"""Complete validation script for AL-11 dual-mode persona system."""

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.alfred.core.prompter import Prompter
from src.alfred.models.config import PersonaConfig
from src.alfred.models.planning_artifacts import (
    ContextAnalysisArtifact,
    StrategyArtifact,
    DesignArtifact
)

class ValidationResult:
    """Track validation results."""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        
    def add_pass(self, test: str):
        self.passed.append(f"✓ {test}")
        
    def add_fail(self, test: str, reason: str = ""):
        msg = f"✗ {test}"
        if reason:
            msg += f" - {reason}"
        self.failed.append(msg)
        
    def add_warning(self, test: str, reason: str = ""):
        msg = f"⚠ {test}"
        if reason:
            msg += f" - {reason}"
        self.warnings.append(msg)
        
    def print_summary(self):
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\nFAILURES:")
            for fail in self.failed:
                print(f"  {fail}")
                
        if self.warnings:
            print("\nWARNINGS:")
            for warn in self.warnings:
                print(f"  {warn}")
                
        print("\n" + "="*80)
        if not self.failed:
            print("✅ ALL VALIDATIONS PASSED!")
        else:
            print("❌ VALIDATION FAILED!")
        print("="*80)

def load_workflow_config() -> Dict:
    """Load workflow configuration."""
    workflow_path = Path("src/alfred/workflow.yml")
    if not workflow_path.exists():
        workflow_path = Path(".alfred/workflow.yml")
    
    with open(workflow_path) as f:
        return yaml.safe_load(f)

def validate_persona_structure(persona_path: Path, result: ValidationResult) -> PersonaConfig:
    """Validate persona YAML structure."""
    test_name = f"Persona structure: {persona_path.name}"
    
    try:
        with open(persona_path) as f:
            data = yaml.safe_load(f)
        
        # Check for required fields
        if "name" not in data:
            result.add_fail(test_name, "Missing 'name' field")
            return None
            
        if "title" not in data:
            result.add_fail(test_name, "Missing 'title' field")
            return None
            
        # Check for dual-mode structure
        if "human" not in data:
            result.add_fail(test_name, "Missing 'human' section for dual-mode")
            return None
            
        if "ai" not in data:
            result.add_fail(test_name, "Missing 'ai' section for dual-mode")
            return None
            
        # Validate human section
        human = data["human"]
        if "greeting" not in human:
            result.add_fail(test_name, "Missing 'human.greeting'")
            return None
            
        if "communication_style" not in human:
            result.add_fail(test_name, "Missing 'human.communication_style'")
            return None
            
        # Validate AI section
        ai = data["ai"]
        if "style" not in ai:
            result.add_fail(test_name, "Missing 'ai.style'")
            return None
            
        # Try to create PersonaConfig
        persona = PersonaConfig(**data)
        result.add_pass(test_name)
        return persona
        
    except Exception as e:
        result.add_fail(test_name, str(e))
        return None

def validate_template_exists(tool: str, state: str, result: ValidationResult) -> bool:
    """Check if template exists for a given tool and state."""
    test_name = f"Template exists: {tool}/{state}"
    
    # Check both .alfred and src locations
    paths = [
        Path(f".alfred/templates/prompts/{tool}/{state}.md"),
        Path(f"src/alfred/templates/prompts/{tool}/{state}.md")
    ]
    
    for path in paths:
        if path.exists():
            result.add_pass(test_name)
            return True
            
    result.add_fail(test_name, "Template not found in any location")
    return False

def validate_template_content(tool: str, state: str, result: ValidationResult) -> Dict:
    """Validate template content has required sections."""
    test_name = f"Template content: {tool}/{state}"
    
    # Find template
    template_path = None
    for path in [
        Path(f".alfred/templates/prompts/{tool}/{state}.md"),
        Path(f"src/alfred/templates/prompts/{tool}/{state}.md")
    ]:
        if path.exists():
            template_path = path
            break
            
    if not template_path:
        result.add_fail(test_name, "Template not found")
        return {"has_ai_section": False, "has_persona_refs": False}
        
    content = template_path.read_text()
    
    # Check for AI directives section
    has_ai_section = "{% if ai_directives %}" in content or "AI Agent Instructions" in content
    
    # Check for persona references
    has_persona_refs = any([
        "{{ persona.name }}" in content,
        "{{ persona.title }}" in content,
        "{{ persona.human.greeting }}" in content,
        "{% if persona.human %}" in content
    ])
    
    if has_ai_section and has_persona_refs:
        result.add_pass(test_name)
    else:
        issues = []
        if not has_ai_section:
            issues.append("Missing AI directives section")
        if not has_persona_refs:
            issues.append("Missing persona references")
        result.add_fail(test_name, ", ".join(issues))
        
    return {"has_ai_section": has_ai_section, "has_persona_refs": has_persona_refs}

def validate_prompter_generation(tool: str, state: str, persona: PersonaConfig, result: ValidationResult):
    """Validate that Prompter can generate prompts correctly."""
    test_name = f"Prompt generation: {tool}/{state}"
    
    try:
        prompter = Prompter()
        
        # Prepare additional context based on state
        additional_context = {}
        if state in ["awaiting_ai_review", "awaiting_human_review", "review_context", "review_strategy", "review_design", "review_plan"]:
            additional_context["artifact_content"] = json.dumps({
                "context_summary": "Test context",
                "affected_files": ["test.py"],
                "questions_for_developer": ["Test question?"]
            })
        elif state == "strategize":
            additional_context["context_artifact"] = ContextAnalysisArtifact(
                context_summary="Test context",
                affected_files=["test.py"],
                questions_for_developer=["Test question?"]
            )
        elif state == "design":
            additional_context["strategy_artifact"] = StrategyArtifact(
                high_level_strategy="Test approach",
                key_components=["component1", "component2"],
                new_dependencies=[],
                risk_analysis="Test risk analysis"
            )
        elif state == "generate_subtasks":
            additional_context["design_artifact"] = DesignArtifact(
                design_summary="Test design",
                file_breakdown=[]
            )
        
        # Generate prompt
        prompt = prompter.generate_prompt(
            task={"task_id": "TEST-01"},
            tool_name=tool,
            state=state,
            additional_context=additional_context,
            persona_config=persona.model_dump()
        )
        
        # Check if it's an error message
        if "CRITICAL ERROR:" in prompt:
            result.add_fail(test_name, "Template not found or error in generation")
            return
            
        # Validate content
        checks = []
        
        # Check for AI directives
        if "AI Agent Instructions" in prompt:
            checks.append("ai_directives")
            
        # Check for analysis patterns
        if "Required Analysis Steps:" in prompt:
            checks.append("analysis_patterns")
            
        # Check for validation criteria
        if "Self-Validation Checklist:" in prompt:
            checks.append("validation_criteria")
            
        # Check for persona content
        if persona.human and (persona.human.greeting in prompt or persona.name in prompt):
            checks.append("persona_content")
            
        if len(checks) >= 2:  # At least AI directives and persona content
            result.add_pass(test_name)
        else:
            missing = []
            if "ai_directives" not in checks:
                missing.append("AI directives")
            if "persona_content" not in checks:
                missing.append("Persona content")
            result.add_warning(test_name, f"Missing: {', '.join(missing)}")
            
    except Exception as e:
        result.add_fail(test_name, str(e))

def validate_ai_directives_in_persona(persona: PersonaConfig, tool: str, states: List[str], result: ValidationResult):
    """Validate that persona has AI directives for all states."""
    test_name = f"AI directives in persona: {persona.name}"
    
    if not persona.ai:
        result.add_fail(test_name, "No AI section in persona")
        return
        
    missing_analysis = []
    missing_validation = []
    
    for state in states:
        # Check analysis patterns
        if not hasattr(persona.ai, 'analysis_patterns') or state not in persona.ai.analysis_patterns:
            missing_analysis.append(state)
            
        # Check validation criteria
        if not hasattr(persona.ai, 'validation_criteria') or state not in persona.ai.validation_criteria:
            missing_validation.append(state)
            
    if not missing_analysis and not missing_validation:
        result.add_pass(test_name)
    else:
        issues = []
        if missing_analysis:
            issues.append(f"Missing analysis_patterns for: {', '.join(missing_analysis)}")
        if missing_validation:
            issues.append(f"Missing validation_criteria for: {', '.join(missing_validation)}")
        result.add_fail(test_name, "; ".join(issues))

def main():
    """Run complete validation."""
    print("\n" + "="*80)
    print("AL-11 DUAL-MODE PERSONA SYSTEM - COMPLETE VALIDATION")
    print("="*80)
    
    result = ValidationResult()
    
    # Load workflow configuration
    print("\n1. Loading workflow configuration...")
    try:
        workflow = load_workflow_config()
        result.add_pass("Load workflow configuration")
    except Exception as e:
        result.add_fail("Load workflow configuration", str(e))
        result.print_summary()
        return
        
    # Validate each tool
    for tool, config in workflow["tools"].items():
        if tool not in ["start_task", "plan_task"]:  # Skip implement_task for now
            continue
            
        print(f"\n2. Validating {tool}...")
        
        # Load persona
        persona_name = config["persona"]
        persona_path = Path(f"src/alfred/personas/{persona_name}.yml")
        
        print(f"   - Loading {persona_name} persona...")
        persona = validate_persona_structure(persona_path, result)
        if not persona:
            continue
            
        # Get states from workflow
        states = config["states"]
        
        # Validate AI directives in persona
        print(f"   - Validating AI directives for all states...")
        validate_ai_directives_in_persona(persona, tool, states, result)
        
        # Validate each state
        print(f"   - Validating {len(states)} states...")
        for state in states:
            # Skip certain states that don't need templates
            if state in ["completed", "verified"]:
                continue
                
            # Check template exists
            if validate_template_exists(tool, state, result):
                # Check template content
                validate_template_content(tool, state, result)
                
                # Check prompt generation
                validate_prompter_generation(tool, state, persona, result)
    
    # Print final summary
    result.print_summary()
    
    # Write detailed results
    results_file = Path("temp_scripts/al11_validation_results.json")
    results_data = {
        "passed": len(result.passed),
        "failed": len(result.failed),
        "warnings": len(result.warnings),
        "details": {
            "passed": result.passed,
            "failed": result.failed,
            "warnings": result.warnings
        }
    }
    
    with open(results_file, "w") as f:
        json.dump(results_data, f, indent=2)
        
    print(f"\nDetailed results written to: {results_file}")

if __name__ == "__main__":
    main()