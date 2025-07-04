"""Get next task implementation using the task provider factory."""

from alfred.models.schemas import ToolResponse
from alfred.task_providers.factory import get_provider
from alfred.lib.logger import get_logger

logger = get_logger(__name__)


async def get_next_task_impl() -> ToolResponse:
    """Gets the next recommended task using the configured provider.

    This tool intelligently determines which task should be worked on next
    based on task status, priority, and other factors. It uses the configured
    task provider (local, jira, linear) to fetch and rank tasks.

    Returns:
        ToolResponse containing:
        - The recommended task ID and details
        - Reasoning for the recommendation
        - Alternative tasks that could be worked on
        - A prompt suggesting how to proceed
    """
    try:
        # Get the configured task provider
        provider = get_provider()

        # Delegate to the provider's implementation
        return provider.get_next_task()

    except NotImplementedError as e:
        # Handle providers that aren't implemented yet
        logger.error(f"Provider not implemented: {e}")
        return ToolResponse(status="error", message=str(e))
    except Exception as e:
        # Handle any other errors
        logger.error(f"Failed to get next task: {e}")
        return ToolResponse(status="error", message=f"Failed to get next task: {str(e)}")
