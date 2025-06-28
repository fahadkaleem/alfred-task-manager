#!/usr/bin/env python3
"""
Test script to validate the Alfred flow with the new ArtifactManager.
"""

from pathlib import Path

from src.alfred.tools.review_tools import approve_and_handoff as approve_and_handoff_impl
from src.alfred.tools.review_tools import provide_review as provide_review_impl
from src.alfred.tools.task_tools import begin_task as begin_task_impl
from src.alfred.tools.task_tools import submit_work as submit_work_impl


def main():
    """Run the test flow."""
    task_id = "TEST-01"

    # 1. Begin task
    begin_task_impl(task_id=task_id)

    # 2. Submit work
    artifact = {"branch_name": "feature/TEST-01-artifact-manager", "branch_status": "clean", "ready_for_work": True}
    submit_work_impl(task_id=task_id, artifact=artifact)

    # 3. Provide review (approve)
    provide_review_impl(task_id=task_id, is_approved=True, feedback_notes="")

    # 4. Approve and handoff
    approve_and_handoff_impl(task_id=task_id)

    # 5. Check if artifact was created
    workspace_dir = Path(".alfred/workspace")
    artifact_path = workspace_dir / task_id / "archive" / "git_setup_artifact.md"

    if artifact_path.exists():
        pass
    else:
        pass


if __name__ == "__main__":
    main()
