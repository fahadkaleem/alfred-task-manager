"""
Local provider package for Epic Task Manager.

This package implements the local file-based task provider that reads
markdown task files from the .epictaskmanager/tasks/ inbox directory.
"""

from .provider import LocalProvider

__all__ = ["LocalProvider"]
