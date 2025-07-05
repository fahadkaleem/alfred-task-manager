"""Get next task implementation using the task provider factory."""

from alfred.models.schemas import ToolResponse
from alfred.task_providers.factory import get_provider
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
async def get_next_task_logic(**kwargs) -> ToolResponse:
    """Logic function for get_next_task compatible with GenericWorkflowHandler.

    Gets the next recommended task using the configured provider.
    This tool doesn't require a task_id parameter.
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
