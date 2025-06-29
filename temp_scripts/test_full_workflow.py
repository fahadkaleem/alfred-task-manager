#!/usr/bin/env python
"""Test full workflow for AL-11 dual-mode persona system."""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.alfred.core.prompter import Prompter
from src.alfred.models.config import PersonaConfig
from src.alfred.models.planning_artifacts import (
    ContextAnalysisArtifact,
    StrategyArtifact,
    DesignArtifact,
    ExecutionPlanArtifact
)
from src.alfred.models.schemas import Subtask
from src.alfred.tools.start_task import StartTaskTool
from src.alfred.tools.plan_task import PlanTaskTool
from pydantic import BaseModel

class TestContext:
    """Context for testing."""
    
    def __init__(self, task_id, task_type="plan_task"):
        self.task_id = task_id
        self.task_type = task_type
        self.current_state = None
        self.artifacts = {}
        
    def log(self, message):
        """Log message with context."""
        print(f"[{self.task_id}:{self.current_state}] {message}")
        
    def log_prompt(self, prompt):
        """Log prompt content."""
        print("\n" + "="*80)
        print(f"PROMPT FOR STATE: {self.current_state}")
        print("="*80)
        print(prompt)
        print("="*80 + "\n")

def test_start_task_workflow():
    """Test start_task workflow with all states."""
    print("\n" + "="*100)
    print("TESTING START_TASK WORKFLOW")
    print("="*100)
    
    context = TestContext("TEST-START-01", "start_task")
    
    # Initialize project directory structure
    project_dir = Path("/tmp/alfred-test-start")
    project_dir.mkdir(exist_ok=True)
    (project_dir / ".alfred").mkdir(exist_ok=True)
    
    # Copy personas
    personas_dir = project_dir / ".alfred" / "personas"
    personas_dir.mkdir(exist_ok=True)
    
    # Copy onboarding persona
    src_persona = Path("src/alfred/personas/onboarding.yml")
    if src_persona.exists():
        (personas_dir / "onboarding.yml").write_text(src_persona.read_text())
    
    # Copy templates
    templates_dir = project_dir / ".alfred" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy start_task templates
    src_templates = Path("src/alfred/templates/prompts/start_task")
    if src_templates.exists():
        dst_templates = templates_dir / "prompts" / "start_task"
        dst_templates.mkdir(parents=True, exist_ok=True)
        for template in src_templates.glob("*.md"):
            (dst_templates / template.name).write_text(template.read_text())
    
    # Create task directory
    task_dir = project_dir / ".alfred" / "tasks" / context.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Create task.json
    task_json = {
        "task_id": context.task_id,
        "status": "planning",
        "type": "task",
        "created_at": "2024-01-01T00:00:00Z"
    }
    (task_dir / "task.json").write_text(json.dumps(task_json, indent=2))
    
    # Test states
    states = ["initialized", "ready"]
    
    os.chdir(project_dir)
    
    for state in states:
        context.current_state = state
        context.log(f"Testing state: {state}")
        
        try:
            # Create prompter
            prompter = Prompter()
            
            # Load persona
            persona_path = personas_dir / "onboarding.yml"
            if persona_path.exists():
                import yaml
                with open(persona_path) as f:
                    persona_data = yaml.safe_load(f)
                persona = PersonaConfig(**persona_data)
            else:
                raise Exception(f"Persona file not found: {persona_path}")
            
            # Get AI directives for state
            ai_directives = None
            if hasattr(persona, 'ai') and persona.ai and hasattr(persona.ai, state):
                ai_directives = getattr(persona.ai, state)
            
            # Test context
            test_context = {
                "task": {"task_id": context.task_id},
                "persona": persona,
                "state": state,
                "ai_directives": ai_directives
            }
            
            # Generate prompt
            prompt = prompter.generate_prompt(
                task={"task_id": context.task_id},
                tool_name="start_task" if context.task_type == "start_task" else "plan_task", 
                state=state,
                additional_context=test_context.get("additional_context", {}),
                persona_config=persona.model_dump()
            )
            
            context.log_prompt(prompt)
            
            # Check for AI directives
            if "AI Agent Instructions" in prompt:
                context.log("✓ AI directives found")
            else:
                context.log("✗ AI directives NOT found")
                
            # Check for persona fields
            if "greeting" in prompt or prompter.persona.human.greeting in prompt:
                context.log("✓ Persona greeting found")
            else:
                context.log("✗ Persona greeting NOT found")
                
        except Exception as e:
            context.log(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

def test_plan_task_workflow():
    """Test plan_task workflow with all states."""
    print("\n" + "="*100)
    print("TESTING PLAN_TASK WORKFLOW")
    print("="*100)
    
    context = TestContext("TEST-PLAN-01", "plan_task")
    
    # Initialize project directory structure
    project_dir = Path("/tmp/alfred-test-plan")
    project_dir.mkdir(exist_ok=True)
    (project_dir / ".alfred").mkdir(exist_ok=True)
    
    # Copy personas
    personas_dir = project_dir / ".alfred" / "personas"
    personas_dir.mkdir(exist_ok=True)
    
    # Copy planning persona
    src_persona = Path("src/alfred/personas/planning.yml")
    if src_persona.exists():
        (personas_dir / "planning.yml").write_text(src_persona.read_text())
    
    # Copy templates
    templates_dir = project_dir / ".alfred" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy plan_task templates
    src_templates = Path("src/alfred/templates/prompts/plan_task")
    if src_templates.exists():
        dst_templates = templates_dir / "prompts" / "plan_task"
        dst_templates.mkdir(parents=True, exist_ok=True)
        for template in src_templates.glob("*.md"):
            (dst_templates / template.name).write_text(template.read_text())
    
    # Create task directory
    task_dir = project_dir / ".alfred" / "tasks" / context.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Create task.json
    task_json = {
        "task_id": context.task_id,
        "status": "planning",
        "type": "task",
        "created_at": "2024-01-01T00:00:00Z"
    }
    (task_dir / "task.json").write_text(json.dumps(task_json, indent=2))
    
    # Test states with proper artifacts
    states_and_artifacts = [
        ("initialized", {}),
        ("contextualize", {}),
        ("awaiting_ai_review", {
            "artifact_content": json.dumps({
                "context_summary": "Test context",
                "affected_files": ["test.py"],
                "questions": ["Test question?"]
            })
        }),
        ("awaiting_human_review", {
            "artifact_content": json.dumps({
                "context_summary": "Test context",
                "affected_files": ["test.py"],
                "questions": ["Test question?"]
            })
        }),
        ("strategize", {
            "context_artifact": ContextAnalysisArtifact(
                context_summary="Test context",
                affected_files=["test.py"],
                questions_for_developer=["Test question?"]
            )
        }),
        ("design", {
            "strategy_artifact": StrategyArtifact(
                high_level_strategy="Test approach",
                key_components=["component1", "component2"],
                new_dependencies=[],
                risk_analysis="Test risk analysis"
            )
        }),
        ("generate_subtasks", {
            "design_artifact": DesignArtifact(
                design_summary="Test design",
                file_breakdown=[]
            )
        })
    ]
    
    os.chdir(project_dir)
    
    for state, artifacts in states_and_artifacts:
        context.current_state = state
        context.log(f"Testing state: {state}")
        
        try:
            # Create prompter
            prompter = Prompter()
            
            # Load persona
            persona_path = personas_dir / "planning.yml"
            if persona_path.exists():
                import yaml
                with open(persona_path) as f:
                    persona_data = yaml.safe_load(f)
                persona = PersonaConfig(**persona_data)
            else:
                raise Exception(f"Persona file not found: {persona_path}")
            
            # Get AI directives for state
            ai_directives = None
            if hasattr(persona, 'ai') and persona.ai and hasattr(persona.ai, state):
                ai_directives = getattr(persona.ai, state)
            
            # Test context
            test_context = {
                "task": {"task_id": context.task_id},
                "persona": persona,
                "state": state,
                "additional_context": artifacts,
                "ai_directives": ai_directives
            }
            
            # Generate prompt
            prompt = prompter.generate_prompt(
                task={"task_id": context.task_id},
                tool_name="start_task" if context.task_type == "start_task" else "plan_task", 
                state=state,
                additional_context=test_context.get("additional_context", {}),
                persona_config=persona.model_dump()
            )
            
            context.log_prompt(prompt)
            
            # Check for AI directives
            if "AI Agent Instructions" in prompt:
                context.log("✓ AI directives found")
            else:
                context.log("✗ AI directives NOT found")
                
            # Check for persona fields
            if "greeting" in prompt or prompter.persona.human.greeting in prompt:
                context.log("✓ Persona greeting found")
            else:
                context.log("✗ Persona greeting NOT found")
                
        except Exception as e:
            context.log(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Run all workflow tests."""
    print("Testing AL-11 Dual-Mode Persona System")
    print("=====================================")
    
    # Test both workflows
    test_start_task_workflow()
    test_plan_task_workflow()
    
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    print("Check the logs above for:")
    print("1. AI directives presence in each state")
    print("2. Persona fields rendering correctly")
    print("3. No template errors or undefined variables")
    print("4. Proper JSON serialization of Pydantic models")

if __name__ == "__main__":
    main()