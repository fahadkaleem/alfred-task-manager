# src/alfred/orchestration/orchestrator.py
"""
Legacy orchestrator module - largely deprecated in stateless design.

The orchestrator previously managed active tool sessions but this functionality
has been replaced by the stateless WorkflowEngine pattern where StateManager
is the single source of truth.
"""

from alfred.config import ConfigManager
from alfred.config.settings import settings
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    """
    Legacy orchestrator class - deprecated in favor of stateless design.

    Previously managed active tool sessions but this functionality has been
    replaced by WorkflowEngine + StateManager pattern. Kept for backwards
    compatibility but no longer holds any state.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.config_manager = ConfigManager(settings.alfred_dir)
        self._initialized = True
        logger.info("Orchestrator initialized (legacy mode - stateless design active)", orchestrator_type="legacy_deprecated", alfred_dir=str(settings.alfred_dir))


# Global singleton instance - kept for backwards compatibility
orchestrator = Orchestrator()
