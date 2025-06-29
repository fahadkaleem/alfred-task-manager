#!/usr/bin/env python
"""Simple test for AL-11 dual-mode persona system."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.alfred.core.prompter import Prompter
from src.alfred.models.config import PersonaConfig
from src.alfred.models.planning_artifacts import (
    ContextAnalysisArtifact,
    StrategyArtifact,
    DesignArtifact
)
import yaml

def test_prompter():
    """Test the Prompter with both personas."""
    
    print("\n" + "="*80)
    print("TESTING AL-11 DUAL-MODE PERSONA SYSTEM")
    print("="*80)
    
    # Load personas
    personas = {
        "onboarding": Path("src/alfred/personas/onboarding.yml"),
        "planning": Path("src/alfred/personas/planning.yml")
    }
    
    for persona_name, persona_path in personas.items():
        print(f"\n### Testing {persona_name} persona ###")
        
        if not persona_path.exists():
            print(f"✗ Persona file not found: {persona_path}")
            continue
            
        # Load persona
        with open(persona_path) as f:
            persona_data = yaml.safe_load(f)
        persona = PersonaConfig(**persona_data)
        
        print(f"✓ Loaded persona: {persona.name}")
        
        # Create prompter
        prompter = Prompter()
        
        # Test states based on persona type
        if persona_name == "onboarding":
            states = ["initialized", "ready"]
            tool_name = "start_task"
        else:
            states = ["initialized", "contextualize", "awaiting_ai_review", "awaiting_human_review", "strategize", "design", "generate_subtasks"]
            tool_name = "plan_task"
        
        for state in states:
            print(f"\n  Testing state: {state}")
            
            # Prepare additional context based on state
            additional_context = {}
            if state == "awaiting_ai_review":
                additional_context["artifact_content"] = json.dumps({
                    "context_summary": "Test context",
                    "affected_files": ["test.py"],
                    "questions_for_developer": ["Test question?"]
                })
            elif state == "awaiting_human_review":
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
            
            try:
                # Generate prompt
                prompt = prompter.generate_prompt(
                    task={"task_id": "TEST-01"},
                    tool_name=tool_name,
                    state=state,
                    additional_context=additional_context,
                    persona_config=persona.model_dump()
                )
                
                # Check for key elements
                checks = []
                
                # Check for AI directives
                if "AI Agent Instructions" in prompt:
                    checks.append("✓ AI directives found")
                else:
                    checks.append("✗ AI directives NOT found")
                
                # Check for persona greeting (human mode)
                if persona.human and persona.human.greeting and persona.human.greeting in prompt:
                    checks.append("✓ Persona greeting found")
                elif "ROLE:" in prompt and persona.name in prompt:
                    checks.append("✓ Persona role found")
                else:
                    checks.append("✗ Persona human content NOT found")
                
                # Check for analysis patterns in AI sections
                if "Required Analysis Steps:" in prompt:
                    checks.append("✓ Analysis patterns section found")
                    
                # Check for validation criteria in AI sections  
                if "Self-Validation Checklist:" in prompt:
                    checks.append("✓ Validation criteria section found")
                
                # Print results
                for check in checks:
                    print(f"    {check}")
                    
                # Print prompt snippet for debugging
                if "✗" in " ".join(checks):
                    print(f"\n    Prompt snippet (first 500 chars):")
                    print("    " + "-"*40)
                    print("    " + prompt[:500].replace("\n", "\n    "))
                    print("    " + "-"*40)
                    
            except Exception as e:
                print(f"    ✗ Error: {e}")
                import traceback
                traceback.print_exc()

def main():
    """Run the test."""
    test_prompter()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()