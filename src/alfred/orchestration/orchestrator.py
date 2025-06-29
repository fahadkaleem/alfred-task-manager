# src/alfred/orchestration/orchestrator.py
"""
A simplified, central session manager for Alfred's active workflow tools.
"""
from typing import Dict
from src.alfred.config import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)

class Orchestrator:
    """
    Singleton class to manage active tool sessions.
    This class holds a dictionary of active tool instances, keyed by task_id.
    It no longer manages workflows or personas directly.
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
        self.active_tools: Dict[str, BaseWorkflowTool] = {}
        self.config_manager = ConfigManager(settings.alfred_dir)
        self._initialized = True
        logger.info("Orchestrator initialized as a simple tool session manager.")

# Global singleton instance
orchestrator = Orchestrator()