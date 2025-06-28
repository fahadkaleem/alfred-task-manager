#!/usr/bin/env python3
"""
Main entry point for Epic Task Manager MCP Server
"""

from src.epic_task_manager.server import app

if __name__ == "__main__":
    app.run()
