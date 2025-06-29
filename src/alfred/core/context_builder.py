# src/alfred/core/context_builder.py
"""
Context assembly for template rendering during state transitions.

This module ensures proper context is built for both forward progression
and backward revision flows in the feedback loop.
"""
from typing import Dict, Any, Optional
from src.alfred.constants import ArtifactKeys
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """Builds proper context for template rendering based on state transitions."""
    
    @staticmethod
    def build_feedback_context(tool: Any, state: str, feedback_notes: str) -> Dict[str, Any]:
        """
        Build context when returning to a work state with feedback.
        
        This ensures the rejected artifact is available under the correct key
        for the destination state's template to render properly.
        
        Args:
            tool: The active workflow tool instance
            state: The destination state (work state we're returning to)
            feedback_notes: The feedback from the reviewer
            
        Returns:
            Dictionary with complete context for template rendering
        """
        context = tool.context_store.copy()
        context["feedback_notes"] = feedback_notes
        
        # Get the expected artifact key for this state
        artifact_key = ArtifactKeys.get_artifact_key(state)
        logger.debug(f"Building feedback context for state '{state}', expecting artifact key '{artifact_key}'")
        
        # Ensure artifact is available with expected key
        if artifact_key not in context:
            logger.warning(f"Artifact key '{artifact_key}' not found in context, searching for recent artifact")
            
            # Find the most recent artifact from any state
            artifact_found = False
            for key, value in tool.context_store.items():
                if key.endswith("_artifact") and value is not None:
                    logger.info(f"Found artifact under key '{key}', copying to '{artifact_key}'")
                    context[artifact_key] = value
                    artifact_found = True
                    break
            
            if not artifact_found:
                logger.error(f"No artifact found in context_store for feedback loop")
        else:
            logger.debug(f"Artifact already available under key '{artifact_key}'")
        
        # Log final context keys for debugging
        logger.debug(f"Final context keys: {list(context.keys())}")
        logger.debug(f"Feedback notes (first 100 chars): {feedback_notes[:100]}")
        
        return context
    
    @staticmethod
    def build_review_context(tool: Any, artifact: Any) -> Dict[str, Any]:
        """
        Build context for review states (AI/Human review).
        
        Args:
            tool: The active workflow tool instance
            artifact: The artifact just submitted
            
        Returns:
            Dictionary with context for review template rendering
        """
        context = tool.context_store.copy()
        
        # Review states expect artifact under 'artifact_content' key
        if hasattr(artifact, 'model_dump'):
            context["artifact_content"] = artifact.model_dump()
        else:
            context["artifact_content"] = artifact
            
        logger.debug(f"Built review context with artifact_content")
        
        return context
    
    @staticmethod
    def build_standard_context(tool: Any) -> Dict[str, Any]:
        """
        Build standard context for forward progression.
        
        Args:
            tool: The active workflow tool instance
            
        Returns:
            Copy of the tool's context_store
        """
        return tool.context_store.copy()