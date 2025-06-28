"""
Custom exceptions for the execution module
"""


class ArtifactNotFoundError(Exception):
    """Raised when a required artifact is not found"""


class TemplateNotFoundError(Exception):
    """Raised when a required template is not found"""


class InvalidArtifactError(Exception):
    """Raised when an artifact has invalid format or content"""
